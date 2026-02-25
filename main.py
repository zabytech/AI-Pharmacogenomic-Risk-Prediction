import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from database import db, create_document, get_documents

app = FastAPI(title="MediSphere Pharmacogenomics API", description="VCF analysis and risk prediction")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_GENES = {"CYP2D6", "CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "DPYD"}
SUPPORTED_DRUGS = {"CODEINE", "WARFARIN", "CLOPIDOGREL", "SIMVASTATIN", "AZATHIOPRINE", "FLUOROURACIL"}

class ChatRequest(BaseModel):
    patient_id: Optional[str] = None
    message: str
    provider: Optional[str] = None  # 'gemini' | 'openai' | None

@app.get("/")
def read_root():
    return {"message": "MediSphere API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            collections = db.list_collection_names()
            response["collections"] = collections[:10]
            response["connection_status"] = "Connected"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# --- Utility functions ---

def parse_vcf(content: str, max_bytes: int = 5_000_000) -> List[Dict[str, Any]]:
    """Parse VCF v4.2 content, extract INFO tags relevant to pharmacogenomics.
    - Accepts STAR values that may be comma-separated.
    - Normalizes keys to upper-case for robustness.
    Returns list of variant dicts.
    """
    encoded = content.encode("utf-8")
    if len(encoded) > max_bytes:
        raise HTTPException(status_code=413, detail="VCF exceeds 5MB limit")
    variants = []
    for line in content.splitlines():
        if not line or line.startswith('#'):
            continue
        parts = line.strip().split('\t')
        if len(parts) < 8:
            continue
        chrom, pos, vid, ref, alt, qual, flt, info = parts[:8]
        info_dict: Dict[str, Any] = {}
        for kv in info.split(';'):
            if '=' in kv:
                k, v = kv.split('=', 1)
                info_dict[k.upper()] = v
            else:
                info_dict[kv.upper()] = True
        gene = info_dict.get('GENE')
        star_raw = info_dict.get('STAR')
        rs = info_dict.get('RS') or (vid if vid and vid.lower().startswith('rs') else None)
        stars = []
        if star_raw:
            for s in str(star_raw).split(','):
                s = s.strip()
                if s:
                    stars.append(s if s.startswith('*') else f"*{s}")
        if gene in SUPPORTED_GENES:
            variants.append({
                "CHROM": chrom,
                "POS": pos,
                "ID": vid,
                "REF": ref,
                "ALT": alt,
                "INFO": info_dict,
                "GENE": gene,
                "STARS": stars,
                "RS": rs,
            })
    return variants

# CPIC-inspired allele function categories (simplified)
LOSS_CYP2D6 = {'*3','*4','*5','*6'}
DECREASED_CYP2D6 = {'*17','*41'}

LOSS_CYP2C19 = {'*2','*3','*4'}
INCREASED_CYP2C19 = {'*17'}

LOSS_CYP2C9 = {'*2','*3'}

LOSS_TPMT = {'*2','*3A','*3B','*3C'}

REDUCED_DPYD = {'*2A','*13'}
CRITICAL_RS_DPYD = {'RS3918290','RS55886062'}

SLCO1B1_DECREASED = {'*5','RS4149056'}


def determine_diplotype(variants: List[Dict[str, Any]], gene: str) -> str:
    """Infer a diplotype from STAR annotations.
    - Picks up to two distinct star alleles.
    - If duplication (XN) is present, include it.
    - Default heterozygous with *1 if a single allele.
    """
    stars: List[str] = []
    for v in variants:
        stars.extend(v.get('STARS', []))
    if not stars:
        return "Unknown"
    # Normalize and unique preserving order
    uniq: List[str] = []
    for s in stars:
        s = s.upper()
        if s not in uniq:
            uniq.append(s)
    # Handle copy number notations
    dup = next((u for u in uniq if 'XN' in u), None)
    if dup:
        # Place duplication first
        base = [dup] + [u for u in uniq if u != dup]
    else:
        base = uniq
    if len(base) >= 2:
        return f"{base[0]}/{base[1]}"
    return f"{base[0]}/*1"


def phenotype_from_diplotype(gene: str, diplotype: str) -> str:
    g = gene.upper()
    d = diplotype.upper()
    if g == 'CYP2D6':
        if any(a in d for a in LOSS_CYP2D6) and any(b in d for b in LOSS_CYP2D6):
            return 'PM'
        if any(a in d for a in LOSS_CYP2D6) and '*1' in d:
            return 'IM'
        if any(a in d for a in DECREASED_CYP2D6):
            return 'IM'
        if 'XN' in d:
            return 'URM'
        return 'NM'
    if g == 'CYP2C19':
        if any(a in d for a in LOSS_CYP2C19) and any(b in d for b in LOSS_CYP2C19):
            return 'PM'
        if any(a in d for a in LOSS_CYP2C19) and '*1' in d:
            return 'IM'
        if '*17' in d and '*1' in d:
            return 'RM'
        return 'NM'
    if g == 'CYP2C9':
        if any(a in d for a in LOSS_CYP2C9) and any(b in d for b in LOSS_CYP2C9):
            return 'PM'
        if any(a in d for a in LOSS_CYP2C9) and '*1' in d:
            return 'IM'
        return 'NM'
    if g == 'SLCO1B1':
        if any(a in d for a in SLCO1B1_DECREASED):
            return 'IM'
        return 'NM'
    if g == 'TPMT':
        if any(a in d for a in LOSS_TPMT) and any(b in d for b in LOSS_TPMT):
            return 'PM'
        if any(a in d for a in LOSS_TPMT) and '*1' in d:
            return 'IM'
        return 'NM'
    if g == 'DPYD':
        if any(a in d for a in REDUCED_DPYD) or any(rs in d for rs in CRITICAL_RS_DPYD):
            # If two reduced/critical markers
            cnt = sum(1 for a in REDUCED_DPYD if a in d) + sum(1 for rs in CRITICAL_RS_DPYD if rs in d)
            return 'PM' if cnt >= 2 else 'IM'
        return 'NM'
    return 'Unknown'


def risk_for_drug(drug: str, gene: str, phenotype: str) -> Dict[str, Any]:
    drug = drug.upper()
    phenotype = phenotype.upper()
    risk_label = 'Unknown'
    severity = 'none'
    cpic_ref = ''
    action = ''
    dose = ''
    confidence = 0.6

    if drug == 'CODEINE' and gene == 'CYP2D6':
        cpic_ref = 'CPIC Guideline for Codeine and CYP2D6'
        if phenotype == 'PM':
            risk_label, severity, action = 'Ineffective', 'moderate', 'Avoid codeine; use alternative analgesic'
            confidence = 0.92
        elif phenotype in ['URM', 'RM']:
            risk_label, severity, action = 'Toxic', 'high', 'Avoid codeine due to risk of toxicity'
            confidence = 0.92
        elif phenotype == 'IM':
            risk_label, severity, action, dose = 'Adjust Dosage', 'low', 'Consider alternative or monitor closely', 'Consider lower dose'
            confidence = 0.82
        else:
            risk_label, severity, action = 'Safe', 'none', 'Standard dosing'
            confidence = 0.72
    elif drug == 'WARFARIN' and gene == 'CYP2C9':
        cpic_ref = 'CPIC Guideline for Warfarin and CYP2C9'
        if phenotype == 'PM':
            risk_label, severity, action, dose = 'Toxic', 'high', 'Reduce initial dose and monitor INR closely', 'Lower dose'
            confidence = 0.86
        elif phenotype == 'IM':
            risk_label, severity, action, dose = 'Adjust Dosage', 'moderate', 'Use lower initial dose; frequent INR monitoring', 'Lower dose'
            confidence = 0.82
        else:
            risk_label, severity, action = 'Safe', 'none', 'Standard dosing with INR monitoring'
            confidence = 0.76
    elif drug == 'CLOPIDOGREL' and gene == 'CYP2C19':
        cpic_ref = 'CPIC Guideline for Clopidogrel and CYP2C19'
        if phenotype == 'PM':
            risk_label, severity, action = 'Ineffective', 'high', 'Use alternative antiplatelet (e.g., prasugrel, ticagrelor)'
            confidence = 0.91
        elif phenotype == 'IM':
            risk_label, severity, action = 'Adjust Dosage', 'moderate', 'Consider alternative therapy or enhanced platelet inhibition'
            confidence = 0.86
        else:
            risk_label, severity, action = 'Safe', 'none', 'Standard dosing'
            confidence = 0.76
    elif drug == 'SIMVASTATIN' and gene == 'SLCO1B1':
        cpic_ref = 'CPIC Guideline for Simvastatin and SLCO1B1'
        if phenotype in ['PM', 'IM']:
            risk_label, severity, action = 'Toxic', 'moderate', 'Consider lower dose or alternative statin due to myopathy risk'
            dose = 'Lower dose or switch'
            confidence = 0.82
        else:
            risk_label, severity, action = 'Safe', 'none', 'Standard dosing'
            confidence = 0.76
    elif drug == 'AZATHIOPRINE' and gene == 'TPMT':
        cpic_ref = 'CPIC Guideline for Thiopurines and TPMT'
        if phenotype == 'PM':
            risk_label, severity, action = 'Toxic', 'critical', 'Use drastically reduced dose or alternative; monitor for myelosuppression'
            dose = 'Reduce dose by 90% or avoid'
            confidence = 0.92
        elif phenotype == 'IM':
            risk_label, severity, action = 'Adjust Dosage', 'high', 'Use reduced dose and monitor'
            dose = 'Reduce dose 30-70%'
            confidence = 0.87
        else:
            risk_label, severity, action = 'Safe', 'none', 'Standard dosing'
            confidence = 0.76
    elif drug == 'FLUOROURACIL' and gene == 'DPYD':
        cpic_ref = 'CPIC Guideline for Fluoropyrimidines and DPYD'
        if phenotype == 'PM':
            risk_label, severity, action = 'Toxic', 'critical', 'Avoid or use greatly reduced dose; consider alternative'
            dose = 'Avoid or reduce >50%'
            confidence = 0.92
        elif phenotype == 'IM':
            risk_label, severity, action = 'Adjust Dosage', 'high', 'Use reduced dose with close monitoring'
            dose = 'Reduce 25-50%'
            confidence = 0.87
        else:
            risk_label, severity, action = 'Safe', 'none', 'Standard dosing'
            confidence = 0.76
    else:
        action = 'Insufficient evidence for gene-drug pair'
    return {
        "risk_label": risk_label,
        "confidence_score": round(confidence, 2),
        "severity": severity,
        "cpic": cpic_ref,
        "action": action,
        "dose": dose,
    }


def generate_llm_explanation(drug: str, gene: str, variants: List[Dict[str, Any]], phenotype: str, risk: Dict[str, Any]) -> Dict[str, str]:
    rsids = [v.get('RS') for v in variants if v.get('RS')]
    rs_text = ', '.join([r.lower() if r else '' for r in rsids]) or 'N/A'
    summary = (
        f"For {drug.title()}, the patient's {gene} phenotype is {phenotype}. "
        f"Based on detected variants ({rs_text}), the assessed risk is '{risk['risk_label']}'."
    )
    mechanism = (
        f"{gene} influences {drug.title()} pharmacokinetics/pharmacodynamics. Variants like {rs_text} can alter enzyme or transporter activity, "
        f"leading to changes in drug metabolism or exposure."
    )
    clinical = (
        f"Following CPIC guidance ({risk.get('cpic','')}), the recommended action is: {risk['action']}. "
        f"Dose adjustment: {risk['dose'] or 'None'}."
    )
    return {
        "summary": summary,
        "mechanism": mechanism,
        "clinical_significance": clinical,
    }

# --- LLM Integrations ---

def _openai_generate(content: str) -> str:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return ''
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': 'gpt-4o',
        'messages': [
            { 'role': 'system', 'content': 'You are a clinical pharmacogenomics assistant. Explain results simply, clarify terminology, reference CPIC where relevant, and include an educational disclaimer.' },
            { 'role': 'user', 'content': content }
        ],
        'temperature': 0.7
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            choice = (data.get('choices') or [{}])[0]
            msg = (choice.get('message') or {}).get('content')
            return msg or ''
        return ''
    except Exception:
        return ''

@app.post("/analyze")
async def analyze_vcf(
    file: UploadFile = File(...),
    drugs: str = Form(...),
    patient_id: str | None = Form(None)
):
    if not file.filename.lower().endswith('.vcf'):
        raise HTTPException(status_code=400, detail="File must be a VCF (.vcf)")
    data = await file.read()
    if len(data) > 5_000_000:
        raise HTTPException(status_code=413, detail="VCF exceeds 5MB limit")
    try:
        content = data.decode('utf-8')
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to decode VCF as UTF-8")

    variants = parse_vcf(content)
    drugs_list = [d.strip().upper() for d in drugs.split(',') if d.strip()]
    drugs_list = [d for d in drugs_list if d in SUPPORTED_DRUGS]
    if not drugs_list:
        raise HTTPException(status_code=400, detail="No supported drugs provided")

    genes_detected = {v['GENE'] for v in variants}
    rsids = [v['RS'] for v in variants if v.get('RS')]

    reports: List[Dict[str, Any]] = []
    now_ts = datetime.now(timezone.utc).isoformat()
    pid = patient_id or f"PATIENT_{uuid.uuid4().hex[:8].upper()}"

    for drug in drugs_list:
        gene_map = {
            'CODEINE': 'CYP2D6',
            'WARFARIN': 'CYP2C9',
            'CLOPIDOGREL': 'CYP2C19',
            'SIMVASTATIN': 'SLCO1B1',
            'AZATHIOPRINE': 'TPMT',
            'FLUOROURACIL': 'DPYD',
        }
        primary_gene = gene_map.get(drug)
        gene_vars = [v for v in variants if v['GENE'] == primary_gene]
        diplotype = determine_diplotype(gene_vars, primary_gene)
        phenotype = phenotype_from_diplotype(primary_gene, diplotype) if diplotype != 'Unknown' else 'Unknown'
        risk = risk_for_drug(drug, primary_gene, phenotype)
        explanation = generate_llm_explanation(drug, primary_gene, gene_vars, phenotype, risk)

        missing_annotations = not gene_vars or not any(v.get('STARS') for v in gene_vars) or not any(v.get('RS') for v in gene_vars)

        result: Dict[str, Any] = {
            "patient_id": pid,
            "drug": drug,
            "timestamp": now_ts,
            "risk_assessment": {
                "risk_label": risk['risk_label'],
                "confidence_score": risk['confidence_score'],
                "severity": risk['severity']
            },
            "pharmacogenomic_profile": {
                "primary_gene": primary_gene,
                "diplotype": diplotype,
                "phenotype": phenotype,
                "detected_variants": [{"rsid": (v.get('RS') or '')} for v in gene_vars] or [{"rsid": ""}]
            },
            "clinical_recommendation": {
                "cpic_guideline_reference": risk['cpic'],
                "recommended_action": risk['action'],
                "dose_adjustment": risk['dose']
            },
            "llm_generated_explanation": {
                "summary": explanation['summary'],
                "mechanism": explanation['mechanism'],
                "clinical_significance": explanation['clinical_significance']
            },
            "quality_metrics": {
                "vcf_parsing_success": True,
                "missing_annotations": bool(missing_annotations),
                "analysis_timestamp": now_ts
            }
        }

        try:
            create_document('pharmacogenomicreport', result)
        except Exception:
            pass

        reports.append(result)

    summary = {
        "patient_id": pid,
        "total_variants": len(variants),
        "genes_covered": list(genes_detected),
        "rsids_detected": rsids,
    }

    return {"reports": reports, "summary": summary}

@app.post('/chat')
def chat(req: ChatRequest):
    patient_reports = []
    if req.patient_id:
        try:
            patient_reports = get_documents('pharmacogenomicreport', {"patient_id": req.patient_id}, limit=3)
        except Exception:
            patient_reports = []

    context_lines = []
    for r in patient_reports:
        context_lines.append(
            f"Drug: {r.get('drug')} | Risk: {r.get('risk_assessment',{}).get('risk_label')} | Phenotype: {r.get('pharmacogenomic_profile',{}).get('phenotype')} | Gene: {r.get('pharmacogenomic_profile',{}).get('primary_gene')}"
        )
    context = "\n".join(context_lines)

    user_prompt = f"Question: {req.message}\n\nRecent context:\n{context or 'No prior reports.'}"

    # Force OpenAI (GPT‑4o) usage for consistency
    llm_text = _openai_generate(user_prompt)

    if not llm_text:
        llm_text = (
            "MediSphere Assistant: In simple terms, pharmacogenomics looks at how your genes affect medicines. "
            "If enzyme activity is reduced, drug levels can rise (more side effects); if increased, drugs may clear quickly (less effect). "
            "Discuss dosing changes with your clinician. This is educational information, not medical advice."
        )

    try:
        create_document('chatmessage', {
            "patient_id": req.patient_id,
            "role": "assistant",
            "message": llm_text,
        })
    except Exception:
        pass

    return {"reply": llm_text, "disclaimer": "Educational guidance; not a substitute for professional medical advice."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

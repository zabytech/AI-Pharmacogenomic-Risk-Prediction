import os
import json
import re
import uvicorn
from datetime import datetime, timezone

import anthropic
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ─── Secure API Key Initialisation ────────────────────────────────────────────
# The key is read ONCE at startup from the environment.  It is never accepted
# from the user, never passed through the API, and never appears in any
# response payload.  If the variable is absent the process exits immediately
# with an actionable message rather than silently failing at request time.
_ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
if not _ANTHROPIC_API_KEY:
    raise RuntimeError(
        "ANTHROPIC_API_KEY environment variable is not set. "
        "Export it before starting the server:\n"
        "  export ANTHROPIC_API_KEY='sk-ant-...'"
    )

# Single, module-level client — created once, reused for every request.
# This avoids the overhead of re-instantiating the client per call and ensures
# the key is held in one place that no request handler can accidentally expose.
anthropic_client = anthropic.Anthropic(api_key=_ANTHROPIC_API_KEY)

app = FastAPI(title="PharmaGuard API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── Knowledge Base ────────────────────────────────────────────────────────────
GENE_VARIANT_DB = {
    "CYP2D6": {
        "rs3892097":  {"star": "*4",   "effect": "loss_of_function",  "description": "Splicing defect eliminating enzyme activity"},
        "rs35742686": {"star": "*3",   "effect": "loss_of_function",  "description": "Frameshift mutation causing truncated protein"},
        "rs5030655":  {"star": "*1xN", "effect": "gain_of_function",  "description": "Gene duplication causing ultrarapid metabolism"},
        "rs16947":    {"star": "*2",   "effect": "reduced_function",  "description": "Amino acid change reducing enzyme activity"},
        "rs28371725": {"star": "*41",  "effect": "reduced_function",  "description": "Splicing variant reducing expression"},
        "rs1065852":  {"star": "*10",  "effect": "reduced_function",  "description": "Pro34Ser common in Asian populations"},
    },
    "CYP2C19": {
        "rs4244285":  {"star": "*2",  "effect": "loss_of_function",  "description": "Splicing defect causing premature stop codon"},
        "rs4986893":  {"star": "*3",  "effect": "loss_of_function",  "description": "W212X nonsense mutation"},
        "rs12248560": {"star": "*17", "effect": "gain_of_function",  "description": "Promoter variant increasing transcription"},
        "rs28399504": {"star": "*4",  "effect": "loss_of_function",  "description": "Start codon mutation"},
    },
    "CYP2C9": {
        "rs1799853": {"star": "*2", "effect": "reduced_function",    "description": "R144C variant reducing warfarin metabolism by ~30%"},
        "rs1057910": {"star": "*3", "effect": "reduced_function",    "description": "I359L variant reducing warfarin metabolism by ~80%"},
        "rs28371686":{"star": "*5", "effect": "reduced_function",    "description": "D360E variant"},
        "rs9332131": {"star": "*6", "effect": "loss_of_function",    "description": "Frameshift deletion"},
    },
    "SLCO1B1": {
        "rs4149056":  {"star": "*5",  "effect": "reduced_function",  "description": "Val174Ala reducing hepatic statin uptake"},
        "rs2306283":  {"star": "*1B", "effect": "normal_function",   "description": "Increased statin uptake"},
        "rs11045819": {"star": "*15", "effect": "reduced_function",  "description": "Combined variant with rs4149056"},
    },
    "TPMT": {
        "rs1800462": {"star": "*2",  "effect": "loss_of_function",   "description": "A80P variant causing misfolding"},
        "rs1800460": {"star": "*3B", "effect": "loss_of_function",   "description": "G460A variant"},
        "rs1142345": {"star": "*3C", "effect": "loss_of_function",   "description": "A719G variant"},
        "rs1800584": {"star": "*3A", "effect": "loss_of_function",   "description": "Combined *3B/*3C, most common deficiency"},
    },
    "DPYD": {
        "rs3918290":  {"star": "*2A",       "effect": "loss_of_function", "description": "Splicing variant eliminating exon 14; major cause of 5-FU toxicity"},
        "rs55886062": {"star": "*13",       "effect": "loss_of_function", "description": "I560S variant"},
        "rs67376798": {"star": "c.2846A>T", "effect": "reduced_function","description": "D949V reduced DPYD activity"},
        "rs75017182": {"star": "HapB3",     "effect": "reduced_function","description": "Haplotype B3 reducing DPYD activity"},
    }
}

DRUG_GENE_MAP = {
    "CODEINE":      {"primary_gene": "CYP2D6",  "secondary_genes": ["CYP2C19"]},
    "WARFARIN":     {"primary_gene": "CYP2C9",  "secondary_genes": ["CYP2C19","SLCO1B1"]},
    "CLOPIDOGREL":  {"primary_gene": "CYP2C19", "secondary_genes": ["CYP2D6"]},
    "SIMVASTATIN":  {"primary_gene": "SLCO1B1", "secondary_genes": ["CYP2C9"]},
    "AZATHIOPRINE": {"primary_gene": "TPMT",    "secondary_genes": []},
    "FLUOROURACIL": {"primary_gene": "DPYD",    "secondary_genes": []},
}

PHENOTYPE_RULES = {
    "CYP2D6":  {("*1","*1"):"NM",("*1","*2"):"NM",("*1","*4"):"IM",("*1","*3"):"IM",("*1","*41"):"IM",
                ("*4","*4"):"PM",("*3","*4"):"PM",("*3","*3"):"PM",("*1xN","*1"):"UM",
                ("*1xN","*4"):"NM",("*2","*41"):"IM",("*10","*10"):"IM",("*1","*10"):"NM"},
    "CYP2C19": {("*1","*1"):"NM",("*1","*2"):"IM",("*1","*17"):"RM",("*2","*2"):"PM",
                ("*2","*3"):"PM",("*17","*17"):"UM",("*1","*3"):"IM",("*1","*4"):"IM"},
    "CYP2C9":  {("*1","*1"):"NM",("*1","*2"):"IM",("*1","*3"):"IM",("*2","*2"):"IM",
                ("*2","*3"):"PM",("*3","*3"):"PM",("*1","*5"):"IM",("*1","*6"):"IM"},
    "SLCO1B1": {("*1","*1"):"NF",("*1","*5"):"DF",("*5","*5"):"PF",
                ("*1","*1B"):"NF",("*1","*15"):"DF",("*5","*15"):"PF"},
    "TPMT":    {("*1","*1"):"NM",("*1","*2"):"IM",("*1","*3A"):"IM",("*1","*3C"):"IM",
                ("*2","*3A"):"PM",("*3A","*3A"):"PM",("*3C","*3C"):"PM",("*3B","*3C"):"PM",("*1","*3B"):"IM"},
    "DPYD":    {("*1","*1"):"NM",("*1","*2A"):"IM",("*2A","*2A"):"PM",("*1","*13"):"IM",
                ("*1","HapB3"):"IM",("*1","c.2846A>T"):"IM",("*13","*13"):"PM"},
}

RISK_MATRIX = {
    ("PM","CODEINE"):("Ineffective","high","No enzyme to convert codeine to active morphine"),
    ("IM","CODEINE"):("Adjust Dosage","moderate","Reduced conversion; lower analgesic effect"),
    ("NM","CODEINE"):("Safe","none","Normal codeine metabolism expected"),
    ("RM","CODEINE"):("Safe","none","Normal to slightly increased metabolism"),
    ("UM","CODEINE"):("Toxic","critical","Ultra-rapid conversion to morphine; fatal respiratory depression risk"),
    ("PM","WARFARIN"):("Toxic","critical","Severely reduced clearance; major bleeding risk"),
    ("IM","WARFARIN"):("Adjust Dosage","moderate","Reduced clearance; lower maintenance dose needed"),
    ("NM","WARFARIN"):("Safe","none","Standard warfarin dosing appropriate"),
    ("RM","WARFARIN"):("Adjust Dosage","low","Slightly increased clearance; monitor INR"),
    ("UM","WARFARIN"):("Ineffective","moderate","Rapid metabolism; anticoagulation may be insufficient"),
    ("PM","CLOPIDOGREL"):("Ineffective","high","Cannot activate prodrug; no antiplatelet effect"),
    ("IM","CLOPIDOGREL"):("Adjust Dosage","moderate","Reduced activation; consider alternative"),
    ("NM","CLOPIDOGREL"):("Safe","none","Adequate activation expected"),
    ("RM","CLOPIDOGREL"):("Safe","none","Normal to enhanced activation"),
    ("UM","CLOPIDOGREL"):("Adjust Dosage","low","Enhanced activation; monitor for bleeding"),
    ("PF","SIMVASTATIN"):("Toxic","high","Reduced hepatic uptake; elevated plasma statin → myopathy"),
    ("DF","SIMVASTATIN"):("Adjust Dosage","moderate","Moderately reduced uptake; lower dose or switch"),
    ("NF","SIMVASTATIN"):("Safe","none","Normal simvastatin hepatic transport"),
    ("IM","SIMVASTATIN"):("Adjust Dosage","low","Minor metabolic impact"),
    ("PM","AZATHIOPRINE"):("Toxic","critical","TPMT deficiency; severe myelosuppression risk"),
    ("IM","AZATHIOPRINE"):("Adjust Dosage","high","Reduced TPMT; reduce dose 30-50%"),
    ("NM","AZATHIOPRINE"):("Safe","none","Normal TPMT activity"),
    ("PM","FLUOROURACIL"):("Toxic","critical","Complete DPYD deficiency; 5-FU accumulation; life-threatening"),
    ("IM","FLUOROURACIL"):("Adjust Dosage","high","Reduced DPYD; reduce 5-FU dose 25-50% per CPIC"),
    ("NM","FLUOROURACIL"):("Safe","none","Normal 5-FU catabolism"),
}

CPIC_RECOMMENDATIONS = {
    ("PM","CODEINE"):     "Avoid codeine. Use morphine, oxymorphone, or NSAIDs/acetaminophen.",
    ("IM","CODEINE"):     "Use with caution at standard doses. Monitor analgesic efficacy. Consider morphine.",
    ("NM","CODEINE"):     "Initiate at standard doses per label.",
    ("UM","CODEINE"):     "CONTRAINDICATED. Avoid entirely. Risk of fatal respiratory depression. Use morphine (reduced dose).",
    ("PM","WARFARIN"):    "Initiate at 30-50% reduced dose. Intensive INR monitoring. Target INR 2-3.",
    ("IM","WARFARIN"):    "Initiate at 20-30% reduced dose. Increase INR monitoring frequency.",
    ("NM","WARFARIN"):    "Standard dosing (5-10 mg loading, 2-5 mg maintenance). Standard INR monitoring.",
    ("PM","CLOPIDOGREL"): "Avoid clopidogrel. Use prasugrel or ticagrelor (not CYP2C19 substrates).",
    ("IM","CLOPIDOGREL"): "Consider prasugrel or ticagrelor. If clopidogrel used, monitor platelet function.",
    ("NM","CLOPIDOGREL"): "Standard dosing (75 mg/day maintenance after loading dose).",
    ("UM","CLOPIDOGREL"): "Standard dosing. Monitor for increased bleeding risk.",
    ("PF","SIMVASTATIN"): "Avoid simvastatin >20 mg/day. Prefer pravastatin, rosuvastatin, or fluvastatin.",
    ("DF","SIMVASTATIN"): "Limit to ≤20 mg/day. Consider switching to pravastatin or rosuvastatin.",
    ("NF","SIMVASTATIN"): "Standard simvastatin dosing appropriate.",
    ("PM","AZATHIOPRINE"):"CONTRAINDICATED. 10-fold dose reduction or switch to mycophenolate mofetil.",
    ("IM","AZATHIOPRINE"):"Reduce starting dose 30-50%. Monitor CBC more frequently.",
    ("NM","AZATHIOPRINE"):"Standard azathioprine dosing per indication.",
    ("PM","FLUOROURACIL"):"CONTRAINDICATED. Do not administer fluorouracil/capecitabine. Use alternative chemotherapy.",
    ("IM","FLUOROURACIL"):"Reduce starting dose 25-50% per CPIC. Consider DPD enzyme activity testing.",
    ("NM","FLUOROURACIL"):"Standard fluorouracil dosing per protocol.",
}

# ─── Drug-Drug-Gene Interactions ───────────────────────────────────────────────
DDI_DATABASE = {
    ("CODEINE","FLUOXETINE","CYP2D6",None):{"severity":"critical","interaction_type":"Phenoconversion",
        "mechanism":"Fluoxetine is a strong CYP2D6 inhibitor. Converts NM patients to phenotypic PM, making codeine ineffective and accumulating toxic parent drug.",
        "recommendation":"Avoid this combination. Use non-opioid analgesia or morphine."},
    ("CODEINE","PAROXETINE","CYP2D6",None):{"severity":"critical","interaction_type":"Phenoconversion",
        "mechanism":"Paroxetine is the most potent CYP2D6 inhibitor. Converts even NM patients to phenotypic PM.",
        "recommendation":"Avoid. Switch to morphine or oxycodone."},
    ("WARFARIN","AMIODARONE","CYP2C9",None):{"severity":"critical","interaction_type":"Enzyme inhibition",
        "mechanism":"Amiodarone inhibits CYP2C9, dramatically increasing warfarin plasma levels. Combined with CYP2C9 variants, bleeding risk is life-threatening.",
        "recommendation":"Reduce warfarin dose by 30-50% on amiodarone initiation. Monitor INR weekly."},
    ("CLOPIDOGREL","OMEPRAZOLE","CYP2C19",None):{"severity":"high","interaction_type":"Competitive inhibition",
        "mechanism":"Omeprazole inhibits CYP2C19, reducing clopidogrel activation. With PM genotype, platelet inhibition may be completely abolished.",
        "recommendation":"Use pantoprazole instead. Pantoprazole has minimal CYP2C19 inhibition."},
    ("SIMVASTATIN","AMLODIPINE","SLCO1B1","DF"):{"severity":"moderate","interaction_type":"Compound myopathy risk",
        "mechanism":"Amlodipine inhibits CYP3A4, increasing simvastatin exposure. With SLCO1B1 decreased function, myopathy risk increases significantly.",
        "recommendation":"Limit simvastatin to ≤20 mg/day or use pravastatin."},
    ("SIMVASTATIN","AMLODIPINE","SLCO1B1","PF"):{"severity":"critical","interaction_type":"Compound myopathy risk",
        "mechanism":"Amlodipine raises simvastatin exposure in a patient already impaired at hepatic uptake. Extreme rhabdomyolysis risk.",
        "recommendation":"Contraindicated combination. Switch to rosuvastatin or pravastatin immediately."},
}

KNOWN_INHIBITORS = {
    "FLUOXETINE": {"gene":"CYP2D6","strength":"strong"},
    "PAROXETINE": {"gene":"CYP2D6","strength":"strong"},
    "AMIODARONE": {"gene":"CYP2C9","strength":"moderate"},
    "OMEPRAZOLE": {"gene":"CYP2C19","strength":"moderate"},
    "LANSOPRAZOLE":{"gene":"CYP2C19","strength":"moderate"},
    "VORICONAZOLE":{"gene":"CYP2C19","strength":"strong"},
    "FLUCONAZOLE": {"gene":"CYP2C9","strength":"strong"},
}

# ─── Population Frequencies (gnomAD-derived) ───────────────────────────────────
POP_FREQ = {
    "CYP2D6": {
        "*4":   {"European":0.20,"African":0.06,"East Asian":0.02,"South Asian":0.04,"Latino":0.07,"Global":0.12},
        "*3":   {"European":0.02,"African":0.01,"East Asian":0.00,"South Asian":0.01,"Latino":0.01,"Global":0.01},
        "*10":  {"European":0.02,"African":0.02,"East Asian":0.50,"South Asian":0.24,"Latino":0.08,"Global":0.18},
        "*41":  {"European":0.09,"African":0.03,"East Asian":0.05,"South Asian":0.07,"Latino":0.05,"Global":0.06},
        "*1xN": {"European":0.03,"African":0.07,"East Asian":0.01,"South Asian":0.02,"Latino":0.05,"Global":0.03},
    },
    "CYP2C19": {
        "*2":   {"European":0.15,"African":0.17,"East Asian":0.29,"South Asian":0.24,"Latino":0.14,"Global":0.20},
        "*3":   {"European":0.00,"African":0.00,"East Asian":0.09,"South Asian":0.04,"Latino":0.02,"Global":0.03},
        "*17":  {"European":0.22,"African":0.27,"East Asian":0.04,"South Asian":0.12,"Latino":0.16,"Global":0.15},
    },
    "CYP2C9": {
        "*2":   {"European":0.13,"African":0.03,"East Asian":0.00,"South Asian":0.06,"Latino":0.07,"Global":0.07},
        "*3":   {"European":0.07,"African":0.02,"East Asian":0.04,"South Asian":0.07,"Latino":0.04,"Global":0.05},
    },
    "SLCO1B1": {
        "*5":   {"European":0.15,"African":0.02,"East Asian":0.13,"South Asian":0.11,"Latino":0.08,"Global":0.10},
    },
    "TPMT": {
        "*3A":  {"European":0.05,"African":0.01,"East Asian":0.00,"South Asian":0.02,"Latino":0.03,"Global":0.03},
        "*3C":  {"European":0.01,"African":0.03,"East Asian":0.02,"South Asian":0.01,"Latino":0.02,"Global":0.02},
        "*2":   {"European":0.01,"African":0.00,"East Asian":0.00,"South Asian":0.00,"Latino":0.00,"Global":0.00},
    },
    "DPYD": {
        "*2A":       {"European":0.01,"African":0.00,"East Asian":0.00,"South Asian":0.00,"Latino":0.00,"Global":0.004},
        "HapB3":     {"European":0.02,"African":0.01,"East Asian":0.01,"South Asian":0.01,"Latino":0.01,"Global":0.013},
        "c.2846A>T": {"European":0.01,"African":0.00,"East Asian":0.00,"South Asian":0.00,"Latino":0.01,"Global":0.005},
    }
}

PM_PREVALENCE = {
    "CYP2D6":  {"PM":{"European":0.07,"African":0.02,"East Asian":0.01,"Global":0.05},
                "UM":{"European":0.02,"African":0.05,"East Asian":0.01,"Global":0.02}},
    "CYP2C19": {"PM":{"European":0.02,"African":0.03,"East Asian":0.15,"Global":0.04},
                "UM":{"European":0.04,"African":0.06,"East Asian":0.01,"Global":0.03}},
    "DPYD":    {"PM":{"European":0.001,"African":0.0,"East Asian":0.0,"Global":0.0004}},
    "TPMT":    {"PM":{"European":0.003,"African":0.002,"East Asian":0.001,"Global":0.003}},
}

CPIC_EVIDENCE = {
    "CODEINE":     {"level":"A","strength":"Strong","url":"https://cpicpgx.org/guidelines/guideline-for-codeine-and-cyp2d6/"},
    "WARFARIN":    {"level":"A","strength":"Strong","url":"https://cpicpgx.org/guidelines/guideline-for-warfarin-and-cyp2c9-and-vkorc1/"},
    "CLOPIDOGREL": {"level":"A","strength":"Strong","url":"https://cpicpgx.org/guidelines/guideline-for-clopidogrel-and-cyp2c19/"},
    "SIMVASTATIN": {"level":"A","strength":"Strong","url":"https://cpicpgx.org/guidelines/guideline-for-simvastatin-and-slco1b1/"},
    "AZATHIOPRINE":{"level":"A","strength":"Strong","url":"https://cpicpgx.org/guidelines/guideline-for-azathioprine-and-tpmt-and-nudt15/"},
    "FLUOROURACIL":{"level":"A","strength":"Strong","url":"https://cpicpgx.org/guidelines/guideline-for-fluoropyrimidines-and-dpyd/"},
}

GENE_CHROMOSOMES = {
    "CYP2D6":"22q13.1","CYP2C19":"10q23.33","CYP2C9":"10q23.33",
    "SLCO1B1":"12p12.2","TPMT":"6p22.3","DPYD":"1p21.3"
}

# ─── VCF Parser ────────────────────────────────────────────────────────────────
def parse_vcf(content: str) -> dict:
    lines = content.strip().split("\n")
    variants = {}
    patient_id = "PATIENT_UNKNOWN"
    for line in lines:
        if line.startswith("#CHROM"):
            parts = line.split("\t")
            if len(parts) >= 10:
                patient_id = parts[9].strip()
    if not any(l.startswith("#CHROM") for l in lines):
        raise ValueError("Invalid VCF: missing #CHROM header")
    for line in lines:
        if line.startswith("#"): continue
        parts = line.split("\t")
        if len(parts) < 9: continue
        chrom,pos,vid,ref,alt,qual,filt,info_str = parts[:8]
        fmt = parts[8] if len(parts)>8 else ""
        sample = parts[9] if len(parts)>9 else "0|0"
        info = {}
        for item in info_str.split(";"):
            if "=" in item:
                k,v = item.split("=",1); info[k]=v
        gene = info.get("GENE","").upper()
        star = info.get("STAR","*1")
        rsid = info.get("RS",vid) or vid
        if not gene or gene not in GENE_VARIANT_DB: continue
        gt = "0|0"
        if "GT" in fmt:
            try:
                gt_idx = fmt.split(":").index("GT")
                gt = sample.split(":")[gt_idx] if ":" in sample else sample
            except: gt = sample
        alleles = gt.replace("|","/").split("/")
        if not any(a!="0" for a in alleles): continue
        is_hom = all(a!="0" for a in alleles)
        vi = GENE_VARIANT_DB.get(gene,{}).get(rsid,{"star":star,"effect":"unknown","description":"Variant of unknown significance"})
        variants.setdefault(gene,[]).append({
            "rsid":rsid,"star":vi["star"],"effect":vi["effect"],"description":vi["description"],
            "chrom":chrom,"pos":pos,"ref":ref,"alt":alt,"gt":gt,
            "is_homozygous":is_hom,"zygosity":"homozygous" if is_hom else "heterozygous"
        })
    return {"patient_id":patient_id,"variants":variants}

def infer_diplotype(gene, gvars):
    if not gvars: return ("*1","*1")
    alleles = []
    for v in gvars:
        alleles.extend([v["star"],v["star"]] if v["is_homozygous"] else [v["star"]])
    if len(alleles)==1: alleles.append("*1")
    return (alleles[0], alleles[1] if len(alleles)>1 else "*1")

def lookup_phenotype(gene, diplotype):
    rules = PHENOTYPE_RULES.get(gene,{})
    if diplotype in rules: return rules[diplotype]
    rev=(diplotype[1],diplotype[0])
    if rev in rules: return rules[rev]
    return "Unknown"

def infer_risk(drug, phenotype):
    key=(phenotype,drug.upper())
    if key in RISK_MATRIX:
        l,s,r=RISK_MATRIX[key]
        c=0.92 if s in["none","critical"] else 0.78
        return l,s,c,r
    return ("Unknown","low",0.45,"Insufficient data")

# ─── Drug-Drug-Gene Interactions ───────────────────────────────────────────────
def detect_interactions(drugs, gene_profiles):
    interactions=[]
    up=[d.upper() for d in drugs]
    for (d1,d2,gene,ph_req),idata in DDI_DATABASE.items():
        if d1 in up and d2 in up:
            gph=gene_profiles.get(gene,{}).get("phenotype","Unknown")
            if ph_req is None or gph==ph_req:
                interactions.append({"drug_1":d1,"drug_2":d2,"gene_affected":gene,
                    "severity":idata["severity"],"interaction_type":idata["interaction_type"],
                    "mechanism":idata["mechanism"],"recommendation":idata["recommendation"],
                    "patient_phenotype":gph})
    for drug in up:
        if drug in KNOWN_INHIBITORS:
            info=KNOWN_INHIBITORS[drug]
            g=info["gene"]
            ph=gene_profiles.get(g,{}).get("phenotype","Unknown")
            interactions.append({"drug_1":drug,"drug_2":f"(via {g} inhibition)",
                "gene_affected":g,"severity":"high",
                "interaction_type":f"Phenoconversion — {info['strength']} inhibitor",
                "mechanism":f"{drug} is a {info['strength']} {g} inhibitor. Patient's {g} phenotype ({ph}) may shift toward Poor Metabolizer regardless of genotype. All {g}-substrate medications are affected.",
                "recommendation":f"Re-evaluate all {g}-substrate drugs. Adjust doses or switch to non-{g} alternatives.",
                "patient_phenotype":ph})
    return interactions

# ─── Population Context ────────────────────────────────────────────────────────
def build_population_context(gene, variants, phenotype):
    pop_data=[]
    for v in variants:
        star=v["star"]
        freqs=POP_FREQ.get(gene,{}).get(star,{})
        if freqs:
            pop_data.append({"star_allele":star,"rsid":v["rsid"],"frequencies":freqs,
                "rarest_in":min(freqs,key=freqs.get),"most_common_in":max(freqs,key=freqs.get)})
    pm_context=None
    if phenotype in["PM","UM"] and gene in PM_PREVALENCE:
        pm_context=PM_PREVALENCE[gene].get(phenotype)
    summary=""
    if pop_data:
        v=pop_data[0]
        gf=v["frequencies"].get("Global",0)
        mc=v["most_common_in"]; mcf=v["frequencies"].get(mc,0)
        pm_line=""
        if pm_context:
            eur=pm_context.get("European",0)
            pm_line=f" The {phenotype} phenotype affects {eur*100:.1f}% of Europeans globally."
        summary=f"The {v['star_allele']} allele occurs in {gf*100:.1f}% of the global population and is most prevalent in {mc} populations ({mcf*100:.1f}%).{pm_line}"
    else:
        summary=f"No population frequency data for detected {gene} variants."
    return {"variant_frequencies":pop_data,"phenotype_prevalence":pm_context,"summary":summary}

# ─── Confidence Breakdown ──────────────────────────────────────────────────────
def build_confidence(gene, variants, phenotype, diplotype, drug, risk_label):
    factors=[]; score=0.0
    if variants:
        factors.append({"factor":"Variants confirmed in VCF","contribution":"+25%","detail":f"{len(variants)} pathogenic variant(s) detected with zygosity"})
        score+=0.25
    else:
        factors.append({"factor":"Wildtype assumed (no variants)","contribution":"+10%","detail":"Reference allele inferred; adds uncertainty"})
        score+=0.10
    if diplotype[0]!="*1" and diplotype[1]!="*1":
        factors.append({"factor":"Both alleles characterized","contribution":"+20%","detail":f"Full diplotype {diplotype[0]}/{diplotype[1]} confirmed in VCF"})
        score+=0.20
    else:
        factors.append({"factor":"One allele inferred as *1","contribution":"+10%","detail":"One allele assumed wildtype — increases uncertainty"})
        score+=0.10
    cpic=CPIC_EVIDENCE.get(drug,{})
    if cpic.get("level")=="A":
        factors.append({"factor":"CPIC Evidence Level A","contribution":"+30%","detail":f"Highest-grade clinical evidence for {gene}/{drug} interaction"})
        score+=0.30
    else:
        factors.append({"factor":"Limited CPIC evidence","contribution":"+10%","detail":"Extrapolated from limited data"})
        score+=0.10
    if phenotype!="Unknown":
        factors.append({"factor":"Phenotype assignment successful","contribution":"+15%","detail":f"Diplotype maps to established {phenotype} phenotype in CPIC tables"})
        score+=0.15
    if risk_label!="Unknown":
        factors.append({"factor":"Risk matrix match found","contribution":"+10%","detail":f"{phenotype}/{drug} pair has established CPIC risk category"})
        score+=0.10
    return {"total_confidence":round(min(score,0.99),3),"factors":factors,
            "cpic_evidence_level":cpic.get("level","D"),"cpic_evidence_strength":cpic.get("strength","Limited"),
            "cpic_guideline_url":cpic.get("url","https://cpicpgx.org")}

# ─── LLM Dual-Mode Explanation ─────────────────────────────────────────────────
def generate_explanation(drug, gene, diplotype, phenotype, risk_label, severity, variants, rec, client):
    vtext="\n".join([f"  - {v['rsid']} ({v['star']}): {v['description']} [{v['zygosity']}]"
                     for v in variants]) or "  - No pathogenic variants (wildtype assumed)"
    prompt=f"""You are a senior clinical pharmacogenomicist generating a structured report.

Drug: {drug} | Gene: {gene} | Diplotype: {diplotype[0]}/{diplotype[1]}
Phenotype: {phenotype} | Risk: {risk_label} | Severity: {severity}
CPIC Recommendation: {rec}
Variants:\n{vtext}

Return ONLY valid JSON (no markdown):
{{
  "summary": "2-3 sentence plain-language patient summary",
  "biological_mechanism": "Technical explanation for clinicians (2-3 sentences with enzyme pathway)",
  "clinical_implications": "Prescribing decision impact (2-3 sentences)",
  "monitoring_parameters": "Specific labs, timepoints, symptoms to monitor",
  "alternative_drugs": "Specific alternatives if high/critical risk, else 'Standard therapy appropriate'",
  "patient_education_points": ["point 1","point 2","point 3"],
  "patient_letter": "3-4 sentence plain-English letter for patient to hand to any doctor. First person, no jargon. Include gene name in simple terms, what it means, and which drug to avoid/adjust.",
  "clinician_note": "3-4 sentence formal EHR consult note. Third person. Include diplotype, phenotype, CPIC evidence level A, specific dose adjustment."
}}"""
    try:
        msg=client.messages.create(model="claude-opus-4-6",max_tokens=1000,messages=[{"role":"user","content":prompt}])
        raw=msg.content[0].text.strip()
        raw=re.sub(r"^```json\s*","",raw); raw=re.sub(r"```$","",raw).strip()
        return json.loads(raw)
    except:
        return {"summary":f"Patient has {phenotype} phenotype for {gene}, affecting {drug} metabolism with {risk_label.lower()} risk.",
                "biological_mechanism":f"Variants in {gene} alter enzyme activity affecting {drug} processing.",
                "clinical_implications":f"Risk: {risk_label}. {rec}",
                "monitoring_parameters":"Monitor for adverse drug reactions and therapeutic efficacy.",
                "alternative_drugs":"Consult clinical pharmacist.",
                "patient_education_points":[f"Your genetics affect how you process {drug}","Inform all providers of this result","Do not adjust medication without consulting your physician"],
                "patient_letter":f"I have a genetic variant in the {gene} gene that affects how my body processes {drug}. My genetic type is called '{phenotype}'. Please review my pharmacogenomics report before prescribing this medication.",
                "clinician_note":f"Patient carries {diplotype[0]}/{diplotype[1]} diplotype for {gene} ({phenotype} phenotype, CPIC Level A). Risk classification: {risk_label}. {rec}"}

# ─── Core Analysis ─────────────────────────────────────────────────────────────
def analyze_single(vcf_text: str, drug: str, extra_drugs: list | None = None) -> dict:
    """Run a full pharmacogenomic analysis for one drug against one VCF.

    The Anthropic client is sourced from the module-level ``anthropic_client``
    singleton — no API key is accepted or forwarded through this function.
    """
    drug = drug.upper().strip()
    if drug not in DRUG_GENE_MAP:
        raise HTTPException(400, f"Drug '{drug}' not supported. Supported: {', '.join(DRUG_GENE_MAP.keys())}")
    try:
        parsed = parse_vcf(vcf_text)
    except Exception as e:
        return {"error": str(e), "quality_metrics": {"vcf_parsing_success": False, "error_message": str(e)}}

    patient_id = parsed["patient_id"]
    all_variants = parsed["variants"]
    primary_gene = DRUG_GENE_MAP[drug]["primary_gene"]
    gene_variants = all_variants.get(primary_gene, [])
    diplotype = infer_diplotype(primary_gene, gene_variants)
    phenotype = lookup_phenotype(primary_gene, diplotype)
    risk_label, severity, confidence, risk_reason = infer_risk(drug, phenotype)
    rec = CPIC_RECOMMENDATIONS.get((phenotype, drug), "Consult clinical pharmacogenomics service.")

    # Build all gene profiles
    gene_profiles = {}
    for g in GENE_VARIANT_DB:
        gvars = all_variants.get(g, [])
        d = infer_diplotype(g, gvars)
        p = lookup_phenotype(g, d)
        gene_profiles[g] = {
            "diplotype": f"{d[0]}/{d[1]}",
            "phenotype": p,
            "variant_count": len(gvars),
            "chromosome": GENE_CHROMOSOMES.get(g, "Unknown"),
        }

    # Use the shared module-level client — no key ever touches a request boundary.
    explanation = generate_explanation(
        drug, primary_gene, diplotype, phenotype,
        risk_label, severity, gene_variants, rec, anthropic_client,
    )

    all_drugs = [drug] + (extra_drugs or [])
    interactions = detect_interactions(all_drugs, gene_profiles)
    pop_ctx = build_population_context(primary_gene, gene_variants, phenotype)
    conf_bd = build_confidence(primary_gene, gene_variants, phenotype, diplotype, drug, risk_label)

    detected_out = [
        {
            "rsid": v["rsid"], "gene": primary_gene, "star_allele": v["star"],
            "chromosome": v["chrom"],
            "position": int(v["pos"]) if v["pos"].isdigit() else 0,
            "ref_allele": v["ref"], "alt_allele": v["alt"], "zygosity": v["zygosity"],
            "functional_effect": v["effect"], "clinical_significance": v["description"],
        }
        for v in gene_variants
    ]

    return {
        "patient_id": patient_id,
        "drug": drug,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "risk_assessment": {
            "risk_label": risk_label,
            "confidence_score": round(conf_bd["total_confidence"], 3),
            "severity": severity,
            "risk_rationale": risk_reason,
        },
        "pharmacogenomic_profile": {
            "primary_gene": primary_gene,
            "diplotype": f"{diplotype[0]}/{diplotype[1]}",
            "phenotype": phenotype,
            "detected_variants": detected_out,
            "all_gene_profiles": gene_profiles,
        },
        "clinical_recommendation": {
            "cpic_guideline": rec,
            "action_required": risk_label != "Safe",
            "urgency": severity,
            "prescriber_alert": risk_label in ["Toxic", "Ineffective"],
        },
        "drug_drug_gene_interactions": interactions,
        "population_context": pop_ctx,
        "confidence_breakdown": conf_bd,
        "llm_generated_explanation": explanation,
        "quality_metrics": {
            "vcf_parsing_success": True,
            "variants_detected": len(gene_variants),
            "genes_analyzed": list(all_variants.keys()),
            "diplotype_confidence": "high" if gene_variants else "low (wildtype assumed)",
            "cpic_evidence_level": conf_bd["cpic_evidence_level"],
        },
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────
# Note: neither endpoint accepts an api_key parameter.  Authentication is
# handled entirely at startup via the ANTHROPIC_API_KEY environment variable.

@app.post("/analyze")
async def analyze_endpoint(
    vcf_file: UploadFile = File(...),
    drugs: str = Form(...),
) -> JSONResponse:
    """Analyse a patient VCF file against one or more drugs."""
    if not vcf_file.filename.endswith(".vcf"):
        raise HTTPException(400, "Only .vcf files accepted")
    content = await vcf_file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(400, "File exceeds 5 MB")
    vcf_text = content.decode("utf-8", errors="replace")
    drug_list = [d.strip().upper() for d in drugs.split(",") if d.strip()]
    if not drug_list:
        raise HTTPException(400, "At least one drug is required")
    results = [
        analyze_single(vcf_text, drug, extra_drugs=drug_list)
        for drug in drug_list
    ]
    if len(results) == 1:
        return JSONResponse(content=results[0])
    return JSONResponse(content={"multi_drug_analysis": results, "drug_count": len(results)})


@app.post("/compare")
async def compare_endpoint(
    vcf_file_a: UploadFile = File(...),
    vcf_file_b: UploadFile = File(...),
    drug: str = Form(...),
) -> JSONResponse:
    """Side-by-side pharmacogenomic comparison of two patients."""
    ca = (await vcf_file_a.read()).decode("utf-8", errors="replace")
    cb = (await vcf_file_b.read()).decode("utf-8", errors="replace")
    ra = analyze_single(ca, drug.upper())
    rb = analyze_single(cb, drug.upper())
    diffs = []
    for g, pa in (ra.get("pharmacogenomic_profile", {}).get("all_gene_profiles") or {}).items():
        pb = (rb.get("pharmacogenomic_profile", {}).get("all_gene_profiles") or {}).get(g, {})
        if pa.get("phenotype") != pb.get("phenotype"):
            diffs.append({
                "gene": g,
                "patient_a": {"phenotype": pa.get("phenotype"), "diplotype": pa.get("diplotype")},
                "patient_b": {"phenotype": pb.get("phenotype"), "diplotype": pb.get("diplotype")},
            })
    return JSONResponse(content={
        "patient_a": ra,
        "patient_b": rb,
        "comparison": {
            "differences": diffs,
            "patient_a_risk": ra.get("risk_assessment", {}).get("risk_label"),
            "patient_b_risk": rb.get("risk_assessment", {}).get("risk_label"),
            "drug": drug.upper(),
        },
    })


@app.get("/supported-drugs")
async def supported() -> dict:
    return {"supported_drugs": list(DRUG_GENE_MAP.keys()), "gene_panel": list(GENE_VARIANT_DB.keys())}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "PharmaGuard API", "version": "2.0.0"}


if __name__ == "__main__":
    uvicorn.run("pharmaguard_v2_backend:app", host="0.0.0.0", port=8000, reload=True)

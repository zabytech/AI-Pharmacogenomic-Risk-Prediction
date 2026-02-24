 # 🧬 PharmaGuard  
## AI-Powered Pharmacogenomic Risk Prediction System  
### RIFT 2026 – Pharmacogenomics / Explainable AI Track  

---

## 🌐 Live Demo

🔗 https://prj-a5o4cwbj-frontend.flames.app  

---

## 🎬 LinkedIn Demo Video

🔗 (https://www.linkedin.com/posts/mohammed-danish-303066350_rift2026-pharmaguard-pharmacogenomics-activity-7430420092594716672-khXJ?utm_source=share&utm_medium=member_android&rcm=ACoAAFeS0DMBTgXtfGF1bhQec2pkaxN0eocVc1I))  

Required Hashtags:  
`#RIFT2026 #PharmaGuard #Pharmacogenomics #AIinHealthcare`

---

## 📌 Project Overview

Adverse drug reactions cause over 100,000 deaths annually. Many of these are preventable through pharmacogenomic testing — analyzing how genetic variants affect drug metabolism.

**PharmaGuard** is an explainable AI web application that:

- Parses authentic VCF (Variant Call Format v4.2) files  
- Identifies pharmacogenomic variants across six clinically significant genes  
- Predicts drug-specific risk categories  
- Generates CPIC-aligned dosing recommendations  
- Produces LLM-powered clinical explanations  
- Returns structured JSON matching the required hackathon schema  

---

## 🧠 Supported Genes

- CYP2D6  
- CYP2C19  
- CYP2C9  
- SLCO1B1  
- TPMT  
- DPYD  

---

## 💊 Supported Drugs

- CODEINE  
- WARFARIN  
- CLOPIDOGREL  
- SIMVASTATIN  
- AZATHIOPRINE  
- FLUOROURACIL  

---

## 🏗 Architecture Overview

```
Frontend (HTML + CSS + JS)
        │
        ▼
FastAPI Backend (Python)
- VCF Parsing Engine
- Variant Detection
- Diplotype & Phenotype Mapping
- CPIC Risk Matrix
- Structured JSON Output
        │
        ▼
Explainable AI Layer
(Anthropic Claude API)
- Biological Mechanism
- Clinical Implications
- Patient Education
- Clinician Notes
```

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| Server | Uvicorn |
| AI Layer | Anthropic Claude API |
| Data Format | VCF (Variant Call Format) |
| Hosting | Flames (Frontend) |
| Version Control | GitHub |

---

## ⚙ Installation Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/zabytech/AI-Pharmacogenomic-Risk-Prediction.git
cd AI-Pharmacogenomic-Risk-Prediction
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Set Anthropic API Key

Linux / macOS:
```bash
export ANTHROPIC_API_KEY="sk-ant-XXXXX"
```

Windows (CMD):
```cmd
set ANTHROPIC_API_KEY=sk-ant-XXXXX
```

### 4️⃣ Start Backend Server

```bash
python -m uvicorn pharmaguard_v2_backend:app --reload
```

### 5️⃣ Open Frontend

Use deployed version:  
https://prj-a5o4cwbj-frontend.flames.app  

Or open:
```
pharmaguard_demo_frontend.html
```

---

## 📡 API Documentation

### ✅ GET `/health`

Returns backend service status.

Example Response:
```json
{
  "status": "ok",
  "service": "PharmaGuard API",
  "version": "2.0.0"
}
```

---

### ✅ GET `/supported-drugs`

Returns supported pharmacogenomic drugs.

Example Response:
```json
["CODEINE","WARFARIN","CLOPIDOGREL","SIMVASTATIN","AZATHIOPRINE","FLUOROURACIL"]
```

---

### ✅ POST `/analyze`

Analyzes VCF file with one or more drugs.

**Request Parameters**
- `vcf_file` → .vcf file  
- `drugs` → Single or comma-separated drug names  

Example cURL:

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
-F "vcf_file=@demo.vcf" \
-F "drugs=CODEINE,WARFARIN"
```

**Response**

Structured JSON including:
- Risk Assessment  
- Pharmacogenomic Profile  
- Clinical Recommendation  
- LLM Generated Explanation  
- Quality Metrics  

---

## 🧪 Usage Example

1. Upload a VCF file  
2. Enter drug name (e.g., CODEINE)  
3. Click Analyze  
4. View:
   - Risk Label  
   - Confidence Score  
   - CPIC Recommendation  
   - Explainable AI Clinical Summary  

---

## 🧾 JSON Output Compliance

PharmaGuard strictly follows the required RIFT schema:

- patient_id  
- drug  
- timestamp  
- risk_assessment  
- pharmacogenomic_profile  
- clinical_recommendation  
- llm_generated_explanation  
- quality_metrics  

Ensuring full compatibility with evaluation test cases.
 

---

## ⚠ Clinical Disclaimer

PharmaGuard provides pharmacogenomic decision support and does not replace clinical judgment or professional healthcare advice.

---

## 🌟 Why PharmaGuard Stands Out

- CPIC-aligned risk logic  
- Multi-drug support  
- Structured explainable AI outputs  
- Professional UI dashboard  
- Clean, schema-compliant JSON  
- Ethical and transparent clinical positioning  

---

👥 Team Members
Subhash V
Mohammed Zabiulla
Shreyas Gennur
Mohammed Danish

 
**Built for RIFT 2026 Hackathon – Precision Medicine Track**

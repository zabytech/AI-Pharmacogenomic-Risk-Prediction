# 📘 PharmaGuard – AI-Powered Pharmacogenomic Risk Prediction System

**Live Demo:** https://prj-a5o4cwbj-frontend.flames.app  
**LinkedIn Demo Video:** *(Add your public LinkedIn video link here)*

PharmaGuard is an explainable AI web application designed to analyze patient genomic data (VCF files) and drug names to predict personalized pharmacogenomic risks and provide clinically actionable recommendations with LLM-generated explanations. Built for the **RIFT 2026 Pharmacogenomics / Explainable AI Track**.

---

## 🌐 Live Demo

Experience the fully functional web application here:  
👉 https://prj-a5o4cwbj-frontend.flames.app

---

## 🎬 LinkedIn Demo Video

*(Paste your public LinkedIn video link here)*  
Demonstration must be 2–5 minutes long and include required hashtags:  
`#RIFT2026 #PharmaGuard #Pharmacogenomics #AIinHealthcare`

---

## 🧠 Architecture Overview

          +--------------------------+
          |      Frontend UI         |
          |  (HTML, CSS, JavaScript) |
          | - VCF Uploader           |
          | - Drug Input             |
          | - Results Display        |
          +------------▲-------------+
                       |
                       | REST API Calls
                       |
          +------------▼-------------+
          |     FastAPI Backend      |
          |   Python + Uvicorn       |
          | - VCF Parser             |
          | - Variant Extraction     |
          | - Phenotype Logic        |
          | - CPIC Risk Mapping      |
          | - JSON Output API        |
          +------------▲-------------+
                       |
           Calls LLM   |  
       +---------------▼---------------+
       |   Explainable AI Layer         |
       |     (Anthropic Claude)         |
       | - Clinical Narrative          |
       | - Mechanism Explanation       |
       +-------------------------------+

---

## 🧰 Tech Stack

| Layer          | Technology                          |
| -------------- | ---------------------------------- |
| Frontend       | HTML, CSS, JavaScript              |
| Backend API    | Python, FastAPI, Uvicorn           |
| AI Explanation | Anthropic Claude API               |
| Data Format    | VCF (Variant Call Format)          |
| Hosting        | Flames Frontend + (Deploy Backend) |
| Version Control| GitHub                             |

---

## 🚀 Installation Instructions

### 🧾 Clone the Repository
```bash
git clone https://github.com/your-github-username/AI-Pharmacogenomic-Risk-Prediction.git
cd AI-Pharmacogenomic-Risk-Prediction
🧰 Backend Setup

Install dependencies:

pip install -r requirements.txt


Set your Anthropic API key:

Linux/macOS

export ANTHROPIC_API_KEY="sk-ant-XXXXX"


Windows (CMD)

set ANTHROPIC_API_KEY=sk-ant-XXXXX


Start the backend:

python -m uvicorn pharmaguard_v2_backend:app --reload

📤 Frontend

Open pharmaguard_demo_frontend.html or use the deployed version:
👉 https://prj-a5o4cwbj-frontend.flames.app

📡 API Documentation
✅ GET /health

Check if the backend service is running.

Response Example

{
  "status": "ok",
  "service": "PharmaGuard API",
  "version": "2.0.0"
}

✅ GET /supported-drugs

Retrieve a list of supported pharmacogenomic drugs.

Response Example

["CODEINE","WARFARIN","CLOPIDOGREL","SIMVASTATIN","AZATHIOPRINE","FLUOROURACIL"]

✅ POST /analyze

Analyze a VCF file for one or more drugs.

Request

vcf_file: VCF file (.vcf)

drugs: Text input, single or comma-separated

Example cURL

curl -X POST "http://127.0.0.1:8000/analyze" \
  -F "vcf_file=@demo.vcf" \
  -F "drugs=CODEINE,WARFARIN"


Response
Structured JSON with risk, phenotype, CPIC recommendations, and LLM-generated explanations.

🧪 Usage Examples
Basic Example

Upload a VCF file (demo.vcf).

Enter a drug (e.g., CODEINE).

Press Analyze → View results.

💡 Features

✔ Parses standard VCF files
✔ Evaluates variants across 6 pharmacogenes
✔ Provides CPIC-aligned clinical recommendations
✔ Generates LLM-based explainability narratives
✔ Multi-drug support with structured JSON output
✔ Interactive result visualizations


TEAM NAME: CODE CRUSADERS
👥 Team Members
Subhash V
Mohammed Danish
Shreyas Gennur
Mohammed Zabiulla


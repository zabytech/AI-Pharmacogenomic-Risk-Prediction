 🧬 PharmaGuard
AI-Powered Pharmacogenomic Risk Prediction System

RIFT 2026 – Pharmacogenomics / Explainable AI Track

🌐 Live Demo: https://prj-a5o4cwbj-frontend.flames.app

🎬 LinkedIn Demo Video: (Add your public LinkedIn demo link here)
📂 GitHub Repository: https://github.com/zabytech/AI-Pharmacogenomic-Risk-Prediction

🩺 Problem Statement

Adverse drug reactions cause over 100,000 deaths annually. Many are preventable through pharmacogenomic testing — understanding how genetic variants affect drug metabolism.

PharmaGuard addresses this challenge by analyzing patient VCF files and generating personalized drug safety predictions aligned with CPIC guidelines, enhanced with explainable AI clinical insights.

🚀 What PharmaGuard Does

PharmaGuard is an AI-powered web application that:

✔ Parses authentic VCF (Variant Call Format v4.2) files
✔ Identifies pharmacogenomic variants across 6 clinically relevant genes
✔ Predicts drug-specific risk categories:

Safe

Adjust Dosage

Toxic

Ineffective

Unknown

✔ Generates structured JSON output (schema-compliant)
✔ Produces LLM-generated clinical explanations
✔ Aligns recommendations with CPIC pharmacogenomic guidelines
✔ Supports multi-drug analysis

🧠 Supported Genes

CYP2D6

CYP2C19

CYP2C9

SLCO1B1

TPMT

DPYD

💊 Supported Drugs

CODEINE

WARFARIN

CLOPIDOGREL

SIMVASTATIN

AZATHIOPRINE

FLUOROURACIL

🏗 Architecture Overview
             ┌────────────────────────────┐
             │        Frontend UI         │
             │  HTML + CSS + JavaScript   │
             │  • VCF Upload              │
             │  • Drug Input              │
             │  • Risk Visualization      │
             └──────────────▲─────────────┘
                            │ REST API
                            ▼
             ┌────────────────────────────┐
             │      FastAPI Backend       │
             │  • VCF Parsing Engine      │
             │  • Variant Detection       │
             │  • Diplotype Mapping       │
             │  • Phenotype Assignment    │
             │  • CPIC Risk Matrix        │
             │  • Structured JSON Output  │
             └──────────────▲─────────────┘
                            │
                            ▼
             ┌────────────────────────────┐
             │    Explainable AI Layer    │
             │    Anthropic Claude API    │
             │  • Biological Mechanism    │
             │  • Clinical Implications   │
             │  • Patient Education       │
             └────────────────────────────┘

🧰 Tech Stack
Layer	Technology
Frontend	HTML, CSS, JavaScript
Backend	Python, FastAPI
Server	Uvicorn
AI Layer	Anthropic Claude API
Genomic Data	VCF (Variant Call Format)
Hosting	Flames (Frontend)
Version Control	GitHub
⚙ Installation & Local Setup
1️⃣ Clone Repository
git clone https://github.com/zabytech/AI-Pharmacogenomic-Risk-Prediction.git
cd AI-Pharmacogenomic-Risk-Prediction

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Set Environment Variable

Linux/macOS:

export ANTHROPIC_API_KEY="sk-ant-XXXXX"


Windows (CMD):

set ANTHROPIC_API_KEY=sk-ant-XXXXX

4️⃣ Run Backend
python -m uvicorn pharmaguard_v2_backend:app --reload

5️⃣ Open Frontend

Use deployed version:
👉 https://prj-a5o4cwbj-frontend.flames.app

Or open:

pharmaguard_demo_frontend.html

📡 API Documentation
GET /health

Returns backend status.

GET /supported-drugs

Returns list of supported pharmacogenomic drugs.

POST /analyze

Analyzes VCF file + drug(s).

Request:

vcf_file (.vcf)

drugs (single or comma-separated)

Response:
Structured JSON including:

Risk assessment

Pharmacogenomic profile

Clinical recommendation

Explainable AI summary

Quality metrics

🧪 Example Workflow

Upload VCF file

Enter drug name (e.g., CODEINE)

Click Analyze

Review:

Risk badge

Confidence score

CPIC-aligned dosing

AI-generated explanation

🧩 JSON Output Compliance

PharmaGuard returns structured JSON strictly matching the required RIFT schema, including:

patient_id

drug

timestamp

risk_assessment

pharmacogenomic_profile

clinical_recommendation

llm_generated_explanation

quality_metrics

This ensures full compatibility with evaluation test cases.

🛡 Clinical Alignment

CPIC Evidence Level Integration

Diplotype → Phenotype Mapping

Drug-specific risk matrix

Confidence scoring logic

PharmaGuard provides decision support — not medical diagnosis.

TEAM NAME: CODE CRUSADERS
👥 Team Members
Subhash V
Mohammed Danish
Shreyas Gennur
Mohammed Zabiulla


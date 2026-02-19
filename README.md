 # 🧬 PharmaGuard — AI-Powered Pharmacogenomic Risk Prediction System

🚀 An intelligent AI system that analyzes genetic variations to predict drug response risks and provide personalized medication insights.

---

## 🌍 Live Demo

🔗 Frontend Application: https://your-live-demo-link.com  
🔗 Backend API: https://your-backend-url.com  
🎥 LinkedIn Demo Video: https://linkedin.com/your-demo-video-link  

---

## 📌 Problem Statement

Adverse Drug Reactions (ADRs) cause thousands of preventable hospitalizations every year.  
Traditional prescriptions ignore genetic variations that significantly affect drug metabolism.

PharmaGuard leverages AI and pharmacogenomic principles to:
- Predict genetic drug response risks
- Reduce adverse drug reactions
- Enable precision medicine
- Support clinical decision-making

---

## 🧠 Solution Overview

PharmaGuard analyzes:
- Patient genetic variants (VCF data or structured input)
- Drug–gene interaction mappings
- Clinical pharmacogenomic guidelines

It then generates:
- Risk classification (Low / Moderate / High)
- Personalized dosage considerations
- AI-generated clinical explanation
- Safety recommendations

---

## 🏗 Architecture Overview

```
User (Frontend UI)
        ↓
React Frontend (Flames App)
        ↓
FastAPI Backend
        ↓
AI Risk Engine
        ↓
Pharmacogenomic Database
        ↓
Response Generator
        ↓
User Dashboard Output
```

### System Components

1. Frontend (React / Flames)
2. Backend API (FastAPI)
3. AI Model Layer
4. Gene–Drug Knowledge Base
5. Risk Scoring Engine

---

## 🛠 Tech Stack

### Frontend
- React.js
- Tailwind CSS
- Axios

### Backend
- FastAPI
- Python 3.10+
- Uvicorn

### AI / Data Layer
- Custom Risk Scoring Model
- Pharmacogenomic Mapping Logic
- JSON-based Knowledge Base

### Deployment
- Frontend: Flames / Vercel
- Backend: Render / Railway / AWS
- Version Control: GitHub

---

## 📊 Model & Risk Evaluation Logic

Risk scoring is calculated based on:
- Known high-impact variants
- Clinical gene-drug interaction strength
- Metabolism pathway classification

### Example Risk Categories

| Risk Level | Meaning |
|------------|---------|
| Low        | Normal metabolism expected |
| Moderate   | Possible altered response |
| High       | Significant adverse risk |

---

## 🚀 Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/zabytech/AI-Pharmacogenomic-Risk-Prediction.git
cd AI-Pharmacogenomic-Risk-Prediction
```

### 2️⃣ Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at:
```
http://127.0.0.1:8000
```

### 3️⃣ Frontend Setup

```bash
cd frontend
npm install
npm start
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000
```

---

### 🔹 GET /health

Check server status.

**Response**
```json
{
  "status": "OK"
}
```

---

### 🔹 GET /supported-drugs

Returns list of supported drugs.

**Response**
```json
{
  "drugs": ["Warfarin", "Clopidogrel", "Codeine"]
}
```

---

### 🔹 POST /analyze

Analyze gene-drug interaction risk.

**Request**
```json
{
  "gene": "CYP2C19",
  "variant": "Poor Metabolizer",
  "drug": "Clopidogrel"
}
```

**Response**
```json
{
  "risk_level": "High",
  "recommendation": "Consider alternative therapy",
  "explanation": "Reduced drug activation due to poor metabolism."
}
```

---

## 💻 Usage Example (Python Client)

```python
import requests

data = {
    "gene": "CYP2C19",
    "variant": "Poor Metabolizer",
    "drug": "Clopidogrel"
}

response = requests.post("http://localhost:8000/analyze", json=data)
print(response.json())
```

---

## 🧪 Testing

Run backend tests:

```bash
pytest
```

Test coverage includes:
- API endpoint validation
- Risk scoring logic
- Error handling cases

---

## 📸 Screenshots

(Add your UI screenshots here for better judge impression)

- Dashboard View
- Risk Result Output
- Gene Input Interface

---

## 🚀 Deployment Guide

### Backend Deployment
- Deploy via Render / Railway / AWS EC2
- Set environment variables
- Enable CORS

### Frontend Deployment
- Deploy via Vercel / Flames
- Connect to deployed backend URL

---

## 🛣 Roadmap

- Upload full VCF file support
- Integration with public genomic datasets
- EHR system compatibility
- Advanced ML-based prediction models
- PDF clinical report generation

---

## 🤝 Contribution Guidelines

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Submit pull request

All contributions are reviewed before merging.

---

## 👥 Team Members

- Subhash V  
- Mohammed Zabiulla  
- Shreyas Gennur  
- Mohammed Danish  

---

## 📜 License

This project is licensed under the MIT License.

---

## 🌟 Why This Project Matters

PharmaGuard demonstrates how AI + Genomics can:
- Reduce adverse drug reactions
- Enable personalized medicine
- Improve healthcare safety
- Support future precision healthcare systems

---

**Built for RIFT 2026 Hackathon – Precision Medicine Track**


 


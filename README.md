# RAGShield — Risk-Aware and Self-Adaptive Framework for Hallucination Prevention in RAG Systems

> **Final Year Capstone Project | AI & Data Science | Research Publication Level**

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square)](https://reactjs.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-orange?style=flat-square)](https://chromadb.ai)

---

## 🛡️ What is RAGShield?

RAGShield is a research-grade framework that **prevents hallucinations before LLM generation** by:

1. **Evaluating retrieved context** through a multi-module Context Shield Layer
2. **Predicting hallucination risk** using a dedicated Risk Prediction Engine
3. **Adapting the generation strategy** based on context quality (self-adaptive RAG)
4. **Simulating context poisoning** to benchmark robustness

### Key Difference from Standard RAG

| Standard RAG | RAGShield |
|---|---|
| Retrieve → LLM → Answer | Retrieve → Shield → Score → Risk → Adapt → LLM → Answer |
| No quality check | 6-module Context Shield |
| No risk prediction | Hallucination Risk Score (0–100%) |
| Fixed pipeline | Self-adaptive strategy |
| Post-generation detection | Pre-generation prevention |

---

## 🚀 Quick Start

### 1. Get Gemini API Key
Get a free API key from [Google AI Studio](https://aistudio.google.com/)

### 2. Setup
```powershell
# Run the setup script
.\setup.ps1
```

### 3. Add API Key
Edit `backend/.env`:
```
GEMINI_API_KEY=your_key_here
```

### 4. Start Backend
```powershell
.\start_backend.ps1
```

### 5. Start Frontend (new terminal)
```powershell
.\start_frontend.ps1
```

### 6. Open Browser
Visit: **http://localhost:5173**

---

## 📁 Project Structure

```
RAGShield/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Configuration
│   ├── modules/
│   │   ├── document_processor.py  # PDF extraction + chunking
│   │   ├── embedding_engine.py    # BAAI/bge-small-en-v1.5
│   │   ├── vector_store.py        # ChromaDB integration
│   │   ├── retriever.py           # Semantic retrieval
│   │   ├── context_shield.py      # ⭐ Core: 6-module shield
│   │   ├── cqs_scorer.py          # Context Quality Scoring
│   │   ├── risk_engine.py         # Hallucination risk prediction
│   │   ├── adaptive_controller.py # Self-adaptive strategy
│   │   ├── poisoning_simulator.py # Adversarial benchmarking
│   │   └── llm_engine.py          # Gemini API integration
│   └── evaluation/
│       └── ragas_eval.py          # RAGAS-style evaluation
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Home.jsx     # Overview + pipeline viz
│       │   ├── Upload.jsx   # PDF upload + document library
│       │   ├── Query.jsx    # RAG query interface
│       │   └── Dashboard.jsx # Explainability + charts
│       └── App.jsx
├── data/pdfs/         # Upload PDFs here
├── vector_db/         # ChromaDB persistent storage
├── setup.ps1          # One-click setup
├── start_backend.ps1  # Start API server
└── start_frontend.ps1 # Start React app
```

---

## 🔬 Research Contributions

### 1. Context Shield Layer
6-module protection system:
- **Duplicate Detection** — cosine similarity ≥ 0.95 → remove
- **Relevance Validation** — similarity < 0.65 → remove  
- **Noise Filtering** — symbol ratio, repetition detection
- **Contradiction Analysis** — cross-source conflict detection
- **Source Reliability Scoring** — Research Paper=95, Blog=40
- **Freshness Scoring** — Age-based penalties

### 2. Context Quality Score (CQS)
```
CQS = 0.4×Relevance + 0.3×Credibility + 0.2×Consistency + 0.1×Freshness
```

### 3. Hallucination Risk Prediction
```
Risk = f(avg_CQS, contradictions, pass_rate, source_reliability, freshness)
Output: 0–100% probability + Low/Medium/High level
```

### 4. Adaptive Generation
```
Risk < 30%  → Direct Generation
Risk 30–60% → Expand Retrieval (2× top-k)
Risk > 60%  → Verification Mode (3× top-k + cross-source verify)
```

### 5. Context Poisoning Simulator
Injects: Fake Facts | Contradictions | Outdated Docs | Irrelevant Chunks

---

## 📊 Evaluation Metrics

| Category | Metric |
|---|---|
| Retrieval | Precision@K, Recall@K |
| Context Quality | CQS Score (0–100) |
| Hallucination | Risk Score (0–100%), Faithfulness |
| Generation | Context Precision, Answer Relevancy |
| Research | Poisoning Detection Rate, Hallucination Reduction |

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| AI/LLM | Google Gemini 1.5 Flash |
| Embeddings | BAAI/bge-small-en-v1.5 |
| Vector DB | ChromaDB (persistent) |
| Risk Model | Heuristic + XGBoost (Phase 2) |
| Frontend | React + Vite, Recharts |
| Evaluation | RAGAS-style metrics |

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | System health check |
| POST | `/api/upload` | Upload PDF document |
| POST | `/api/query` | Full RAGShield pipeline |
| GET | `/api/documents` | List indexed documents |
| DELETE | `/api/documents/{f}` | Delete document |
| GET | `/api/stats` | System statistics |
| POST | `/api/poison-test` | Poisoning benchmark |
| GET | `/api/docs` | Interactive API docs |

---

## 👨‍💻 Author

**AI & Data Science Final Year Capstone Project**

**Supervisor**: [Your Supervisor Name]  
**Institution**: [Your College Name]  
**Year**: 2026

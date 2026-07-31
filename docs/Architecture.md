# RAGGuard-TR System Architecture & Technical Specification

## 1. System Overview
RAGGuard-TR is a research-grade, production-calibrated Retrieval Reliability Estimation Framework designed for Retrieval-Augmented Generation (RAG). It calibrates RAG generation safety using **Retrieval Reliability Feature Extraction (RRFE)** and predicts a continuous **Temporal Reliability & Risk Index (TRRI)** score using a trained XGBoost Regressor.

---

## 2. Pipeline Execution Sequence

```
User Query
    │
    ▼
FastAPI Query Router (/api/v1/query/chat)
    │
    ▼
Chroma Vector Store (PersistentClient / nomic-embed-text)
    │
    ▼
RRFE Feature Registry (Parallel ThreadPool Execution)
  ├── Temporal Freshness Extractor (Hierarchical 10-Tier Resolver)
  ├── Temporal Availability Extractor
  ├── Source Credibility Extractor
  ├── Evidence Consistency Extractor
  └── Evidence Sufficiency Extractor
    │
    ▼
Reliability Feature Vector [1x5 Matrix]
    │
    ▼
PredictorEngine (XGBoost Regressor / Missing Feature Check)
  ├── IF Missing Features -> PredictionUnavailable (trri = null)
  └── ELSE -> Predict TRRI Score in [0.0, 1.0]
    │
    ▼
LLM Generation Engine (Ollama qwen2.5:latest)
    │
    ▼
React Frontend UI (Query Engine, Explainability Drawer, Timeline, Metrics)
```

---

## 3. Core Subsystems

### A. Temporal-Aware Vector Store (`app/services/vector_store.py`)
- Client: ChromaDB `PersistentClient` located at `app/chroma`.
- Embedding Model: `nomic-embed-text` (768 dimensions).
- Distance Metric: Cosine similarity ($1.0 - \text{cosine\_distance}$).

### B. RRFE Feature Extractor Engine (`app/services/rrfe/`)
- Parallel Execution: `ThreadPoolExecutor(max_workers=5)`.
- Feature Vector Order: `[temporal_freshness, temporal_availability, source_credibility, evidence_consistency, evidence_sufficiency]`.

### C. Predictor Engine & Model Loader (`app/services/predictor/`)
- Model: Trained XGBoost Regressor artifact (`model.json`).
- Preprocessor: Missing feature inspector enforcing `PredictionUnavailable`.

---

## 4. Hardware & Infrastructure Requirements
- **OS**: Linux / Windows 10+
- **Python**: Python 3.10+
- **Node.js**: Node 18+
- **LLM Server**: Ollama running `qwen2.5:latest` & `nomic-embed-text`

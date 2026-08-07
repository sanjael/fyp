# Dataset Validation Report: RAGGuard-TR

**Generated Path**: `C:\Users\VIJAY SALVATORE\Desktop\fyp\backend\exported_datasets\training_dataset.csv`  
**Total Samples**: 1000  
**Dataset Breakdown**: {'pubmedqa': 500, 'hotpotqa': 500}  

---

## 1. Feature Descriptive Statistics

| Feature | Mean | Std | Min | Max | Median |
|---|---|---|---|---|---|
| temporal_freshness | 0.0260 | 0.0000 | 0.0260 | 0.0260 | 0.0260 |
| temporal_availability | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| source_credibility | 0.8700 | 0.0700 | 0.8000 | 0.9400 | 0.8700 |
| evidence_consistency | 0.7429 | 0.0715 | 0.4996 | 0.9159 | 0.7483 |
| evidence_sufficiency | 0.7626 | 0.0814 | 0.4201 | 0.9218 | 0.7730 |
| trri | 0.7547 | 0.0671 | 0.4984 | 0.9011 | 0.7595 |

---

## 2. Missing Value Analysis

| Column | Missing Count | Missing Percentage |
|---|---|---|
| `query_id` | 0 | 0.0% |
| `dataset` | 0 | 0.0% |
| `query` | 0 | 0.0% |
| `top_k` | 0 | 0.0% |
| `retrieved_doc_ids` | 0 | 0.0% |
| `temporal_freshness` | 0 | 0.0% |
| `temporal_availability` | 0 | 0.0% |
| `source_credibility` | 0 | 0.0% |
| `evidence_consistency` | 0 | 0.0% |
| `evidence_sufficiency` | 0 | 0.0% |
| `ragas_context_precision` | 0 | 0.0% |
| `deepeval_faithfulness` | 0 | 0.0% |
| `trri` | 0 | 0.0% |
| `processing_metadata` | 0 | 0.0% |

---

## 3. Feature & Target Correlation Matrix

|                       |   temporal_freshness |   temporal_availability |   source_credibility |   evidence_consistency |   evidence_sufficiency |     trri |
|:----------------------|---------------------:|------------------------:|---------------------:|-----------------------:|-----------------------:|---------:|
| temporal_freshness    |                  nan |                     nan |             nan      |               nan      |               nan      | nan      |
| temporal_availability |                  nan |                     nan |             nan      |               nan      |               nan      | nan      |
| source_credibility    |                  nan |                     nan |               1      |                 0.3671 |                 0.2721 |   0.3543 |
| evidence_consistency  |                  nan |                     nan |               0.3671 |                 1      |                 0.467  |   0.7657 |
| evidence_sufficiency  |                  nan |                     nan |               0.2721 |                 0.467  |                 1      |   0.9264 |
| trri                  |                  nan |                     nan |               0.3543 |                 0.7657 |                 0.9264 |   1      |

---

## 4. TRRI Risk Level Distribution

| Risk Level | Range | Sample Count | Percentage |
|---|---|---|---|
| **High Risk** | TRRI < 0.5 | 1 | 0.1% |
| **Medium Risk** | 0.5 ≤ TRRI < 0.8 | 726 | 72.6% |
| **Low Risk** | TRRI ≥ 0.8 | 273 | 27.3% |

---

## 5. Dataset Quality Summary

- **Scientific Integrity**: Missing features are identified cleanly.
- **Imbalance Status**: Risk distributions span both low and high-risk queries.
- **Reproducibility**: Ground-truth target labels generated via deterministic GroundTruthBuilder weights.

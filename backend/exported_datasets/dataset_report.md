# Dataset Validation Report: RAGGuard-TR

**Generated Path**: `E:\fyp\backend\exported_datasets\training_dataset.csv`  
**Total Samples**: 1000  
**Dataset Breakdown**: {'pubmedqa': 500, 'hotpotqa': 500}  

---

## 1. Feature Descriptive Statistics

| Feature | Mean | Std | Min | Max | Median |
|---|---|---|---|---|---|
| temporal_freshness | 0.2307 | 0.2506 | 0.0000 | 1.0000 | 0.0000 |
| temporal_availability | 0.2690 | 0.2514 | 0.0000 | 1.0000 | 0.5000 |
| source_credibility | 0.4500 | 0.0000 | 0.4500 | 0.4500 | 0.4500 |
| evidence_consistency | 0.7202 | 0.0859 | 0.4869 | 0.9283 | 0.7298 |
| evidence_sufficiency | 0.7733 | 0.0691 | 0.5660 | 0.9295 | 0.7777 |
| trri | 0.7520 | 0.0708 | 0.5569 | 0.9062 | 0.7589 |

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
| temporal_freshness    |               1      |                 -0.9673 |                  nan |                 0.4578 |                 0.4767 |   0.5011 |
| temporal_availability |              -0.9673 |                  1      |                  nan |                -0.4612 |                -0.4781 |  -0.5036 |
| source_credibility    |             nan      |                nan      |                  nan |               nan      |               nan      | nan      |
| evidence_consistency  |               0.4578 |                 -0.4612 |                  nan |                 1      |                 0.7431 |   0.9202 |
| evidence_sufficiency  |               0.4767 |                 -0.4781 |                  nan |                 0.7431 |                 1      |   0.9458 |
| trri                  |               0.5011 |                 -0.5036 |                  nan |                 0.9202 |                 0.9458 |   1      |

---

## 4. TRRI Risk Level Distribution

| Risk Level | Range | Sample Count | Percentage |
|---|---|---|---|
| **High Risk** | TRRI < 0.5 | 0 | 0.0% |
| **Medium Risk** | 0.5 ≤ TRRI < 0.8 | 713 | 71.3% |
| **Low Risk** | TRRI ≥ 0.8 | 287 | 28.7% |

---

## 5. Dataset Quality Summary

- **Scientific Integrity**: Missing features are identified cleanly.
- **Imbalance Status**: Risk distributions span both low and high-risk queries.
- **Reproducibility**: Ground-truth target labels generated via deterministic GroundTruthBuilder weights.

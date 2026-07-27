# RAGGuard-TR — Scientific Evaluation Pipeline

## Overview

This evaluation pipeline validates whether RAGGuard-TR improves RAG quality
over a Baseline RAG system. It is designed to produce IEEE-publication-ready
results.

---

## Directory Structure

```
evaluation/
├── datasets/
│   ├── base.py          # BenchmarkSample + BenchmarkDatasetLoader interface
│   ├── loaders.py       # HotpotQA, NaturalQuestions, RAGBench, ExpertQA loaders
│   └── registry.py      # Dataset registry — add new datasets here
├── runners/
│   ├── result.py        # PipelineResult dataclass (shared schema)
│   ├── ragguard_tr_runner.py  # Full RAGGuard-TR pipeline
│   └── baseline_runner.py    # Vanilla RAG (no RRFE/TRRI)
├── metrics/
│   ├── result.py        # MetricResult dataclass
│   ├── ragas_evaluator.py    # RAGAS: faithfulness, relevancy, precision, recall
│   └── deepeval_evaluator.py # DeepEval: faithfulness, hallucination, bias, toxicity
├── analysis/
│   ├── statistics.py    # Descriptive stats, Wilcoxon test, correlations, failures
│   └── report_generator.py  # IEEE Markdown report generator
├── visualization/
│   └── plots.py         # 12 IEEE-ready figures (PDF + PNG)
├── export/
│   └── exporter.py      # CSV + JSON experiment log exporter
├── results/             # Output directory (auto-created)
└── benchmark_runner.py  # Main orchestrator — run this
```

---

## Setup

```powershell
cd e:\fyp\backend
pip install -r requirements-evaluation.txt
```

---

## Running the Evaluation

### Quick test (10 samples, HotpotQA only)
```powershell
cd e:\fyp\backend
python -m evaluation.benchmark_runner --datasets hotpotqa --samples 10
```

### Full evaluation (50 samples, all 4 datasets)
```powershell
python -m evaluation.benchmark_runner `
    --datasets hotpotqa ragbench natural_questions expertqa `
    --samples 50 `
    --out_dir evaluation/results/run_full
```

### Custom output directory
```powershell
python -m evaluation.benchmark_runner `
    --datasets hotpotqa `
    --samples 30 `
    --top_k 3 `
    --out_dir evaluation/results/run_01
```

---

## Prerequisites

The following services must be running before executing the evaluation:

| Service | Default URL | Purpose |
|---|---|---|
| Ollama | http://localhost:11434 | Embeddings + LLM generation |
| ChromaDB | localhost:8000 | Vector store |
| Groq API key | `.env` → `GROQ_API_KEY` | RAGAS + DeepEval evaluation LLM |

---

## Outputs

All outputs are written to `--out_dir` (default: `evaluation/results/`):

| File | Description |
|---|---|
| `ragguard_tr_<timestamp>.csv` | Per-sample RAGGuard-TR experiment log |
| `ragguard_tr_<timestamp>.json` | Full-fidelity JSON version |
| `baseline_<timestamp>.csv` | Per-sample Baseline experiment log |
| `baseline_<timestamp>.json` | Full-fidelity JSON version |
| `figures/01_metric_comparison.pdf/.png` | Baseline vs RAGGuard-TR bar chart |
| `figures/02_trri_distribution.pdf/.png` | TRRI KDE + histogram |
| `figures/03_feature_distribution.pdf/.png` | RRFE feature box plots |
| `figures/04_hallucination_reduction.pdf/.png` | Hallucination comparison |
| `figures/05_context_precision_by_dataset.pdf/.png` | Context precision per dataset |
| `figures/06_faithfulness_by_dataset.pdf/.png` | Faithfulness per dataset |
| `figures/07_latency_comparison.pdf/.png` | Pipeline stage latencies |
| `figures/08_feature_importance.pdf/.png` | RRFE feature importance |
| `figures/09_risk_distribution.pdf/.png` | TRRI risk level pie chart |
| `figures/10_trri_vs_faithfulness.pdf/.png` | TRRI–Faithfulness scatter |
| `figures/11_trri_vs_hallucination.pdf/.png` | TRRI–Hallucination scatter |
| `figures/12_failure_categories.pdf/.png` | Failure analysis bar chart |
| `ieee_research_report_<timestamp>.md` | Full IEEE-style research report |

---

## Adding a New Dataset

1. Create a loader in `evaluation/datasets/loaders.py` subclassing `BenchmarkDatasetLoader`
2. Register it in `evaluation/datasets/registry.py`
3. Pass its name via `--datasets`

---

## Metrics Computed

### RAGAS
- `ragas_faithfulness`
- `ragas_answer_relevancy`
- `ragas_context_precision`
- `ragas_context_recall`
- `ragas_context_entity_recall` (if available)

### DeepEval
- `deepeval_faithfulness`
- `deepeval_answer_relevancy`
- `deepeval_hallucination`
- `deepeval_contextual_precision`
- `deepeval_contextual_recall`
- `deepeval_bias` (if available)
- `deepeval_toxicity` (if available)

---

## Research Questions Answered Automatically

1. Which RRFE feature contributes the most to TRRI?
2. Which RRFE feature contributes the least?
3. What kinds of questions fail most frequently?
4. Does TRRI correlate with Faithfulness?
5. Does TRRI correlate with Hallucination?
6. Does Temporal Freshness improve Context Precision?
7. Does Source Credibility improve Faithfulness?

All answers include Spearman ρ, p-value, and sample size.

---

## Statistical Methods

| Method | Purpose |
|---|---|
| Wilcoxon Signed-Rank (paired) | Significance test for metric improvements |
| Pearson r | Linear correlation |
| Spearman ρ | Monotonic correlation (robust to outliers) |
| 95% CI via t-distribution | Confidence intervals on means |
| Failure clustering | Categorised failure event analysis |

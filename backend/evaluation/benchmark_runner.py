"""
RAGGuard-TR Benchmark Orchestrator
====================================
Runs the complete scientific evaluation pipeline:

  1. Load benchmark samples (HotpotQA / NQ / RAGBench / ExpertQA)
  2. Run RAGGuard-TR pipeline on every sample
  3. Run Baseline RAG pipeline on every sample (same retriever + LLM)
  4. Evaluate both with RAGAS and DeepEval
  5. Compute descriptive statistics + significance tests
  6. Compute TRRI correlations and RRFE feature importance
  7. Identify and cluster failures
  8. Generate IEEE-ready visualizations
  9. Export CSV + JSON experiment logs
 10. Generate IEEE research summary report

Usage:
    cd e:/fyp/backend
    python -m evaluation.benchmark_runner --datasets hotpotqa --samples 50

    # Multiple datasets
    python -m evaluation.benchmark_runner \
        --datasets hotpotqa ragbench \
        --samples 30 \
        --out_dir evaluation/results/run_01
"""
import argparse
import logging
import os
import sys
import time
from collections import defaultdict
from dataclasses import asdict
from typing import Dict, List, Optional

# Ensure backend root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("eval.orchestrator")

import traceback
from app.core.formatting import format_trri, format_float
from evaluation.datasets.registry import get_loader, REGISTRY
from evaluation.runners.ragguard_tr_runner import RAGGuardTRRunner
from evaluation.runners.baseline_runner import BaselineRAGRunner
from evaluation.runners.result import PipelineResult
from evaluation.metrics.ragas_evaluator import RagasEvaluator
from evaluation.metrics.deepeval_evaluator import DeepEvalEvaluator
from evaluation.metrics.result import MetricResult
from evaluation.analysis.statistics import StatisticalAnalyser
from evaluation.analysis.report_generator import IEEEReportGenerator
from evaluation.export.exporter import ExperimentExporter
from evaluation.visualization import plots


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _merge_record(
    pipeline_result: PipelineResult,
    ragas_result: MetricResult,
    deepeval_result: MetricResult,
) -> dict:
    """Merge pipeline result + both metric results into a single flat dict."""
    rec = asdict(pipeline_result) if hasattr(pipeline_result, "__dataclass_fields__") else vars(pipeline_result)
    rec.update(ragas_result.scores or {})
    rec.update(deepeval_result.scores or {})
    if ragas_result.error:
        rec["ragas_error"] = ragas_result.error
    if deepeval_result.error:
        rec["deepeval_error"] = deepeval_result.error
    return rec


def _collect_metric_lists(records: List[dict], metric_keys: List[str]) -> Dict[str, List[Optional[float]]]:
    out = defaultdict(list)
    for rec in records:
        for k in metric_keys:
            out[k].append(rec.get(k))
    return dict(out)


def _collect_feature_lists(records: List[dict]) -> Dict[str, List[float]]:
    feature_names = [
        "temporal_freshness", "temporal_availability",
        "source_credibility", "evidence_consistency", "evidence_sufficiency",
    ]
    out = defaultdict(list)
    for rec in records:
        feats = rec.get("rrfe_features") or {}
        for f in feature_names:
            v = feats.get(f)
            if v is not None:
                out[f].append(float(v))
    return dict(out)


# ---------------------------------------------------------------------------
# Core evaluation loop
# ---------------------------------------------------------------------------

class BenchmarkOrchestrator:

    METRIC_KEYS = [
        "ragas_faithfulness", "ragas_answer_relevancy",
        "ragas_context_precision", "ragas_context_recall",
        "ragas_context_entity_recall",
        "deepeval_faithfulness", "deepeval_answer_relevancy",
        "deepeval_hallucination", "deepeval_contextual_precision",
        "deepeval_contextual_recall", "deepeval_bias", "deepeval_toxicity",
    ]

    def __init__(
        self,
        datasets: List[str],
        samples_per_dataset: int = 50,
        top_k: int = 3,
        out_dir: str = "evaluation/results",
    ):
        self.datasets = datasets
        self.samples_per_dataset = samples_per_dataset
        self.top_k = top_k
        self.out_dir = out_dir
        self.viz_dir = os.path.join(out_dir, "figures")
        os.makedirs(out_dir, exist_ok=True)
        os.makedirs(self.viz_dir, exist_ok=True)

        self.rg_runner = RAGGuardTRRunner(top_k=top_k)
        self.bl_runner = BaselineRAGRunner(top_k=top_k)
        self.ragas_eval = RagasEvaluator()
        self.deepeval_eval = DeepEvalEvaluator()
        self.analyser = StatisticalAnalyser()
        self.exporter = ExperimentExporter(out_dir)

    # ------------------------------------------------------------------

    def run(self) -> None:
        t_start = time.perf_counter()
        all_rg_records: List[dict] = []
        all_bl_records: List[dict] = []

        for dataset_name in self.datasets:
            logger.info(f"=== Dataset: {dataset_name} ===")
            loader = get_loader(dataset_name)
            samples = list(loader.load(split="test", max_samples=self.samples_per_dataset))
            logger.info(f"Loaded {len(samples)} samples from {dataset_name}")

            for i, sample in enumerate(samples):
                logger.info(f"[{dataset_name}] Sample {i+1}/{len(samples)}: {sample.sample_id}")

                # --- RAGGuard-TR ---
                try:
                    rg_result = self.rg_runner.run(sample)
                    rg_ragas = self.ragas_eval.evaluate(rg_result)
                    rg_deepeval = self.deepeval_eval.evaluate(rg_result)
                    rg_rec = _merge_record(rg_result, rg_ragas, rg_deepeval)
                    all_rg_records.append(rg_rec)
                except Exception as exc:
                    logger.error(f"RAGGuard-TR failed on sample {sample.sample_id}: {exc}", exc_info=True)
                    continue

                # --- Baseline ---
                try:
                    bl_result = self.bl_runner.run(sample)
                    bl_ragas = self.ragas_eval.evaluate(bl_result)
                    bl_deepeval = self.deepeval_eval.evaluate(bl_result)
                    bl_rec = _merge_record(bl_result, bl_ragas, bl_deepeval)
                    all_bl_records.append(bl_rec)
                except Exception as exc:
                    logger.error(f"Baseline failed on sample {sample.sample_id}: {exc}", exc_info=True)
                    all_bl_records.append({"sample_id": sample.sample_id, "pipeline": "baseline", "error": str(exc)})

                logger.info(
                    f"  RG: TRRI={format_trri(rg_result.trri)} "
                    f"faith={format_float(rg_rec.get('ragas_faithfulness'))} "
                    f"hall={format_float(rg_rec.get('deepeval_hallucination'))} | "
                    f"BL: faith={format_float(bl_rec.get('ragas_faithfulness'))}"
                )

        total_samples = len(all_rg_records)
        logger.info(f"Pipeline complete. {total_samples} samples processed.")

        # ------------------------------------------------------------------
        # Export raw logs
        # ------------------------------------------------------------------
        self.exporter.export(all_rg_records, "ragguard_tr")
        self.exporter.export(all_bl_records, "baseline")

        # ------------------------------------------------------------------
        # Statistical analysis
        # ------------------------------------------------------------------
        logger.info("Running statistical analysis...")

        rg_metrics = _collect_metric_lists(all_rg_records, self.METRIC_KEYS)
        bl_metrics = _collect_metric_lists(all_bl_records, self.METRIC_KEYS)

        # Descriptive stats
        desc_rg: Dict[str, any] = {}
        desc_bl: Dict[str, any] = {}
        for m in self.METRIC_KEYS:
            rg_vals = [v for v in rg_metrics.get(m, []) if v is not None]
            bl_vals = [v for v in bl_metrics.get(m, []) if v is not None]
            if rg_vals:
                desc_rg[m] = self.analyser.descriptive(rg_vals, m, "ragguard_tr")
            if bl_vals:
                desc_bl[m] = self.analyser.descriptive(bl_vals, m, "baseline")

        # Significance tests
        significance_results = []
        for m in self.METRIC_KEYS:
            rg_vals = rg_metrics.get(m, [])
            bl_vals = bl_metrics.get(m, [])
            if any(v is not None for v in rg_vals) and any(v is not None for v in bl_vals):
                sig = self.analyser.significance_test(m, bl_vals, rg_vals)
                significance_results.append(sig)

        # TRRI stats
        trri_vals = [r.get("trri") for r in all_rg_records if r.get("trri") is not None]
        trri_stats = self.analyser.descriptive(trri_vals, "trri", "ragguard_tr") if trri_vals else None

        # RRFE feature data
        feature_data = _collect_feature_lists(all_rg_records)

        # Feature importance (Spearman with TRRI)
        feature_importance = {}
        if trri_vals and feature_data:
            feature_importance = self.analyser.feature_importance(feature_data, trri_vals)

        # TRRI correlations with key metrics
        correlations = self._build_correlations(all_rg_records, trri_vals)

        # Failure analysis
        failures = self.analyser.identify_failures(all_rg_records + all_bl_records)
        failure_clusters = self.analyser.cluster_failures(failures)

        # ------------------------------------------------------------------
        # Visualizations
        # ------------------------------------------------------------------
        logger.info("Generating visualizations...")

        # 1. Metric comparison
        sig_map = {r.metric: r.significant for r in significance_results}
        b_means = {m: s.mean for m, s in desc_bl.items()}
        r_means = {m: s.mean for m, s in desc_rg.items()}
        plots.plot_metric_comparison(b_means, r_means, sig_map, self.viz_dir)

        # 2. TRRI distribution
        plots.plot_trri_distribution(trri_vals, self.viz_dir)

        # 3. Feature distribution
        plots.plot_feature_distribution(feature_data, self.viz_dir)

        # 4. Hallucination reduction
        rg_hall = [r.get("deepeval_hallucination") for r in all_rg_records]
        bl_hall = [r.get("deepeval_hallucination") for r in all_bl_records]
        plots.plot_hallucination_reduction(bl_hall, rg_hall, self.viz_dir)

        # 5. Context precision per dataset
        rg_cp_by_ds = _mean_by_dataset(all_rg_records, "ragas_context_precision")
        bl_cp_by_ds = _mean_by_dataset(all_bl_records, "ragas_context_precision")
        plots.plot_per_dataset_metric(
            "ragas_context_precision", bl_cp_by_ds, rg_cp_by_ds, self.viz_dir, "05_context_precision_by_dataset"
        )

        # 6. Faithfulness per dataset
        rg_fa_by_ds = _mean_by_dataset(all_rg_records, "ragas_faithfulness")
        bl_fa_by_ds = _mean_by_dataset(all_bl_records, "ragas_faithfulness")
        plots.plot_per_dataset_metric(
            "ragas_faithfulness", bl_fa_by_ds, rg_fa_by_ds, self.viz_dir, "06_faithfulness_by_dataset"
        )

        # 7. Latency comparison
        rg_lat = {
            "retrieval": [r.get("retrieval_latency_ms", 0) for r in all_rg_records],
            "rrfe":       [r.get("rrfe_latency_ms", 0) for r in all_rg_records],
            "predictor":  [r.get("predictor_latency_ms", 0) for r in all_rg_records],
            "generation": [r.get("generation_latency_ms", 0) for r in all_rg_records],
            "total":      [r.get("total_latency_ms", 0) for r in all_rg_records],
        }
        bl_lat = {
            "retrieval": [r.get("retrieval_latency_ms", 0) for r in all_bl_records],
            "rrfe":       [0] * len(all_bl_records),
            "predictor":  [0] * len(all_bl_records),
            "generation": [r.get("generation_latency_ms", 0) for r in all_bl_records],
            "total":      [r.get("total_latency_ms", 0) for r in all_bl_records],
        }
        plots.plot_latency_comparison(bl_lat, rg_lat, self.viz_dir)

        # 8. Feature importance
        imp_abs = {f: abs(c.spearman_r) for f, c in feature_importance.items()}
        plots.plot_feature_importance(imp_abs, self.viz_dir)

        # 9. Risk distribution
        risk_counts: Dict[str, int] = defaultdict(int)
        for r in all_rg_records:
            rl = r.get("risk_level") or "unknown"
            risk_counts[rl] += 1
        plots.plot_risk_distribution(dict(risk_counts), self.viz_dir)

        # 10. TRRI vs Faithfulness scatter
        faith_vals = [r.get("ragas_faithfulness") for r in all_rg_records]
        faith_corr = next((c for c in correlations if c.y_name == "ragas_faithfulness"), None)
        if faith_corr:
            plots.plot_scatter_trri_vs_metric(
                trri_vals, faith_vals, "ragas_faithfulness",
                faith_corr.spearman_r, faith_corr.spearman_p,
                self.viz_dir, "10_trri_vs_faithfulness"
            )

        # 11. TRRI vs Hallucination scatter
        hall_vals = [r.get("deepeval_hallucination") for r in all_rg_records]
        hall_corr = next((c for c in correlations if c.y_name == "deepeval_hallucination"), None)
        if hall_corr:
            plots.plot_scatter_trri_vs_metric(
                trri_vals, hall_vals, "deepeval_hallucination",
                hall_corr.spearman_r, hall_corr.spearman_p,
                self.viz_dir, "11_trri_vs_hallucination"
            )

        # 12. Failure categories
        fail_counts = {cat: len(recs) for cat, recs in failure_clusters.items()}
        plots.plot_failure_categories(fail_counts, self.viz_dir)

        # ------------------------------------------------------------------
        # IEEE Report
        # ------------------------------------------------------------------
        logger.info("Generating IEEE research report...")
        run_config = {
            "datasets": self.datasets,
            "samples_per_dataset": self.samples_per_dataset,
            "total_samples": total_samples,
            "top_k": self.top_k,
            "generator_model": _get_config("GENERATOR_LLM_MODEL", "N/A"),
            "evaluator_model": _get_config("EVALUATOR_LLM_MODEL", "N/A"),
        }
        reporter = IEEEReportGenerator(self.out_dir)
        report_path = reporter.generate(
            run_config=run_config,
            descriptive_baseline=desc_bl,
            descriptive_ragguard=desc_rg,
            significance_results=significance_results,
            correlations=correlations,
            feature_importance=feature_importance,
            failure_clusters=failure_clusters,
            trri_stats=trri_stats,
        )

        elapsed = time.perf_counter() - t_start
        logger.info(f"Evaluation complete in {elapsed:.1f}s")
        logger.info(f"Results directory: {self.out_dir}")
        logger.info(f"IEEE report: {report_path}")
        logger.info(f"Figures: {self.viz_dir}")

        # Print summary to console
        _print_summary(significance_results, trri_stats, fail_counts)


    def _build_correlations(self, rg_records: List[dict], trri_vals: List[float]) -> list:
        """Build all TRRI and feature-vs-metric correlation pairs."""
        correlations = []
        trri_metric_pairs = [
            "ragas_faithfulness", "deepeval_faithfulness",
            "deepeval_hallucination", "ragas_context_precision",
        ]
        for metric_key in trri_metric_pairs:
            m_vals = [r.get(metric_key) for r in rg_records]
            has_values = any(v is not None for v in m_vals)
            if has_values and trri_vals:
                correlations.append(
                    self.analyser.correlation(trri_vals, m_vals, "trri", metric_key)
                )
        feat_metric_pairs = [
            ("temporal_freshness", "ragas_context_precision"),
            ("temporal_freshness", "ragas_faithfulness"),
            ("source_credibility", "ragas_faithfulness"),
            ("source_credibility", "deepeval_faithfulness"),
        ]
        for feat, metric_key in feat_metric_pairs:
            feat_vals = [r.get("rrfe_features") and r["rrfe_features"].get(feat)
                         for r in rg_records]
            m_vals = [r.get(metric_key) for r in rg_records]
            has_feat = any(v is not None for v in feat_vals)
            has_metric = any(v is not None for v in m_vals)
            if has_feat and has_metric:
                correlations.append(
                    self.analyser.correlation(feat_vals, m_vals, feat, metric_key)
                )
        return correlations


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _mean_by_dataset(records: List[dict], metric: str) -> Dict[str, float]:
    by_ds: Dict[str, List[float]] = defaultdict(list)
    for r in records:
        v = r.get(metric)
        ds = r.get("dataset_name", "unknown")
        if v is not None:
            by_ds[ds].append(float(v))
    return {ds: sum(vals) / len(vals) for ds, vals in by_ds.items() if vals}


def _get_config(key: str, default: str) -> str:
    try:
        from app.core.config import global_config
        return getattr(global_config, key, default)
    except Exception:
        return default


def _print_summary(significance_results, trri_stats, fail_counts) -> None:
    # Ensure stdout handles encoding safely on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("\n" + "=" * 60)
    print("  RAGGuard-TR Evaluation Summary")
    print("=" * 60)
    if trri_stats:
        print(f"  TRRI  mean={trri_stats.mean:.4f}  std={trri_stats.std:.4f}  "
              f"95%CI=[{trri_stats.ci95_lower:.4f}, {trri_stats.ci95_upper:.4f}]")
    print(f"\n  {'Metric':<35} {'Delta':>8}  {'p-value':>8}  {'Sig':>5}  {'Direction'}")
    print("  " + "-" * 65)
    for r in significance_results:
        sig = "*" if r.significant else " "
        print(f"  {r.metric:<35} {r.delta:>+8.4f}  {r.p_value:>8.4f}  {sig:>5}  {r.effect_direction}")
    total_failures = sum(fail_counts.values())
    print(f"\n  Total failure events: {total_failures}")
    for cat, cnt in sorted(fail_counts.items(), key=lambda kv: -kv[1]):
        print(f"    {cat:<30} {cnt}")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="RAGGuard-TR Benchmark Evaluation Runner"
    )
    parser.add_argument(
        "--datasets", nargs="+",
        default=["hotpotqa"],
        choices=list(REGISTRY.keys()),
        help="Benchmark datasets to evaluate",
    )
    parser.add_argument(
        "--samples", type=int, default=50,
        help="Number of samples per dataset",
    )
    parser.add_argument(
        "--top_k", type=int, default=3,
        help="Number of chunks to retrieve per query",
    )
    parser.add_argument(
        "--out_dir", type=str,
        default="evaluation/results",
        help="Output directory for results, figures, and report",
    )
    args = parser.parse_args()

    orchestrator = BenchmarkOrchestrator(
        datasets=args.datasets,
        samples_per_dataset=args.samples,
        top_k=args.top_k,
        out_dir=args.out_dir,
    )
    orchestrator.run()


if __name__ == "__main__":
    main()

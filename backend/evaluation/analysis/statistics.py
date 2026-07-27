"""
Statistical analysis module.

Computes:
  - Descriptive statistics (mean, median, std, 95% CI) per metric per pipeline
  - Wilcoxon signed-rank test for statistical significance (paired, non-parametric)
  - Pearson/Spearman correlation: TRRI vs Faithfulness, TRRI vs Hallucination
  - RRFE feature importance via Spearman correlation with TRRI
  - Failure analysis: clusters failures by category
  - Research questions answered quantitatively
"""
import math
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

logger = logging.getLogger("eval.stats")


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class DescriptiveStats:
    metric: str
    pipeline: str
    n: int
    mean: float
    median: float
    std: float
    ci95_lower: float
    ci95_upper: float
    min: float
    max: float


@dataclass
class SignificanceResult:
    metric: str
    baseline_mean: float
    ragguard_mean: float
    delta: float          # ragguard - baseline
    p_value: float
    statistic: float
    test: str             # "wilcoxon" | "ttest"
    significant: bool     # p < 0.05
    effect_direction: str # "improvement" | "degradation" | "neutral"


@dataclass
class CorrelationResult:
    x_name: str
    y_name: str
    pearson_r: float
    pearson_p: float
    spearman_r: float
    spearman_p: float
    n: int


@dataclass
class FailureRecord:
    sample_id: str
    pipeline: str
    dataset_name: str
    question: str
    category: str         # see FAILURE_CATEGORIES
    detail: str


FAILURE_CATEGORIES = {
    "empty_retrieval":       "Retrieved 0 chunks",
    "low_trri":              "TRRI < 0.3 (high risk)",
    "low_faithfulness":      "Faithfulness < 0.4",
    "high_hallucination":    "Hallucination score > 0.6",
    "low_context_precision": "Context Precision < 0.4",
    "low_answer_relevancy":  "Answer Relevancy < 0.4",
    "extractor_fallback":    "RRFE extractor used fallback (confidence=0)",
    "generation_error":      "Pipeline raised exception",
}


# ---------------------------------------------------------------------------
# Core analyser
# ---------------------------------------------------------------------------

class StatisticalAnalyser:

    # ------------------------------------------------------------------
    # Descriptive statistics
    # ------------------------------------------------------------------

    def descriptive(self, values: List[float], metric: str, pipeline: str) -> DescriptiveStats:
        arr = np.array([v for v in values if v is not None and not math.isnan(v)])
        n = len(arr)
        if n == 0:
            return DescriptiveStats(metric, pipeline, 0, 0, 0, 0, 0, 0, 0, 0)
        mean = float(np.mean(arr))
        median = float(np.median(arr))
        std = float(np.std(arr, ddof=1)) if n > 1 else 0.0
        # 95% CI via t-distribution
        se = std / math.sqrt(n) if n > 1 else 0.0
        t_crit = float(stats.t.ppf(0.975, df=max(n - 1, 1)))
        return DescriptiveStats(
            metric=metric, pipeline=pipeline, n=n,
            mean=round(mean, 4), median=round(median, 4), std=round(std, 4),
            ci95_lower=round(mean - t_crit * se, 4),
            ci95_upper=round(mean + t_crit * se, 4),
            min=round(float(np.min(arr)), 4),
            max=round(float(np.max(arr)), 4),
        )

    # ------------------------------------------------------------------
    # Significance testing (Wilcoxon signed-rank, paired)
    # ------------------------------------------------------------------

    def significance_test(
        self,
        metric: str,
        baseline_scores: List[float],
        ragguard_scores: List[float],
    ) -> SignificanceResult:
        b = np.array([v for v in baseline_scores if v is not None and not math.isnan(v)])
        r = np.array([v for v in ragguard_scores if v is not None and not math.isnan(v)])

        # Align lengths (use intersection of valid indices)
        min_len = min(len(b), len(r))
        b, r = b[:min_len], r[:min_len]

        b_mean = float(np.mean(b)) if len(b) else 0.0
        r_mean = float(np.mean(r)) if len(r) else 0.0
        delta = round(r_mean - b_mean, 4)

        if len(b) < 5:
            return SignificanceResult(
                metric=metric, baseline_mean=round(b_mean, 4),
                ragguard_mean=round(r_mean, 4), delta=delta,
                p_value=1.0, statistic=0.0, test="insufficient_data",
                significant=False,
                effect_direction="neutral",
            )

        try:
            stat, p = stats.wilcoxon(r, b, alternative="two-sided", zero_method="wilcox")
            test_name = "wilcoxon"
        except Exception:
            stat, p = stats.ttest_rel(r, b)
            test_name = "paired_ttest"

        direction = "improvement" if delta > 0.01 else ("degradation" if delta < -0.01 else "neutral")
        return SignificanceResult(
            metric=metric,
            baseline_mean=round(b_mean, 4),
            ragguard_mean=round(r_mean, 4),
            delta=delta,
            p_value=round(float(p), 6),
            statistic=round(float(stat), 4),
            test=test_name,
            significant=float(p) < 0.05,
            effect_direction=direction,
        )

    # ------------------------------------------------------------------
    # Correlation analysis
    # ------------------------------------------------------------------

    def correlation(
        self,
        x_values: List[float],
        y_values: List[float],
        x_name: str,
        y_name: str,
    ) -> CorrelationResult:
        pairs = [(x, y) for x, y in zip(x_values, y_values)
                 if x is not None and y is not None
                 and not math.isnan(x) and not math.isnan(y)]
        if len(pairs) < 3:
            return CorrelationResult(x_name, y_name, 0, 1, 0, 1, len(pairs))
        xs, ys = zip(*pairs)
        pr, pp = stats.pearsonr(xs, ys)
        sr, sp = stats.spearmanr(xs, ys)
        return CorrelationResult(
            x_name=x_name, y_name=y_name,
            pearson_r=round(float(pr), 4), pearson_p=round(float(pp), 6),
            spearman_r=round(float(sr), 4), spearman_p=round(float(sp), 6),
            n=len(pairs),
        )

    # ------------------------------------------------------------------
    # RRFE feature importance (Spearman correlation with TRRI)
    # ------------------------------------------------------------------

    def feature_importance(
        self,
        feature_scores: Dict[str, List[float]],
        trri_scores: List[float],
    ) -> Dict[str, CorrelationResult]:
        results = {}
        for feat_name, feat_vals in feature_scores.items():
            results[feat_name] = self.correlation(feat_vals, trri_scores, feat_name, "trri")
        # Sort by |spearman_r| descending
        return dict(sorted(results.items(), key=lambda kv: abs(kv[1].spearman_r), reverse=True))

    # ------------------------------------------------------------------
    # Failure analysis
    # ------------------------------------------------------------------

    def identify_failures(self, records: list) -> List[FailureRecord]:
        """
        records: list of dicts with keys matching PipelineResult + MetricResult fields.
        """
        failures = []
        for rec in records:
            sid = rec.get("sample_id", "")
            pipeline = rec.get("pipeline", "")
            dataset = rec.get("dataset_name", "")
            question = rec.get("question", "")

            if rec.get("error"):
                failures.append(FailureRecord(sid, pipeline, dataset, question,
                                               "generation_error", rec["error"]))
                continue

            if len(rec.get("retrieved_contexts", [])) == 0:
                failures.append(FailureRecord(sid, pipeline, dataset, question,
                                               "empty_retrieval", "0 chunks retrieved"))

            trri = rec.get("trri")
            if trri is not None and trri < 0.3:
                failures.append(FailureRecord(sid, pipeline, dataset, question,
                                               "low_trri", f"TRRI={trri:.3f}"))

            faith = rec.get("ragas_faithfulness") or rec.get("deepeval_faithfulness")
            if faith is not None and faith < 0.4:
                failures.append(FailureRecord(sid, pipeline, dataset, question,
                                               "low_faithfulness", f"faithfulness={faith:.3f}"))

            hall = rec.get("deepeval_hallucination")
            if hall is not None and hall > 0.6:
                failures.append(FailureRecord(sid, pipeline, dataset, question,
                                               "high_hallucination", f"hallucination={hall:.3f}"))

            cp = rec.get("ragas_context_precision") or rec.get("deepeval_contextual_precision")
            if cp is not None and cp < 0.4:
                failures.append(FailureRecord(sid, pipeline, dataset, question,
                                               "low_context_precision", f"context_precision={cp:.3f}"))

            ar = rec.get("ragas_answer_relevancy") or rec.get("deepeval_answer_relevancy")
            if ar is not None and ar < 0.4:
                failures.append(FailureRecord(sid, pipeline, dataset, question,
                                               "low_answer_relevancy", f"answer_relevancy={ar:.3f}"))

            # RRFE extractor fallback detection
            explanations = rec.get("rrfe_explanations") or {}
            for feat, expl in explanations.items():
                if isinstance(expl, dict) and expl.get("confidence", 1.0) == 0.0:
                    failures.append(FailureRecord(sid, pipeline, dataset, question,
                                                   "extractor_fallback",
                                                   f"{feat} confidence=0"))

        return failures

    def cluster_failures(self, failures: List[FailureRecord]) -> Dict[str, List[FailureRecord]]:
        clusters: Dict[str, List[FailureRecord]] = defaultdict(list)
        for f in failures:
            clusters[f.category].append(f)
        return dict(clusters)

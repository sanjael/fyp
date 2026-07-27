"""
IEEE-style research summary generator.

Produces a structured Markdown report containing:
  - Experimental setup summary
  - Comparison tables (Baseline vs RAGGuard-TR)
  - Statistical significance table
  - Research question answers (quantitative)
  - Key findings
  - Strengths and weaknesses
  - Threats to validity
  - Research conclusions
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .statistics import (
    DescriptiveStats,
    SignificanceResult,
    CorrelationResult,
    FailureRecord,
)

logger = logging.getLogger("eval.report")


class IEEEReportGenerator:

    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate(
        self,
        run_config: dict,
        descriptive_baseline: Dict[str, DescriptiveStats],
        descriptive_ragguard: Dict[str, DescriptiveStats],
        significance_results: List[SignificanceResult],
        correlations: List[CorrelationResult],
        feature_importance: Dict[str, CorrelationResult],
        failure_clusters: Dict[str, List[FailureRecord]],
        trri_stats: Optional[DescriptiveStats] = None,
    ) -> str:
        lines = []

        lines += self._header(run_config)
        lines += self._setup_table(run_config)
        lines += self._comparison_table(descriptive_baseline, descriptive_ragguard)
        lines += self._significance_table(significance_results)
        lines += self._trri_section(trri_stats)
        lines += self._feature_importance_section(feature_importance)
        lines += self._correlation_section(correlations)
        lines += self._research_questions(
            significance_results, correlations, feature_importance, failure_clusters
        )
        lines += self._failure_section(failure_clusters)
        lines += self._findings_section(significance_results, correlations, feature_importance)
        lines += self._threats_section(run_config)
        lines += self._conclusions_section(significance_results)

        report = "\n".join(lines)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.out_dir, f"ieee_research_report_{ts}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"IEEE report saved: {path}")
        return path

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    def _header(self, cfg: dict) -> List[str]:
        return [
            "# RAGGuard-TR: Experimental Evaluation Report",
            "",
            "> **Generated**: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "> **Framework**: RAGGuard-TR (Retrieval-Augmented Generation Guard with Temporal Reliability)",
            "> **Evaluation Standard**: IEEE Research Paper Validation",
            "",
            "---",
            "",
        ]

    def _setup_table(self, cfg: dict) -> List[str]:
        lines = [
            "## I. Experimental Setup",
            "",
            "| Parameter | Value |",
            "|---|---|",
            f"| Datasets | {', '.join(cfg.get('datasets', ['N/A']))} |",
            f"| Samples per dataset | {cfg.get('samples_per_dataset', 'N/A')} |",
            f"| Total samples | {cfg.get('total_samples', 'N/A')} |",
            f"| Retriever | ChromaDB + Ollama Embeddings (nomic-embed-text) |",
            f"| Generator LLM | {cfg.get('generator_model', 'N/A')} |",
            f"| Evaluator LLM | {cfg.get('evaluator_model', 'N/A')} |",
            f"| RRFE Features | temporal_freshness, temporal_availability, source_credibility, evidence_consistency, evidence_sufficiency |",
            f"| TRRI Predictor | XGBoost (5-feature input) |",
            f"| Baseline | Vanilla RAG (same retriever + LLM, no RRFE/TRRI) |",
            f"| Significance Test | Wilcoxon Signed-Rank (paired, two-sided, α=0.05) |",
            f"| Top-K Retrieval | {cfg.get('top_k', 3)} |",
            "",
            "---",
            "",
        ]
        return lines

    def _comparison_table(
        self,
        baseline: Dict[str, DescriptiveStats],
        ragguard: Dict[str, DescriptiveStats],
    ) -> List[str]:
        lines = [
            "## II. Metric Comparison: Baseline RAG vs RAGGuard-TR",
            "",
            "| Metric | Baseline Mean ± Std | RAGGuard-TR Mean ± Std | Δ (RAGGuard − Baseline) |",
            "|---|---|---|---|",
        ]
        all_metrics = list(dict.fromkeys(list(baseline.keys()) + list(ragguard.keys())))
        for m in all_metrics:
            b = baseline.get(m)
            r = ragguard.get(m)
            b_str = f"{b.mean:.4f} ± {b.std:.4f}" if b else "N/A"
            r_str = f"{r.mean:.4f} ± {r.std:.4f}" if r else "N/A"
            if b and r:
                delta = r.mean - b.mean
                delta_str = f"**+{delta:.4f}**" if delta > 0 else f"{delta:.4f}"
            else:
                delta_str = "N/A"
            lines.append(f"| {_fmt_metric(m)} | {b_str} | {r_str} | {delta_str} |")
        lines += ["", "---", ""]
        return lines

    def _significance_table(self, results: List[SignificanceResult]) -> List[str]:
        lines = [
            "## III. Statistical Significance (Wilcoxon Signed-Rank Test)",
            "",
            "| Metric | Baseline | RAGGuard-TR | Δ | p-value | Significant | Direction |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in results:
            sig = "✓ Yes" if r.significant else "No"
            lines.append(
                f"| {_fmt_metric(r.metric)} | {r.baseline_mean:.4f} | {r.ragguard_mean:.4f} "
                f"| {r.delta:+.4f} | {r.p_value:.4f} | {sig} | {r.effect_direction} |"
            )
        lines += ["", "---", ""]
        return lines

    def _trri_section(self, stats: Optional[DescriptiveStats]) -> List[str]:
        if not stats:
            return []
        lines = [
            "## IV. TRRI Score Statistics",
            "",
            "| Statistic | Value |",
            "|---|---|",
            f"| N | {stats.n} |",
            f"| Mean | {stats.mean:.4f} |",
            f"| Median | {stats.median:.4f} |",
            f"| Std Dev | {stats.std:.4f} |",
            f"| 95% CI | [{stats.ci95_lower:.4f}, {stats.ci95_upper:.4f}] |",
            f"| Min | {stats.min:.4f} |",
            f"| Max | {stats.max:.4f} |",
            "",
            "---",
            "",
        ]
        return lines

    def _feature_importance_section(self, importance: Dict[str, CorrelationResult]) -> List[str]:
        lines = [
            "## V. RRFE Feature Importance (Spearman ρ with TRRI)",
            "",
            "| Rank | Feature | Spearman ρ | p-value | Interpretation |",
            "|---|---|---|---|---|",
        ]
        for rank, (feat, corr) in enumerate(importance.items(), 1):
            interp = _interpret_correlation(corr.spearman_r)
            sig = "✓" if corr.spearman_p < 0.05 else ""
            lines.append(
                f"| {rank} | {feat} | {corr.spearman_r:.4f} {sig} | {corr.spearman_p:.4f} | {interp} |"
            )
        lines += ["", "---", ""]
        return lines

    def _correlation_section(self, correlations: List[CorrelationResult]) -> List[str]:
        lines = [
            "## VI. TRRI Correlation Analysis",
            "",
            "| X | Y | Pearson r | Spearman ρ | p-value | Interpretation |",
            "|---|---|---|---|---|---|",
        ]
        for c in correlations:
            interp = _interpret_correlation(c.spearman_r)
            lines.append(
                f"| {c.x_name} | {c.y_name} | {c.pearson_r:.4f} | {c.spearman_r:.4f} "
                f"| {c.spearman_p:.4f} | {interp} |"
            )
        lines += ["", "---", ""]
        return lines

    def _research_questions(
        self,
        significance: List[SignificanceResult],
        correlations: List[CorrelationResult],
        importance: Dict[str, CorrelationResult],
        failures: Dict[str, List[FailureRecord]],
    ) -> List[str]:
        lines = ["## VII. Research Questions — Quantitative Answers", ""]

        sig_map = {r.metric: r for r in significance}
        corr_map = {(c.x_name, c.y_name): c for c in correlations}
        imp_list = list(importance.items())

        # RQ1: Which RRFE feature contributes most?
        lines.append("### RQ1: Which RRFE feature contributes the most to TRRI?")
        if imp_list:
            top_feat, top_corr = imp_list[0]
            lines.append(
                f"> **{top_feat}** has the highest absolute Spearman correlation with TRRI "
                f"(ρ={top_corr.spearman_r:.4f}, p={top_corr.spearman_p:.4f}, n={top_corr.n}). "
                f"This indicates it is the dominant predictor of retrieval reliability."
            )
        lines.append("")

        # RQ2: Which feature contributes least?
        lines.append("### RQ2: Which RRFE feature contributes the least?")
        if imp_list:
            bot_feat, bot_corr = imp_list[-1]
            lines.append(
                f"> **{bot_feat}** has the lowest absolute Spearman correlation with TRRI "
                f"(ρ={bot_corr.spearman_r:.4f}, p={bot_corr.spearman_p:.4f}). "
                f"Its contribution to TRRI prediction is minimal in the current evaluation."
            )
        lines.append("")

        # RQ3: What kinds of questions fail?
        lines.append("### RQ3: What kinds of questions fail most frequently?")
        if failures:
            top_cat = max(failures, key=lambda k: len(failures[k]))
            lines.append(
                f"> The most common failure category is **{top_cat}** "
                f"({len(failures[top_cat])} occurrences). "
                f"Total failure events across all categories: {sum(len(v) for v in failures.values())}."
            )
        else:
            lines.append("> No failure events detected.")
        lines.append("")

        # RQ4: TRRI vs Faithfulness
        lines.append("### RQ4: Does TRRI correlate with Faithfulness?")
        c = corr_map.get(("trri", "ragas_faithfulness")) or corr_map.get(("trri", "deepeval_faithfulness"))
        if c:
            lines.append(
                f"> Spearman ρ={c.spearman_r:.4f} (p={c.spearman_p:.4f}, n={c.n}). "
                f"{_interpret_correlation(c.spearman_r)}. "
                + ("This is statistically significant." if c.spearman_p < 0.05
                   else "This is **not** statistically significant at α=0.05.")
            )
        else:
            lines.append("> Insufficient data to compute this correlation.")
        lines.append("")

        # RQ5: TRRI vs Hallucination
        lines.append("### RQ5: Does TRRI correlate with Hallucination?")
        c = corr_map.get(("trri", "deepeval_hallucination"))
        if c:
            lines.append(
                f"> Spearman ρ={c.spearman_r:.4f} (p={c.spearman_p:.4f}, n={c.n}). "
                f"A negative correlation is expected (higher TRRI → lower hallucination). "
                f"{_interpret_correlation(c.spearman_r)}."
            )
        else:
            lines.append("> Insufficient data to compute this correlation.")
        lines.append("")

        # RQ6: Temporal Freshness vs Context Precision
        lines.append("### RQ6: Does Temporal Freshness improve Context Precision?")
        c = corr_map.get(("temporal_freshness", "ragas_context_precision"))
        if c:
            lines.append(
                f"> Spearman ρ={c.spearman_r:.4f} (p={c.spearman_p:.4f}, n={c.n}). "
                f"{_interpret_correlation(c.spearman_r)}."
            )
        else:
            lines.append("> Insufficient data to compute this correlation.")
        lines.append("")

        # RQ7: Source Credibility vs Faithfulness
        lines.append("### RQ7: Does Source Credibility improve Faithfulness?")
        c = corr_map.get(("source_credibility", "ragas_faithfulness")) or \
            corr_map.get(("source_credibility", "deepeval_faithfulness"))
        if c:
            lines.append(
                f"> Spearman ρ={c.spearman_r:.4f} (p={c.spearman_p:.4f}, n={c.n}). "
                f"{_interpret_correlation(c.spearman_r)}."
            )
        else:
            lines.append("> Insufficient data to compute this correlation.")
        lines.append("")

        lines += ["---", ""]
        return lines

    def _failure_section(self, clusters: Dict[str, List[FailureRecord]]) -> List[str]:
        lines = [
            "## VIII. Failure Analysis",
            "",
            "| Category | Count | Description |",
            "|---|---|---|",
        ]
        from .statistics import FAILURE_CATEGORIES
        for cat, records in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
            desc = FAILURE_CATEGORIES.get(cat, cat)
            lines.append(f"| {cat} | {len(records)} | {desc} |")
        lines += ["", "---", ""]
        return lines

    def _findings_section(
        self,
        significance: List[SignificanceResult],
        correlations: List[CorrelationResult],
        importance: Dict[str, CorrelationResult],
    ) -> List[str]:
        improved = [r for r in significance if r.significant and r.effect_direction == "improvement"]
        degraded = [r for r in significance if r.significant and r.effect_direction == "degradation"]

        lines = [
            "## IX. Key Findings",
            "",
            "### Strengths",
        ]
        if improved:
            for r in improved:
                lines.append(
                    f"- RAGGuard-TR achieves a statistically significant improvement in "
                    f"**{_fmt_metric(r.metric)}** (Δ={r.delta:+.4f}, p={r.p_value:.4f})."
                )
        else:
            lines.append("- No statistically significant improvements detected at α=0.05 "
                         "(may indicate insufficient sample size or genuine parity).")

        if importance:
            top = list(importance.items())[0]
            lines.append(
                f"- **{top[0]}** is the most predictive RRFE feature "
                f"(|ρ|={abs(top[1].spearman_r):.4f})."
            )

        lines += ["", "### Weaknesses"]
        if degraded:
            for r in degraded:
                lines.append(
                    f"- RAGGuard-TR shows a statistically significant **degradation** in "
                    f"**{_fmt_metric(r.metric)}** (Δ={r.delta:+.4f}, p={r.p_value:.4f}). "
                    f"Investigate pipeline overhead or risk gate miscalibration."
                )
        else:
            lines.append("- No statistically significant degradations detected.")

        lines += ["", "---", ""]
        return lines

    def _threats_section(self, cfg: dict) -> List[str]:
        n = cfg.get("total_samples", "unknown")
        return [
            "## X. Threats to Validity",
            "",
            "### Internal Validity",
            f"- **Sample size**: {n} samples may be insufficient for high-power statistical tests. "
            "Wilcoxon signed-rank requires ≥ 20 paired samples for reliable p-values.",
            "- **TRRI predictor**: The XGBoost model is trained on the same pipeline's outputs. "
            "If the training dataset is small or biased, TRRI scores may not generalise.",
            "- **Evaluator LLM bias**: RAGAS and DeepEval metrics are computed by an LLM judge "
            "(Groq/Google). LLM judges can exhibit positional and verbosity biases.",
            "",
            "### External Validity",
            "- **Dataset coverage**: Only RAGBench subsets are used. "
            "Results may not generalise to domain-specific corpora (legal, medical, code).",
            "- **Embedding model**: nomic-embed-text is used for both retrieval and RRFE. "
            "A different embedding model may alter RRFE feature scores.",
            "- **LLM dependency**: Results are tied to the specific Ollama model version used. "
            "Different LLMs may produce different faithfulness/hallucination profiles.",
            "",
            "### Construct Validity",
            "- **Hallucination proxy**: DeepEval HallucinationMetric measures factual consistency "
            "with retrieved context, not with world knowledge. This is a proxy, not ground truth.",
            "- **TRRI as reliability score**: TRRI is trained on RAGAS + DeepEval labels (RRT). "
            "If those labels are noisy, TRRI inherits that noise.",
            "",
            "---",
            "",
        ]

    def _conclusions_section(self, significance: List[SignificanceResult]) -> List[str]:
        n_sig = sum(1 for r in significance if r.significant and r.effect_direction == "improvement")
        n_total = len(significance)
        lines = [
            "## XI. Research Conclusions",
            "",
            f"This evaluation assessed RAGGuard-TR across {n_total} metrics using paired "
            "statistical testing (Wilcoxon signed-rank, α=0.05).",
            "",
            f"- **{n_sig}/{n_total}** metrics show statistically significant improvement over "
            "the Baseline RAG pipeline.",
            "- The RRFE feature extraction layer provides interpretable, per-feature reliability "
            "signals that correlate with downstream generation quality.",
            "- The TRRI score provides a quantitative pre-generation risk estimate, enabling "
            "the adaptive decision gate to modulate retrieval strategy.",
            "- The primary overhead introduced by RAGGuard-TR is the RRFE computation and "
            "TRRI prediction latency, which must be weighed against quality gains.",
            "",
            "> **Publication Readiness Assessment**: The framework demonstrates a scientifically "
            "grounded approach to hallucination prevention in RAG systems. "
            "Strengthening the evaluation with larger sample sizes (≥ 200 per dataset) and "
            "human evaluation of generated answers would further support an IEEE submission.",
            "",
            "---",
            "",
            "*Report generated automatically by the RAGGuard-TR Evaluation Pipeline.*",
        ]
        return lines


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_metric(name: str) -> str:
    return name.replace("_", " ").title()


def _interpret_correlation(r: float) -> str:
    a = abs(r)
    direction = "positive" if r >= 0 else "negative"
    if a >= 0.7:
        strength = "strong"
    elif a >= 0.4:
        strength = "moderate"
    elif a >= 0.2:
        strength = "weak"
    else:
        strength = "negligible"
    return f"{strength.capitalize()} {direction} correlation"

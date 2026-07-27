"""
IEEE-ready visualization module.

All figures use a clean, publication-quality style:
  - No chart junk
  - Consistent color palette (colorblind-safe)
  - Saved as both PDF (vector, for LaTeX) and PNG (300 dpi, for Word/slides)

Figures produced:
  1. metric_comparison_bar       — Baseline vs RAGGuard-TR per metric
  2. trri_distribution           — KDE + histogram of TRRI scores
  3. feature_distribution        — Box plots of all 5 RRFE features
  4. hallucination_reduction     — Paired bar: hallucination baseline vs RAGGuard-TR
  5. context_precision_comparison — Grouped bar per dataset
  6. faithfulness_comparison     — Grouped bar per dataset
  7. latency_comparison          — Grouped bar: pipeline stage latencies
  8. feature_importance          — Horizontal bar: Spearman |r| with TRRI
  9. risk_distribution           — Pie/bar: low/medium/high risk counts
 10. trri_vs_faithfulness_scatter — Scatter with regression line
 11. trri_vs_hallucination_scatter — Scatter with regression line
 12. failure_category_bar        — Failure counts by category
"""
import os
import logging
from typing import Dict, List, Optional

import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — safe for server environments
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MaxNLocator

logger = logging.getLogger("eval.viz")

# ---------------------------------------------------------------------------
# IEEE style constants
# ---------------------------------------------------------------------------
_PALETTE = {
    "baseline":   "#4878CF",   # blue
    "ragguard":   "#D65F5F",   # red
    "accent":     "#6ACC65",   # green
    "neutral":    "#B47CC7",   # purple
    "grid":       "#E0E0E0",
}
_FEATURE_COLORS = ["#4878CF", "#D65F5F", "#6ACC65", "#B47CC7", "#E8A838"]
_FIG_W, _FIG_H = 7.0, 4.5   # IEEE double-column figure size (inches)
_DPI = 300


def _apply_ieee_style(ax, title: str = "", xlabel: str = "", ylabel: str = "") -> None:
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.tick_params(labelsize=8)
    ax.yaxis.grid(True, color=_PALETTE["grid"], linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _safe_fig_path(out_dir: str, name: str, ext: str) -> str:
    """Resolve figure path and assert it stays within out_dir."""
    safe_name = os.path.basename(name).replace("..", "")
    resolved = os.path.realpath(os.path.join(out_dir, f"{safe_name}.{ext}"))
    if not resolved.startswith(os.path.realpath(out_dir)):
        raise ValueError(f"Path traversal detected: {name}")
    return resolved


def _save(fig, out_dir: str, name: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for ext in ("pdf", "png"):
        path = _safe_fig_path(out_dir, name, ext)
        fig.savefig(path, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Saved figure: {name}")


# ---------------------------------------------------------------------------
# 1. Metric comparison bar chart
# ---------------------------------------------------------------------------

def plot_metric_comparison(
    baseline_means: Dict[str, float],
    ragguard_means: Dict[str, float],
    significance: Dict[str, bool],   # metric -> is_significant
    out_dir: str,
) -> None:
    metrics = [m for m in baseline_means if m in ragguard_means]
    if not metrics:
        return
    x = np.arange(len(metrics))
    w = 0.35
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    b1 = ax.bar(x - w / 2, [baseline_means[m] for m in metrics], w,
                label="Baseline RAG", color=_PALETTE["baseline"], zorder=3)
    b2 = ax.bar(x + w / 2, [ragguard_means[m] for m in metrics], w,
                label="RAGGuard-TR", color=_PALETTE["ragguard"], zorder=3)
    # Significance stars
    for i, m in enumerate(metrics):
        if significance.get(m):
            ymax = max(baseline_means[m], ragguard_means[m])
            ax.text(x[i], ymax + 0.02, "*", ha="center", va="bottom", fontsize=12, color="black")
    ax.set_xticks(x)
    ax.set_xticklabels([_short(m) for m in metrics], rotation=30, ha="right", fontsize=8)
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=8, framealpha=0.9)
    _apply_ieee_style(ax, "Metric Comparison: Baseline RAG vs RAGGuard-TR",
                      "Metric", "Score (0–1)")
    ax.text(0.99, 0.97, "* p < 0.05", transform=ax.transAxes,
            ha="right", va="top", fontsize=7, color="gray")
    _save(fig, out_dir, "01_metric_comparison")


# ---------------------------------------------------------------------------
# 2. TRRI distribution
# ---------------------------------------------------------------------------

def plot_trri_distribution(trri_scores: List[float], out_dir: str) -> None:
    if not trri_scores:
        return
    arr = np.array([v for v in trri_scores if v is not None])
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    ax.hist(arr, bins=20, color=_PALETTE["ragguard"], edgecolor="white",
            alpha=0.85, zorder=3, density=True, label="TRRI density")
    # KDE overlay
    try:
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(arr)
        xs = np.linspace(0, 1, 200)
        ax.plot(xs, kde(xs), color="black", linewidth=1.5, label="KDE")
    except Exception as e:
        logger.debug(f"KDE overlay skipped: {e}")
    ax.axvline(float(np.mean(arr)), color=_PALETTE["baseline"], linestyle="--",
               linewidth=1.2, label=f"Mean={np.mean(arr):.3f}")
    ax.set_xlim(0, 1)
    ax.legend(fontsize=8)
    _apply_ieee_style(ax, "TRRI Score Distribution", "TRRI Score", "Density")
    _save(fig, out_dir, "02_trri_distribution")


# ---------------------------------------------------------------------------
# 3. RRFE feature distribution (box plots)
# ---------------------------------------------------------------------------

def plot_feature_distribution(
    feature_data: Dict[str, List[float]],   # feature_name -> list of scores
    out_dir: str,
) -> None:
    if not feature_data:
        return
    names = list(feature_data.keys())
    data = [np.array([v for v in feature_data[n] if v is not None]) for n in names]
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    bp = ax.boxplot(data, patch_artist=True, notch=False,
                    medianprops=dict(color="black", linewidth=1.5))
    for patch, color in zip(bp["boxes"], _FEATURE_COLORS):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    ax.set_xticks(range(1, len(names) + 1))
    ax.set_xticklabels([_short(n) for n in names], rotation=20, ha="right", fontsize=8)
    ax.set_ylim(-0.05, 1.05)
    _apply_ieee_style(ax, "RRFE Feature Score Distributions", "Feature", "Score (0–1)")
    _save(fig, out_dir, "03_feature_distribution")


# ---------------------------------------------------------------------------
# 4. Hallucination reduction
# ---------------------------------------------------------------------------

def plot_hallucination_reduction(
    baseline_hall: List[float],
    ragguard_hall: List[float],
    out_dir: str,
) -> None:
    b = [v for v in baseline_hall if v is not None]
    r = [v for v in ragguard_hall if v is not None]
    if not b or not r:
        return
    fig, ax = plt.subplots(figsize=(5, _FIG_H))
    means = [np.mean(b), np.mean(r)]
    stds  = [np.std(b, ddof=1) if len(b) > 1 else 0,
             np.std(r, ddof=1) if len(r) > 1 else 0]
    bars = ax.bar(["Baseline RAG", "RAGGuard-TR"], means,
                  color=[_PALETTE["baseline"], _PALETTE["ragguard"]],
                  yerr=stds, capsize=5, zorder=3, width=0.5)
    ax.set_ylim(0, 1.1)
    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, mean + 0.03,
                f"{mean:.3f}", ha="center", va="bottom", fontsize=9)
    _apply_ieee_style(ax, "Hallucination Score Comparison", "Pipeline", "Hallucination Score")
    _save(fig, out_dir, "04_hallucination_reduction")


# ---------------------------------------------------------------------------
# 5 & 6. Per-dataset grouped bar (context precision / faithfulness)
# ---------------------------------------------------------------------------

def plot_per_dataset_metric(
    metric_name: str,
    baseline_by_dataset: Dict[str, float],
    ragguard_by_dataset: Dict[str, float],
    out_dir: str,
    fig_id: str,
) -> None:
    datasets = list(baseline_by_dataset.keys())
    if not datasets:
        return
    x = np.arange(len(datasets))
    w = 0.35
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    ax.bar(x - w / 2, [baseline_by_dataset[d] for d in datasets], w,
           label="Baseline RAG", color=_PALETTE["baseline"], zorder=3)
    ax.bar(x + w / 2, [ragguard_by_dataset[d] for d in datasets], w,
           label="RAGGuard-TR", color=_PALETTE["ragguard"], zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(datasets, rotation=15, ha="right", fontsize=8)
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=8)
    _apply_ieee_style(ax, f"{_short(metric_name)} by Dataset", "Dataset", "Score (0–1)")
    _save(fig, out_dir, fig_id)


# ---------------------------------------------------------------------------
# 7. Latency comparison
# ---------------------------------------------------------------------------

def plot_latency_comparison(
    baseline_latencies: Dict[str, List[float]],   # stage -> list of ms values
    ragguard_latencies: Dict[str, List[float]],
    out_dir: str,
) -> None:
    stages = list(ragguard_latencies.keys())
    if not stages:
        return
    b_means = [np.mean([v for v in baseline_latencies.get(s, [0]) if v]) for s in stages]
    r_means = [np.mean([v for v in ragguard_latencies.get(s, [0]) if v]) for s in stages]
    x = np.arange(len(stages))
    w = 0.35
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    ax.bar(x - w / 2, b_means, w, label="Baseline RAG", color=_PALETTE["baseline"], zorder=3)
    ax.bar(x + w / 2, r_means, w, label="RAGGuard-TR", color=_PALETTE["ragguard"], zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(stages, rotation=20, ha="right", fontsize=8)
    ax.legend(fontsize=8)
    _apply_ieee_style(ax, "Pipeline Stage Latency Comparison", "Stage", "Latency (ms)")
    _save(fig, out_dir, "07_latency_comparison")


# ---------------------------------------------------------------------------
# 8. Feature importance (Spearman |r| with TRRI)
# ---------------------------------------------------------------------------

def plot_feature_importance(
    importance: Dict[str, float],   # feature_name -> |spearman_r|
    out_dir: str,
) -> None:
    if not importance:
        return
    names = list(importance.keys())
    vals  = [importance[n] for n in names]
    # Sort ascending for horizontal bar
    sorted_pairs = sorted(zip(names, vals), key=lambda kv: kv[1])
    names, vals = zip(*sorted_pairs)
    fig, ax = plt.subplots(figsize=(_FIG_W, 3.5))
    colors = [_FEATURE_COLORS[i % len(_FEATURE_COLORS)] for i in range(len(names))]
    ax.barh(names, vals, color=colors, zorder=3)
    ax.set_xlim(0, 1.0)
    for i, v in enumerate(vals):
        ax.text(v + 0.01, i, f"{v:.3f}", va="center", fontsize=8)
    _apply_ieee_style(ax, "RRFE Feature Importance (|Spearman ρ| with TRRI)",
                      "|Spearman ρ|", "Feature")
    _save(fig, out_dir, "08_feature_importance")


# ---------------------------------------------------------------------------
# 9. Risk distribution
# ---------------------------------------------------------------------------

def plot_risk_distribution(risk_counts: Dict[str, int], out_dir: str) -> None:
    if not risk_counts:
        return
    labels = list(risk_counts.keys())
    sizes  = [risk_counts[l] for l in labels]
    colors = {"low": _PALETTE["accent"], "medium": "#E8A838", "high": _PALETTE["ragguard"]}
    fig, ax = plt.subplots(figsize=(5, 4))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        colors=[colors.get(l, _PALETTE["neutral"]) for l in labels],
        startangle=90,
        wedgeprops=dict(edgecolor="white", linewidth=1.5),
    )
    for t in autotexts:
        t.set_fontsize(9)
    ax.set_title("TRRI Risk Level Distribution", fontsize=11, fontweight="bold")
    _save(fig, out_dir, "09_risk_distribution")


# ---------------------------------------------------------------------------
# 10 & 11. Scatter plots: TRRI vs metric
# ---------------------------------------------------------------------------

def plot_scatter_trri_vs_metric(
    trri_scores: List[float],
    metric_scores: List[float],
    metric_name: str,
    correlation_r: float,
    correlation_p: float,
    out_dir: str,
    fig_id: str,
) -> None:
    pairs = [(t, m) for t, m in zip(trri_scores, metric_scores)
             if t is not None and m is not None]
    if len(pairs) < 3:
        return
    xs, ys = zip(*pairs)
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    ax.scatter(xs, ys, alpha=0.55, s=25, color=_PALETTE["ragguard"], zorder=3)
    # Regression line
    m_coef, b_coef = np.polyfit(xs, ys, 1)
    x_line = np.linspace(min(xs), max(xs), 100)
    ax.plot(x_line, m_coef * x_line + b_coef, color="black", linewidth=1.2, linestyle="--")
    ax.text(0.05, 0.92,
            f"Spearman ρ={correlation_r:.3f}, p={correlation_p:.4f}",
            transform=ax.transAxes, fontsize=8, color="black",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    _apply_ieee_style(ax, f"TRRI vs {_short(metric_name)}", "TRRI Score", _short(metric_name))
    _save(fig, out_dir, fig_id)


# ---------------------------------------------------------------------------
# 12. Failure category bar
# ---------------------------------------------------------------------------

def plot_failure_categories(
    failure_counts: Dict[str, int],
    out_dir: str,
) -> None:
    if not failure_counts:
        return
    cats = list(failure_counts.keys())
    counts = [failure_counts[c] for c in cats]
    sorted_pairs = sorted(zip(cats, counts), key=lambda kv: kv[1], reverse=True)
    cats, counts = zip(*sorted_pairs)
    fig, ax = plt.subplots(figsize=(_FIG_W, 4.0))
    ax.bar(range(len(cats)), counts, color=_PALETTE["ragguard"], zorder=3)
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels(cats, rotation=30, ha="right", fontsize=8)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    _apply_ieee_style(ax, "Failure Analysis by Category", "Failure Category", "Count")
    _save(fig, out_dir, "12_failure_categories")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _short(name: str) -> str:
    """Convert snake_case metric name to a short display label."""
    return name.replace("ragas_", "").replace("deepeval_", "").replace("_", " ").title()

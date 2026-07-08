"""Risk/return metrics and statistical tests on rolling-window results."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def sharpe_sortino(equity: pd.Series, rf_annual: float = 0.02) -> tuple[float, float]:
    """Annualized Sharpe/Sortino from a daily equity curve (log returns, 252 trading days)."""
    log_r = np.log(equity / equity.shift(1)).dropna()
    if len(log_r) < 5:
        return float("nan"), float("nan")

    excess = log_r - rf_annual / 252
    vol = excess.std(ddof=1)
    sharpe = excess.mean() / vol * np.sqrt(252) if vol > 0 else float("nan")

    downside = excess[excess < 0]
    down_std = downside.std(ddof=1) if len(downside) > 1 else float("nan")
    sortino = excess.mean() / down_std * np.sqrt(252) if down_std and down_std > 0 else float("nan")
    return sharpe, sortino


METRIC_COLUMNS = [
    ("HPR (%)", "lsi_hpr", "dca_hpr", 100),
    ("CAGR (%)", "lsi_cagr", "dca_cagr", 100),
    ("Sharpe", "lsi_sharpe", "dca_sharpe", 1),
    ("Sortino", "lsi_sortino", "dca_sortino", 1),
    ("Final wealth", "lsi_w_final", "dca_w_final", 1),
]


def summary_statistics(results: pd.DataFrame) -> pd.DataFrame:
    """Descriptive stats (mean/std/median/...) per metric, LSI vs DCA."""
    rows = []
    for label, lsi_col, dca_col, scale in METRIC_COLUMNS:
        lsi, dca = results[lsi_col].dropna() * scale, results[dca_col].dropna() * scale
        rows.append({
            "metric": label,
            "lsi_mean": lsi.mean(), "lsi_std": lsi.std(), "lsi_median": lsi.median(),
            "dca_mean": dca.mean(), "dca_std": dca.std(), "dca_median": dca.median(),
            "mean_gap": lsi.mean() - dca.mean(),
        })
    return pd.DataFrame(rows).set_index("metric")


def statistical_tests(results: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Paired tests on HPR (LSI vs DCA share the same market path per window,
    so the paired design cancels common cross-sectional variance)."""
    paired = results[["lsi_hpr", "dca_hpr"]].dropna()
    diff = paired["lsi_hpr"] - paired["dca_hpr"]
    rows = []

    stat, p = stats.mannwhitneyu(paired["lsi_hpr"], paired["dca_hpr"], alternative="two-sided")
    _, p_greater = stats.mannwhitneyu(paired["lsi_hpr"], paired["dca_hpr"], alternative="greater")
    rows.append({
        "test": "Mann-Whitney U", "statistic": stat, "p_value": p,
        "significant": p < alpha,
        "conclusion": ("LSI > DCA" if p_greater < alpha else "DCA > LSI") if p < alpha else "no significant difference",
    })

    if len(diff) >= 10 and not np.all(diff == 0):
        stat, p = stats.wilcoxon(diff, alternative="two-sided")
        median = diff.median()
        rows.append({
            "test": "Wilcoxon signed-rank (paired)", "statistic": stat, "p_value": p,
            "significant": p < alpha,
            "conclusion": (f"LSI > DCA (median Δ={median*100:+.2f}%)" if median > 0
                           else f"DCA > LSI (median Δ={median*100:+.2f}%)") if p < alpha else "no significant difference",
        })

    return pd.DataFrame(rows).set_index("test")


def regime_breakdown(results: pd.DataFrame) -> pd.DataFrame:
    """LSI vs DCA outcomes split by entry-market tertile (low/mid/high)."""
    df = results.copy()
    df["regime"] = pd.qcut(df["entry_level"], q=3, labels=["Low entry", "Mid entry", "High entry"])
    rows = []
    for regime, group in df.groupby("regime", observed=True):
        rows.append({
            "regime": regime, "n_windows": len(group),
            "lsi_hpr_mean": group["lsi_hpr"].mean() * 100,
            "dca_hpr_mean": group["dca_hpr"].mean() * 100,
            "median_gap": (group["lsi_hpr"] - group["dca_hpr"]).median() * 100,
            "lsi_win_rate": (group["hpr_diff"] > 0).mean() * 100,
        })
    return pd.DataFrame(rows).set_index("regime")

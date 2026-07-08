"""A small, curated set of charts for comparing LSI and DCA.

Five charts, each answering one question:
  equity_curves        -> what does the wealth path look like for one window?
  hpr_distribution      -> how spread out are outcomes across all windows?
  hpr_gap_timeline       -> does LSI's edge depend on when you start investing?
  win_rate_by_regime     -> does DCA do better in a specific market regime?
  risk_return            -> return vs risk trade-off, at a glance.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

CLR_LSI, CLR_DCA, CLR_DIFF = "#E63946", "#457B9D", "#2A9D8F"
STYLE = "seaborn-v0_8-whitegrid"


def equity_curves(lsi_curve: pd.Series, dca_curve: pd.Series, *, title: str = "") -> plt.Figure:
    """Overlay LSI vs DCA wealth path for a single window."""
    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.plot(lsi_curve.index, lsi_curve.values, color=CLR_LSI, lw=1.8, label="Lump-Sum")
        ax.plot(dca_curve.index, dca_curve.values, color=CLR_DCA, lw=1.8, label="DCA")
        ax.set_title(title or "Portfolio value over time")
        ax.set_ylabel("Portfolio value")
        ax.legend(frameon=False)
        fig.tight_layout()
    return fig


def hpr_distribution(results: pd.DataFrame, *, ticker: str = "") -> plt.Figure:
    """Distribution of Holding-Period Return across all rolling windows."""
    long = pd.concat([
        results[["lsi_hpr"]].rename(columns={"lsi_hpr": "hpr"}).assign(strategy="Lump-Sum"),
        results[["dca_hpr"]].rename(columns={"dca_hpr": "hpr"}).assign(strategy="DCA"),
    ])
    long["hpr"] *= 100
    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.violinplot(data=long, x="strategy", y="hpr", hue="strategy",
                        palette={"Lump-Sum": CLR_LSI, "DCA": CLR_DCA}, legend=False, ax=ax)
        ax.set_title(f"HPR distribution across rolling windows — {ticker}".strip(" —"))
        ax.set_ylabel("Holding-period return (%)")
        ax.set_xlabel("")
        fig.tight_layout()
    return fig


def hpr_gap_timeline(results: pd.DataFrame, *, ticker: str = "") -> plt.Figure:
    """LSI - DCA gap in HPR against the window's entry date."""
    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(9, 5))
        gap = results["hpr_diff"] * 100
        colors = [CLR_LSI if v > 0 else CLR_DCA for v in gap]
        ax.bar(results["t0"], gap, color=colors, width=20)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(f"LSI − DCA return gap by entry date — {ticker}".strip(" —"))
        ax.set_ylabel("HPR gap (percentage points)")
        fig.tight_layout()
    return fig


def win_rate_by_regime(regimes: pd.DataFrame, *, ticker: str = "") -> plt.Figure:
    """LSI win rate split by entry-market tertile (low / mid / high)."""
    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.bar(regimes.index.astype(str), regimes["lsi_win_rate"], color=CLR_DIFF)
        ax.axhline(50, color="black", lw=0.8, ls="--")
        ax.set_ylim(0, 100)
        ax.set_ylabel("LSI win rate (%)")
        ax.set_title(f"LSI win rate by entry regime — {ticker}".strip(" —"))
        fig.tight_layout()
    return fig


def risk_return(results: pd.DataFrame, *, ticker: str = "") -> plt.Figure:
    """Mean Sharpe vs mean HPR — LSI vs DCA, one point each."""
    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(6, 6))
        for label, hpr_col, sharpe_col, color in [
            ("Lump-Sum", "lsi_hpr", "lsi_sharpe", CLR_LSI),
            ("DCA", "dca_hpr", "dca_sharpe", CLR_DCA),
        ]:
            ax.scatter(results[sharpe_col].mean(), results[hpr_col].mean() * 100,
                       s=160, color=color, label=label, zorder=3)
        ax.set_xlabel("Mean Sharpe ratio")
        ax.set_ylabel("Mean HPR (%)")
        ax.set_title(f"Risk vs return — {ticker}".strip(" —"))
        ax.legend(frameon=False)
        fig.tight_layout()
    return fig

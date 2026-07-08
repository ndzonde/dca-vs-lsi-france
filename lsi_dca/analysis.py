"""Rolling-window orchestration.

Every number this module computes is kept in the returned DataFrames — the
console only ever shows a curated view of it. Set the "lsi_dca" logger to
DEBUG to see a line per window; INFO (default) shows one line per run.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta

import pandas as pd

from . import metrics as metrics_mod
from .engine import simulate_dca, simulate_lsi
from .metrics import regime_breakdown, sharpe_sortino, statistical_tests, summary_statistics

logger = logging.getLogger("lsi_dca")


def run_rolling_windows(
    ticker: str, w0: float, t0: str, *, window_years: int, shift_months: int,
    n_windows: int, dca_freq: str = "M", rf_annual: float = 0.02,
    cash_rf_annual: float | None = None,
) -> pd.DataFrame:
    """Simulate LSI vs DCA over `n_windows` overlapping windows.

    Each window i spans [t0 + i*shift_months, t0 + i*shift_months + window_years].
    Returns one row per window: HPR/CAGR/Sharpe/Sortino for both strategies,
    plus the entry price level used for regime tagging downstream.
    """
    t0_base = pd.Timestamp(t0)
    records = []
    started = time.perf_counter()

    for i in range(n_windows):
        w_t0 = t0_base + relativedelta(months=i * shift_months)
        w_tf = w_t0 + relativedelta(years=window_years)
        try:
            lsi = simulate_lsi(ticker, w0, w_t0, w_tf)
            dca = simulate_dca(ticker, w0, w_t0, w_tf, freq=dca_freq, cash_rf_annual=cash_rf_annual)
        except Exception as exc:  # noqa: BLE001 — a bad window shouldn't kill the whole sweep
            logger.debug("Window %d/%d skipped (%s): %s", i + 1, n_windows, ticker, exc)
            continue

        lsi_sharpe, lsi_sortino = sharpe_sortino(lsi.equity_curve, rf_annual)
        dca_sharpe, dca_sortino = sharpe_sortino(dca.equity_curve, rf_annual)
        records.append({
            "window": i + 1, "t0": lsi.t0, "tf": lsi.tf, "entry_level": lsi.equity_curve.iloc[0],
            "lsi_hpr": lsi.hpr, "lsi_cagr": lsi.cagr, "lsi_sharpe": lsi_sharpe, "lsi_sortino": lsi_sortino,
            "lsi_w_final": lsi.w_final,
            "dca_hpr": dca.hpr, "dca_cagr": dca.cagr, "dca_sharpe": dca_sharpe, "dca_sortino": dca_sortino,
            "dca_w_final": dca.w_final,
            "hpr_diff": lsi.hpr - dca.hpr,
        })
        logger.debug(
            "[%s] window %d/%d %s->%s | LSI HPR=%.1f%% DCA HPR=%.1f%%",
            ticker, i + 1, n_windows, w_t0.date(), w_tf.date(), lsi.hpr * 100, dca.hpr * 100,
        )

    if not records:
        raise RuntimeError(f"No window could be simulated for {ticker} — check parameters.")

    elapsed = time.perf_counter() - started
    logger.info("%-10s | %d/%d windows | DCA %s | %.1fs", ticker, len(records), n_windows, dca_freq, elapsed)
    return pd.DataFrame(records)


@dataclass
class BacktestReport:
    ticker: str
    results: pd.DataFrame
    summary: pd.DataFrame
    tests: pd.DataFrame
    regimes: pd.DataFrame

    @property
    def lsi_win_rate(self) -> float:
        return (self.results["hpr_diff"] > 0).mean() * 100


def compare(
    ticker: str, w0: float, t0: str, *, window_years: int = 5, shift_months: int = 1,
    n_windows: int = 60, dca_freq: str = "M", rf_annual: float = 0.02,
    cash_rf_annual: float | None = None, alpha: float = 0.05,
) -> BacktestReport:
    """Full LSI-vs-DCA comparison for one ticker/frequency: rolling windows +
    descriptive stats + paired significance tests + regime breakdown."""
    results = run_rolling_windows(
        ticker, w0, t0, window_years=window_years, shift_months=shift_months,
        n_windows=n_windows, dca_freq=dca_freq, rf_annual=rf_annual, cash_rf_annual=cash_rf_annual,
    )
    return BacktestReport(
        ticker=ticker,
        results=results,
        summary=summary_statistics(results),
        tests=statistical_tests(results, alpha=alpha),
        regimes=regime_breakdown(results),
    )


def backtest_frequencies(
    ticker: str, w0: float = 12_000, t0: str = "2010-01-04", *,
    freqs: tuple[str, ...] = ("M", "S", "A"), **kwargs,
) -> pd.DataFrame:
    """Compare() at several DCA frequencies, stacked into one tidy table
    (mirrors the paper's Table 1 layout: metric x frequency)."""
    rows = []
    for freq in freqs:
        report = compare(ticker, w0, t0, dca_freq=freq, **kwargs)
        for label, lsi_col, dca_col, scale in metrics_mod.METRIC_COLUMNS:
            lsi = report.results[lsi_col].dropna() * scale
            dca = report.results[dca_col].dropna() * scale
            rows.append({
                "dca_frequency": freq, "metric": label,
                "lsi_mean": lsi.mean(), "lsi_std": lsi.std(),
                "dca_mean": dca.mean(), "dca_std": dca.std(),
                "mean_gap": lsi.mean() - dca.mean(),
                "lsi_win_rate_pct": (report.results[lsi_col] > report.results[dca_col]).mean() * 100,
            })
    return pd.DataFrame(rows).set_index(["dca_frequency", "metric"])

"""Lump-Sum and DCA simulation engines.

Each public entry point (`simulate_lsi`, `simulate_dca`) fetches prices then
delegates to a pure, network-free `_*_from_prices` function that operates on
an OHLC+Dividends DataFrame. The pure functions are what the unit tests
exercise on synthetic data.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import pandas as pd

from .data import fetch_price_history
from .rates import livret_a_rate

FREQ_AZ = {"D": "B", "W": "W-MON", "M": "MS", "Q": "BQS", "S": "6MS", "A": "BYS"}


@dataclass(frozen=True)
class SimulationResult:
    strategy: str
    ticker: str
    t0: pd.Timestamp
    tf: pd.Timestamp
    w0: float
    w_final: float
    shares_final: float
    equity_curve: pd.Series

    @property
    def years(self) -> float:
        return (self.tf - self.t0).days / 365.25

    @property
    def hpr(self) -> float:
        return self.w_final / self.w0 - 1

    @property
    def cagr(self) -> float:
        return (self.w_final / self.w0) ** (1 / self.years) - 1 if self.years > 0 else float("nan")


def _lsi_from_prices(df: pd.DataFrame, w0: float) -> tuple[pd.Series, float]:
    """Buy w0 at t0's open, reinvest every dividend at that day's close."""
    shares = w0 / df.iloc[0]["Open"]
    equity = []
    for _, row in df.iterrows():
        if row["Dividends"] > 0 and shares > 0:
            shares += shares * row["Dividends"] / row["Close"]
        equity.append(shares * row["Close"])
    return pd.Series(equity, index=df.index), shares


def _tranche_dates(index: pd.DatetimeIndex, t0: dt.datetime, tf: dt.datetime, freq: str) -> list[pd.Timestamp]:
    """Map theoretical calendar dates (per `freq`) onto the next available session."""
    theoretical = pd.date_range(start=t0, end=tf, freq=FREQ_AZ[freq.upper()])
    mapped = set()
    for d in theoretical:
        available = index[index >= d]
        if not available.empty:
            mapped.add(available[0])
    return sorted(mapped)


def _dca_from_prices(
    df: pd.DataFrame, w0: float, dates: list[pd.Timestamp], cash_rf_annual: float | None,
) -> tuple[pd.Series, float, float]:
    """Invest w0/N at each tranche date's open; idle cash earns `cash_rf_annual`
    (or the Livret A schedule if None), compounded on calendar days elapsed."""
    tranche = w0 / len(dates)
    shares, cash = 0.0, w0
    prev_date = df.index[0]
    equity = []
    for date, row in df.iterrows():
        elapsed = (date - prev_date).days
        if elapsed > 0 and cash > 0:
            rate = cash_rf_annual if cash_rf_annual is not None else livret_a_rate(date)
            cash *= (1 + rate) ** (elapsed / 365)
        prev_date = date

        if date in dates:
            shares += tranche / row["Open"]
            cash -= tranche

        if row["Dividends"] > 0 and shares > 0:
            shares += shares * row["Dividends"] / row["Close"]

        equity.append(shares * row["Close"] + max(cash, 0.0))
    return pd.Series(equity, index=df.index), shares, cash


def simulate_lsi(ticker: str, w0: float, t0: dt.datetime, tf: dt.datetime) -> SimulationResult:
    df = fetch_price_history(ticker, t0, tf)
    equity, shares = _lsi_from_prices(df, w0)
    return SimulationResult(
        strategy="LSI", ticker=ticker, t0=df.index[0], tf=df.index[-1],
        w0=w0, w_final=float(equity.iloc[-1]), shares_final=shares, equity_curve=equity,
    )


def simulate_dca(
    ticker: str, w0: float, t0: dt.datetime, tf: dt.datetime,
    freq: str = "M", cash_rf_annual: float | None = None,
) -> SimulationResult:
    if freq.upper() not in FREQ_AZ:
        raise ValueError(f"Invalid frequency. Choose one of {list(FREQ_AZ)}.")
    df = fetch_price_history(ticker, t0, tf)
    dates = _tranche_dates(df.index, t0, tf, freq)
    if not dates:
        raise ValueError("Empty DCA schedule — check t0/tf/freq.")
    equity, shares, _cash = _dca_from_prices(df, w0, dates, cash_rf_annual)
    return SimulationResult(
        strategy="DCA", ticker=ticker, t0=df.index[0], tf=df.index[-1],
        w0=w0, w_final=float(equity.iloc[-1]), shares_final=shares, equity_curve=equity,
    )

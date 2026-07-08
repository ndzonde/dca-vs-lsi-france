"""Price history retrieval."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import yfinance as yf


def fetch_price_history(ticker: str, t0: dt.datetime, tf: dt.datetime) -> pd.DataFrame:
    """OHLC + Dividends for `ticker` over [t0, tf], raw (auto_adjust=False).

    auto_adjust=False is mandatory here: yfinance's default (True) already
    folds dividends into the price series, and the simulation engine
    reinvests dividends explicitly via DRIP — combining both double-counts
    every dividend. Splits need no separate handling: yfinance always
    split-adjusts OHLC regardless of auto_adjust.
    """
    df = yf.Ticker(ticker).history(start=t0, end=tf + dt.timedelta(days=5), auto_adjust=False)
    if df.empty:
        raise ValueError(f"No data for {ticker} between {t0.date()} and {tf.date()}.")
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    df = df.loc[t0:tf]
    if df.empty:
        raise ValueError(f"Empty segment for {ticker} between {t0.date()} and {tf.date()}.")
    return df

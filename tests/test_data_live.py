"""Network-dependent regression tests — guard against the dividend
double-counting bug resurfacing (see lsi_dca/data.py docstring)."""
import datetime as dt

import pytest

from lsi_dca.data import fetch_price_history
from lsi_dca.engine import simulate_dca, simulate_lsi

pytestmark = pytest.mark.network


def _fetch_reference(ticker: str, t0: dt.datetime, tf: dt.datetime, *, auto_adjust: bool):
    import yfinance as yf

    df = yf.Ticker(ticker).history(start=t0, end=tf + dt.timedelta(days=10), auto_adjust=auto_adjust)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    return df.loc[t0:tf]


def test_fetched_prices_are_not_dividend_adjusted():
    t0, tf = dt.datetime(2019, 1, 1), dt.datetime(2019, 12, 31)
    raw = fetch_price_history("AI.PA", t0, tf)
    adjusted = _fetch_reference("AI.PA", t0, tf, auto_adjust=True)

    assert (raw["Dividends"] > 0).sum() > 0, "expected at least one dividend in 2019"
    # If our fetch were still dividend-adjusted, this would be ~identical to `adjusted`.
    relative_gap = (raw["Close"] / adjusted["Close"] - 1).abs().max()
    assert relative_gap > 0.01, "raw and dividend-adjusted closes are suspiciously close"


def test_lsi_return_matches_independent_total_return_series():
    # Cross-check against yfinance's own auto-adjusted (total-return) series,
    # used here only as a ground truth, not as the engine's data source.
    ticker, w0 = "AI.PA", 12_000
    t0, tf = dt.datetime(2010, 1, 4), dt.datetime(2015, 1, 4)

    result = simulate_lsi(ticker, w0, t0, tf)

    adjusted = _fetch_reference(ticker, t0, tf, auto_adjust=True)
    independent_hpr = adjusted["Close"].iloc[-1] / adjusted["Open"].iloc[0] - 1

    assert result.hpr == pytest.approx(independent_hpr, abs=0.01)


def test_dca_final_wealth_is_finite_and_positive():
    result = simulate_dca("AI.PA", 12_000, dt.datetime(2010, 1, 4), dt.datetime(2015, 1, 4), freq="S")
    assert result.w_final > 0

"""Unit tests for the pure (network-free) simulation cores, on synthetic data."""
import pandas as pd
import pytest

from lsi_dca.engine import _dca_from_prices, _lsi_from_prices, _tranche_dates


def _flat_price_df(n_days: int = 10, price: float = 100.0, dividend_on: int | None = None,
                    dividend_amount: float = 0.0) -> pd.DataFrame:
    index = pd.bdate_range("2020-01-02", periods=n_days)
    dividends = [0.0] * n_days
    if dividend_on is not None:
        dividends[dividend_on] = dividend_amount
    return pd.DataFrame({"Open": price, "Close": price, "Dividends": dividends}, index=index)


def test_lsi_flat_price_no_dividend_has_zero_return():
    df = _flat_price_df()
    equity, shares = _lsi_from_prices(df, w0=10_000)
    assert shares == pytest.approx(100.0)  # 10_000 / 100
    assert equity.iloc[-1] == pytest.approx(10_000.0)


def test_lsi_single_dividend_matches_hand_calculation():
    # price flat at 100, a single $2 dividend on day 5 -> exactly a 2% DRIP bump
    df = _flat_price_df(dividend_on=5, dividend_amount=2.0)
    equity, shares = _lsi_from_prices(df, w0=10_000)
    assert equity.iloc[-1] == pytest.approx(10_000 * 1.02)
    # the bump must land exactly on the dividend date, not before
    assert equity.iloc[4] == pytest.approx(10_000.0)
    assert equity.iloc[5] == pytest.approx(10_000 * 1.02)


def test_dca_invests_exactly_w0_with_no_growth_and_zero_cash_yield():
    df = _flat_price_df(n_days=20)
    dates = list(df.index[[2, 8, 14]])  # 3 equal tranches
    equity, shares, cash = _dca_from_prices(df, w0=9_000, dates=dates, cash_rf_annual=0.0)
    assert equity.iloc[-1] == pytest.approx(9_000.0)
    assert cash == pytest.approx(0.0, abs=1e-6)


def test_dca_idle_cash_compounds_at_the_given_annual_rate():
    # single tranche on the very last day -> all cash sits idle for the whole window
    df = _flat_price_df(n_days=366)  # ~1 calendar year of business days
    last_date = df.index[-1]
    equity, shares, cash = _dca_from_prices(df, w0=10_000, dates=[last_date], cash_rf_annual=0.05)
    elapsed_days = (last_date - df.index[0]).days
    expected_cash_before_tranche = 10_000 * (1.05) ** (elapsed_days / 365)
    # cash is spent on the tranche the same day it's credited, so equity == that pre-tranche value
    assert equity.iloc[-1] == pytest.approx(expected_cash_before_tranche, rel=1e-6)


def test_tranche_dates_align_to_next_available_session():
    df = _flat_price_df(n_days=40)
    dates = _tranche_dates(df.index, df.index[0], df.index[-1], freq="W")
    assert len(dates) > 0
    assert all(d in df.index for d in dates)
    assert dates == sorted(dates)

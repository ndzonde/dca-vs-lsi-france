import numpy as np
import pandas as pd
import pytest

from lsi_dca.metrics import sharpe_sortino


def _equity_from_log_returns(log_returns: list[float], start: float = 100.0) -> pd.Series:
    index = pd.bdate_range("2020-01-02", periods=len(log_returns) + 1)
    values = [start]
    for r in log_returns:
        values.append(values[-1] * np.exp(r))
    return pd.Series(values, index=index)


def test_sharpe_sortino_match_hand_computation():
    log_returns = [0.02, 0.01, -0.01, 0.03, -0.02, 0.01, 0.0, -0.01, 0.02, 0.01]
    equity = _equity_from_log_returns(log_returns)

    sharpe, sortino = sharpe_sortino(equity, rf_annual=0.0)

    r = np.array(log_returns)
    expected_sharpe = r.mean() / r.std(ddof=1) * np.sqrt(252)
    downside = r[r < 0]
    expected_sortino = r.mean() / downside.std(ddof=1) * np.sqrt(252)

    assert sharpe == pytest.approx(expected_sharpe)
    assert sortino == pytest.approx(expected_sortino)


def test_returns_nan_with_too_few_observations():
    equity = pd.Series([100, 101, 99], index=pd.bdate_range("2020-01-02", periods=3))
    sharpe, sortino = sharpe_sortino(equity)
    assert np.isnan(sharpe) and np.isnan(sortino)

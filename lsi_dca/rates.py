"""Risk-free rate for idle DCA cash: French Livret A historical schedule.

Livret A is the natural benchmark for a French retail investor's idle,
short-term, capital-guaranteed cash — not an interbank rate such as
EONIA/€STR, which retail investors cannot access.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# (effective_date, annual_rate) — official rate-change dates.
SCHEDULE: list[tuple[str, float]] = [
    ("2009-08-01", 0.0125),
    ("2010-08-01", 0.0175),
    ("2011-02-01", 0.0200),
    ("2011-08-01", 0.0225),
    ("2013-02-01", 0.0175),
    ("2013-08-01", 0.0125),
    ("2014-08-01", 0.0100),
    ("2015-08-01", 0.0075),
    ("2020-02-01", 0.0050),
    ("2022-02-01", 0.0100),
    ("2022-08-01", 0.0200),
    ("2023-02-01", 0.0300),
]
_DATES = pd.to_datetime([d for d, _ in SCHEDULE])
_RATES = np.array([r for _, r in SCHEDULE])


def livret_a_rate(date: pd.Timestamp | str) -> float:
    """Annual Livret A rate in effect on `date`.

    Outside the known range, the nearest bound is extended flat (all study
    windows fall within 2009-2024).
    """
    idx = _DATES.searchsorted(pd.Timestamp(date), side="right") - 1
    return float(_RATES[np.clip(idx, 0, len(_RATES) - 1)])

"""LSI vs DCA backtesting library.

    import lsi_dca
    lsi_dca.configure_logging()          # INFO: one line per run
    report = lsi_dca.compare("^FCHI", 12_000, "2010-01-04")
    report.summary                        # descriptive stats, LSI vs DCA
    report.tests                          # paired significance tests
    lsi_dca.plotting.hpr_distribution(report.results)

Every number computed by a run is kept in the returned objects regardless of
the logging level — logging only controls what prints to the console.
"""
from __future__ import annotations

import logging
import sys

from . import plotting
from .analysis import BacktestReport, backtest_frequencies, compare, run_rolling_windows
from .engine import SimulationResult, simulate_dca, simulate_lsi
from .rates import livret_a_rate

__all__ = [
    "configure_logging",
    "compare", "backtest_frequencies", "run_rolling_windows", "BacktestReport",
    "simulate_lsi", "simulate_dca", "SimulationResult",
    "livret_a_rate", "plotting",
]


def configure_logging(level: int = logging.INFO) -> None:
    """INFO (default): one curated line per run. DEBUG: one line per window too."""
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("lsi_dca")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

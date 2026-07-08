# Dollar-Cost Averaging vs. Lump-Sum Investing — Evidence from France

Empirical backtest engine and research paper comparing Lump-Sum Investing (LSI)
and Dollar-Cost Averaging (DCA) on Euronext Paris stocks and the CAC 40 index,
using rolling 5-year windows (2010–2020) and paired significance tests.

**📄 Full paper: [`Final_papers_DCA_LSI.pdf`](Final_papers_DCA_LSI.pdf)**
(LaTeX source: [`dca_lsi_france_corrected.tex`](dca_lsi_france_corrected.tex))

## Headline result

Over 60 rolling 5-year windows on the CAC 40 index, LSI beats DCA in 73–77% of
windows (mean HPR 33.1% vs. 20–21%), at the cost of roughly double the
volatility. DCA's relative advantage is conditional on the entry regime: it
wins outright on names that spent the sample range-bound or declining
(Engie, Alstom, Carrefour), and is essentially irrelevant on structurally
bullish names, where LSI wins nearly every window.

## What's in this repo

| Path | What it is |
|---|---|
| [`lsi_dca/`](lsi_dca) | The simulation library — clean, tested, typed. Use this. |
| [`tests/`](tests) | pytest suite: synthetic-data unit tests + live regression tests |
| [`lump_sum_investing_vs_dollar_cost_averaging.ipynb`](lump_sum_investing_vs_dollar_cost_averaging.ipynb) | Notebook reproducing every table/figure in the paper |
| [`lump_sum_investing_vs_dollar_cost_averaging.py`](lump_sum_investing_vs_dollar_cost_averaging.py) | Original monolithic script (kept for reference; superseded by `lsi_dca/`) |
| [`comparaison_finale_corrigee.xlsx`](comparaison_finale_corrigee.xlsx) | Full numeric results (index + 37 constituents) |
| [`Literature review/`](Literature%20review) | Background papers referenced in the study |

## A data bug worth knowing about

An earlier version of this pipeline silently double-counted dividends: it
fetched prices already dividend-adjusted from Yahoo Finance (`yfinance`'s
default), then reinvested the same dividend a second time through an explicit
DRIP loop. This overstated individual-stock returns by 10–30+ percentage
points in some cases (index-level results were unaffected — a price index has
no dividend data to double-count). `lsi_dca/data.py` fetches raw prices and
documents why; `tests/test_data_live.py` is a regression guard against this
resurfacing. If you're backtesting anything dividend-sensitive with
`yfinance`, check this isn't happening to you too.

## Quickstart

```bash
pip install -r requirements.txt

python -c "
import logging, lsi_dca
lsi_dca.configure_logging(logging.INFO)

report = lsi_dca.compare('^FCHI', 12_000, '2010-01-04',
                          window_years=5, shift_months=1, n_windows=60, dca_freq='S')
print(report.summary)
print(report.tests)
"
```

```python
from lsi_dca import plotting
plotting.equity_curves(lsi_result.equity_curve, dca_result.equity_curve)
```

Run the tests (network-free ones by default):

```bash
pytest tests/ -m "not network"
```

## Method, briefly

- **LSI**: full capital deployed at $t_0$'s open, dividends reinvested (DRIP) at each ex-date's close.
- **DCA**: capital split into equal tranches invested at a fixed frequency; idle cash earns the historical French *Livret A* rate (not 0%) until deployed.
- **Evaluation**: 60 overlapping 5-year rolling windows, 1-month shift, on the CAC 40 index and 38 constituents. Paired Wilcoxon/Mann-Whitney tests exploit the fact that both strategies share the same market path within each window.

Full derivation and results in the paper.

## Citation

```
Ndzonde Fonkou, Y. L. (2026). Dollar-Cost Averaging Versus Lump-Sum-Investing:
Evidence from France.
```

## License

Code: MIT (see [`LICENSE`](LICENSE)). Paper text/PDF: © the author. Third-party
papers under `Literature review/`: © their respective authors, included for
research reference.

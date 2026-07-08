# Dollar-Cost Averaging vs. Lump-Sum Investing — Evidence from France

Rolling-window backtest comparing Lump-Sum Investing (LSI) and Dollar-Cost
Averaging (DCA) on Euronext Paris stocks and the CAC 40 index (2010–2020).

- **[`lump_sum_investing_vs_dollar_cost_averaging.ipynb`](lump_sum_investing_vs_dollar_cost_averaging.ipynb)** — self-contained notebook that runs the full backtest and reproduces every table and figure below. No external dependency beyond the packages it installs in its first cell.
- **[`Final_papers_DCA_LSI.pdf`](Final_papers_DCA_LSI.pdf)** — the paper.

## Headline result

Over 60 rolling 5-year windows on the CAC 40 index, LSI beats DCA in 73–77% of
windows (mean HPR 33.1% vs. 20–21%), at roughly double the volatility. DCA's
edge is conditional on the entry regime: it wins outright on names that spent
the sample range-bound or declining (Engie, Alstom, Carrefour), and is
essentially irrelevant on structurally bullish names, where LSI wins nearly
every window.

## Method, briefly

- **LSI**: full capital deployed at $t_0$'s open, dividends reinvested (DRIP) at each ex-date's close.
- **DCA**: capital split into equal tranches invested at a fixed frequency; idle cash earns the historical French *Livret A* rate (not 0%) until deployed.
- Prices are fetched raw (`auto_adjust=False`): Yahoo Finance's default already
  folds dividends into the price series, so combining that with the explicit
  DRIP loop above would double-count every dividend. Worth checking if you're
  backtesting anything dividend-sensitive with `yfinance`.
- 60 overlapping 5-year rolling windows, 1-month shift, on the CAC 40 index and
  38 constituents. Paired Wilcoxon/Mann-Whitney tests exploit the fact that
  both strategies share the same market path within each window.

Full derivation and results in the paper.

## Citation

```
Ndzonde Fonkou, Y. L. (2026). Dollar-Cost Averaging Versus Lump-Sum-Investing:
Evidence from France.
```

## License

Code (notebook): MIT, see [`LICENSE`](LICENSE). Paper text/PDF: © the author.

# Metrics Reference — fetch-market-data

Complete list of all supported options. Pass any combination in a single command.

Default (no flags): `--price`

## Stock Price & Market Data

| Option | Description | Return type | Source speed |
|--------|-------------|-------------|--------------|
| `--price` | Current price | float | Fast |
| `--volume` | Latest trading volume | int | Fast |
| `--avg-volume` | 3-month average volume | float | Fast |
| `--week52-high` | 52-week high | float | Medium |
| `--week52-low` | 52-week low | float | Medium |
| `--market-cap` | Market capitalisation | int | Medium |
| `--price-change` | Day change (absolute, currency) | float | Medium |
| `--price-change-pct` | Day change (decimal fraction) | float | Medium |
| `--weekly-change` | 5-day change (decimal fraction) | float | Medium |
| `--monthly-change` | 1-month change (decimal fraction) | float | Medium |

## Valuation

| Option | Description | Return type | Source speed |
|--------|-------------|-------------|--------------|
| `--trailing-pe` | Trailing P/E ratio | float | Medium |
| `--forward-pe` | Forward P/E ratio | float | Medium |
| `--pbr` | Price-to-Book ratio | float | Medium |
| `--psr` | Price-to-Sales (TTM) | float | Medium |
| `--ev-ebitda` | EV/EBITDA | float | Medium |
| `--peg` | PEG ratio | float | Medium |
| `--dividend-yield` | Dividend yield (decimal) | float | Medium |
| `--payout-ratio` | Payout ratio (decimal) | float | Medium |

## Income Statement

| Option | Description | Return type | Source speed |
|--------|-------------|-------------|--------------|
| `--revenue` | Total revenue, latest annual | int | Slow |
| `--revenue-growth` | Revenue YoY growth from annual statements (decimal) | float | Slow |
| `--revenue-growth-ttm` | Revenue TTM growth from `info` — same source as `screen-market-data` screener (decimal) | float | Medium |
| `--operating-income` | Operating income, latest annual | int | Slow |
| `--operating-margin` | Operating margin (decimal) | float | Slow |
| `--gross-margin` | Gross margin (decimal) | float | Slow |
| `--net-income` | Net income, latest annual | int | Slow |
| `--trailing-eps` | Trailing EPS | float | Medium |
| `--forward-eps` | Forward EPS | float | Medium |

## Balance Sheet

| Option | Description | Return type | Source speed |
|--------|-------------|-------------|--------------|
| `--cash` | Cash & equivalents, latest annual | int | Slow |
| `--goodwill` | Goodwill, latest annual | int | Slow |
| `--intangible-assets` | Intangible assets, latest annual | int | Slow |
| `--equity-ratio` | Equity / Total Assets (decimal) | float | Slow |
| `--debt-ebitda` | Total Debt / EBITDA | float | Slow |

## Cash Flow

| Option | Description | Return type | Source speed |
|--------|-------------|-------------|--------------|
| `--operating-cf` | Operating cash flow, latest annual | int | Slow |
| `--fcf` | Free cash flow (from info) | int | Medium |
| `--fcf-margin` | FCF / Revenue (decimal) | float | Slow |
| `--buyback` | Repurchase of capital stock (usually negative) | int | Slow |

## Profitability & Risk

| Option | Description | Return type | Source speed |
|--------|-------------|-------------|--------------|
| `--roe` | Return on Equity (decimal) | float | Medium |
| `--roa` | Return on Assets (decimal) | float | Medium |
| `--beta` | Beta (market sensitivity) | float | Medium |

## Shareholder Returns

| Option | Description | Return type | Source speed |
|--------|-------------|-------------|--------------|
| `--dividend-history` | Full dividend history (date → amount JSON) | object | Medium |
| `--dividend-growth` | Annual dividend YoY growth (decimal) | float | Medium |
| `--total-return-ratio` | (Dividends + Buyback) / Net Income | float | Slow |

## Analyst & Growth Data

| Option | Description | Return type | Source speed |
|--------|-------------|-------------|--------------|
| `--eps-estimate` | Analyst EPS estimates (list of records) | array | Medium |
| `--revenue-estimate` | Analyst revenue estimates (list of records) | array | Medium |
| `--price-target` | Analyst price targets (min/mean/max dict) | object | Medium |
| `--ratings` | Analyst rating distribution (buy/hold/sell) | array | Medium |

## Events & Qualitative

| Option | Description | Return type | Source speed |
|--------|-------------|-------------|--------------|
| `--guidance` | Full earnings calendar dict | object | Medium |
| `--next-earnings` | Next earnings date(s) | array of ISO strings | Medium |
| `--insider-trades` | Insider transaction history (list of records) | array | Slow |
| `--major-holders` | Major shareholders (list of records) | array | Slow |

---

## Notes

- **Japanese stocks** (`.T` suffix): analyst metrics (`--ratings`, `--price-target`, `--eps-estimate`, `--revenue-estimate`) typically return `null` — Yahoo Finance analyst coverage is US-centric.
- **`--revenue-growth` vs `--revenue-growth-ttm`**: `--revenue-growth` computes YoY from annual financial statements (two most recent fiscal years). `--revenue-growth-ttm` uses `info["revenueGrowth"]`, a trailing-twelve-month figure matching the EquityQuery field used by `screen-market-data`. Use `--revenue-growth-ttm` when comparing against screener results.
- **Source speed** indicates relative latency. Slow sources make additional HTTP requests to Yahoo Finance. Combine slow-source metrics together to minimise total fetches (each source is fetched at most once per ticker per call).
- `--debt-ebitda` uses Operating Income + D&A for EBITDA. If D&A is unavailable, Operating Income alone is used.
- `--buyback` reflects cashflow statement values and is typically **negative** (cash outflow). Take `abs()` when summing with dividends.
- Data is sourced from Yahoo Finance via [yfinance](https://github.com/ranaroussi/yfinance), an unofficial API. Field availability may vary across tickers and yfinance versions.

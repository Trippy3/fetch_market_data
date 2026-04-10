**Language:** [日本語](README.md) | English

# fetch-market-data

A package providing two CLI tools for US and Japanese equities.

| Tool | Purpose |
|------|---------|
| `fetch-market-data` | Fetch metrics for given ticker symbols, returned as JSON |
| `screen-market-data` | Screen stocks by conditions, returns matching ticker list as JSON |

## Overview

Stock data is retrieved using [yfinance](https://github.com/ranaroussi/yfinance), an unofficial Python library for Yahoo Finance data.

## Claude Code Plugin

This repository is distributed as a Claude Code Plugin. Installing it gives AI agents a Skill to autonomously use this tool.

```bash
# 1. Register the marketplace
claude plugin marketplace add Trippy3/fetch_market_data

# 2. Install the plugin
claude plugin install fetch-market-data@fetch-market-data-marketplace
```

## Requirements

- [uv](https://github.com/astral-sh/uv) must be installed

## Run without installing (uvx)

```bash
# Run directly from GitHub
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data AAPL MSFT 7203.T
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data --region jp --roe-min 10

# Local development (add --reinstall after changes)
uvx --from . --reinstall fetch-market-data AAPL --price
uvx --from . screen-market-data --region jp --roe-min 10
```

## fetch-market-data Usage

```
fetch-market-data SYMBOL [SYMBOL ...] [--price] [--market-cap] [--trailing-pe] ...
```


If no metric option is given, `--price` is applied by default. Multiple metrics can be specified at once.

### Examples

```bash
# Default (same as --price)
fetch-market-data AAPL MSFT 7203.T

# Multiple metrics at once
fetch-market-data AAPL MSFT --price --market-cap --trailing-pe --dividend-yield

# Japanese stocks
fetch-market-data 7203.T 6758.T --price --pbr --roe
```

## Output Format

Outputs a JSON object keyed by ticker symbol to `stdout`.

```json
{
  "AAPL": {
    "price": 255.92,
    "market-cap": 3761492983808,
    "trailing-pe": 32.354,
    "dividend-yield": 0.0041,
    "currency": "USD",
    "error": null
  },
  "7203.T": {
    "price": 3255.0,
    "market-cap": 42423669489664,
    "trailing-pe": 11.4564,
    "dividend-yield": 0.0291,
    "currency": "JPY",
    "error": null
  }
}
```

`currency` and `error` are always included. Metrics that could not be retrieved are `null`.

## Supported Markets

| Market | Ticker Format | Example |
|--------|---------------|---------|
| US equities | Symbol as-is | `AAPL`, `MSFT` |
| Japanese equities | Code + `.T` | `7203.T`, `6758.T` |

## Metrics

### Price & Market Data

| Option | Description |
|--------|-------------|
| `--price` | Current price (default) |
| `--volume` | Latest trading volume |
| `--avg-volume` | 3-month average volume |
| `--week52-high` | 52-week high |
| `--week52-low` | 52-week low |
| `--market-cap` | Market capitalisation |
| `--price-change` | Day change (absolute) |
| `--price-change-pct` | Day change (decimal fraction) |
| `--weekly-change` | 5-day change (decimal fraction) |
| `--monthly-change` | 1-month change (decimal fraction) |

### Valuation

| Option | Description |
|--------|-------------|
| `--trailing-pe` | Trailing P/E ratio |
| `--forward-pe` | Forward P/E ratio |
| `--pbr` | Price-to-Book ratio |
| `--psr` | Price-to-Sales (TTM) |
| `--ev-ebitda` | EV/EBITDA |
| `--peg` | PEG ratio |
| `--dividend-yield` | Dividend yield (decimal) |
| `--payout-ratio` | Payout ratio (decimal) |

### Financials

| Option | Description |
|--------|-------------|
| `--revenue` | Total revenue, latest annual |
| `--revenue-growth` | Revenue YoY growth from annual statements (decimal) |
| `--revenue-growth-ttm` | Revenue TTM growth — same source as `screen-market-data` screener (decimal) |
| `--operating-income` | Operating income, latest annual |
| `--operating-margin` | Operating margin (decimal) |
| `--gross-margin` | Gross margin (decimal) |
| `--net-income` | Net income, latest annual |
| `--trailing-eps` | Trailing EPS |
| `--forward-eps` | Forward EPS |
| `--cash` | Cash & equivalents |
| `--goodwill` | Goodwill |
| `--intangible-assets` | Intangible assets |
| `--equity-ratio` | Equity ratio (decimal) |
| `--debt-ebitda` | Total Debt / EBITDA |
| `--operating-cf` | Operating cash flow |
| `--fcf` | Free cash flow |
| `--fcf-margin` | FCF margin (decimal) |

### Profitability & Risk

| Option | Description |
|--------|-------------|
| `--roe` | Return on Equity (decimal) |
| `--roa` | Return on Assets (decimal) |
| `--beta` | Beta |

### Shareholder Returns

| Option | Description |
|--------|-------------|
| `--buyback` | Share repurchases, latest annual (usually negative) |
| `--dividend-history` | Dividend history (date → amount JSON) |
| `--dividend-growth` | Dividend YoY growth (decimal) |
| `--total-return-ratio` | (Dividends + Buyback) / Net Income |

### Analyst & Growth Data

| Option | Description |
|--------|-------------|
| `--eps-estimate` | Analyst EPS estimates (JSON) |
| `--revenue-estimate` | Analyst revenue estimates (JSON) |
| `--price-target` | Analyst price targets — min/mean/max (JSON) |
| `--ratings` | Analyst rating distribution — buy/hold/sell (JSON) |

### Events & Qualitative

| Option | Description |
|--------|-------------|
| `--guidance` | Earnings calendar and guidance (JSON) |
| `--next-earnings` | Next earnings date |
| `--insider-trades` | Insider transaction history (JSON) |
| `--major-holders` | Major shareholders (JSON) |

## screen-market-data Usage

Screen stocks by combining multiple conditions and returns a JSON list of matching ticker symbols.

```
screen-market-data (--region jp|us | --exchange nasdaq|nyse|us) [filter options]
```

Either `--region` or `--exchange` is required.

### Examples

```bash
# Japanese stocks: ROE 10%+, dividend yield 1.5%+, 3+ years consecutive dividend growth
screen-market-data --region jp --roe-min 10 --div-yield-min 1.5 --div-growth-years 3

# US NASDAQ: revenue growth 15%+, gross margin 50%+, positive FCF
screen-market-data --exchange nasdaq --revenue-growth-min 15 --gross-margin-min 50 --fcf-positive

# US NYSE+NASDAQ Technology sector, insider ownership 5%+, top 20
screen-market-data --region us --sector Technology --insider-min 5 --size 20

# NYSE: PEG ratio below 1.0, Debt/EBITDA below 5x
screen-market-data --exchange nyse --peg-max 1.0 --debt-ebitda-max 5
```

### Output Format

```json
{
  "query": {
    "region": "jp",
    "exchange": null,
    "offset": 0,
    "conditions": {
      "roe_min": 10.0,
      "div_yield_min": 1.5,
      "div_growth_years": 3
    }
  },
  "total": 42,
  "count": 5,
  "tickers": ["7203.T", "8031.T", "8035.T", "8001.T", "8766.T"]
}
```

### Filter Options

| Option | Description | Market |
|--------|-------------|--------|
| `--roe-min PCT` | Minimum ROE (%) | JP / US |
| `--div-yield-min PCT` | Minimum forward dividend yield (%) | JP / US |
| `--div-growth-years N` | Minimum consecutive years of dividend growth | JP / US |
| `--revenue-growth-min PCT` | Minimum YoY revenue growth (%) | JP / US |
| `--debt-ebitda-max RATIO` | Maximum Total Debt / EBITDA | JP / US |
| `--fcf-positive` | Require positive free cash flow | JP / US |
| `--gross-margin-min PCT` | Minimum gross margin (%) | JP / US |
| `--peg-max RATIO` | Maximum PEG ratio | JP / US |
| `--insider-min PCT` | Minimum insider ownership (%) | JP / US |
| `--market-cap-min VALUE` | Minimum market cap (JPY or USD) | JP / US |
| `--sector SECTOR` | Sector filter (e.g. Technology) | JP / US |
| `--size N` | Maximum results per page (default: 50) | JP / US |
| `--offset N` | Starting index for pagination (default: 0) | JP / US |
| `--sort-by FIELD` | Sort field (default: intradaymarketcap) | JP / US |
| `--sort-asc` | Sort ascending (default: descending) | JP / US |

> **Note**: Filtering by TSE market segment (Prime / Standard / Growth) is not currently supported.
> The yfinance screener API does not distinguish between segments; `--region jp` targets the entire TSE.

> **Data discrepancy warning**: `screen-market-data` and `fetch-market-data` may reference different fields for the same concept.
> For example, revenue growth in the screener is TTM-based, while `--revenue-growth` uses annual financial statements — these can diverge.
> Use `--revenue-growth-ttm` to compare against screener results on the same basis. **When values conflict, treat the fetch value as authoritative.**

### Recommended Workflow

```bash
# Step 1: narrow candidates with screen-market-data
screen-market-data --region jp --roe-min 10 --div-yield-min 1.5 --div-growth-years 3

# Step 2: fetch detailed metrics with fetch-market-data
fetch-market-data 7203.T 8031.T --payout-ratio --equity-ratio --operating-margin --price-target
```

### Pagination

Use the `total` field to see the total match count, then page through results with `--offset`.

```bash
# Page 1 (results 0–49)
screen-market-data --region jp --roe-min 10 --size 50 --offset 0

# Page 2 (results 50–99)
screen-market-data --region jp --roe-min 10 --size 50 --offset 50
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v --cov=src

# Run locally
uv run fetch-market-data AAPL --price --market-cap
```

### Lint / Format (ruff)

[ruff](https://github.com/astral-sh/ruff) is used as the linter and formatter.

```bash
# Lint check
uv run ruff check src/ tests/

# Auto-fix lint issues
uv run ruff check --fix src/ tests/

# Format
uv run ruff format src/ tests/

# Lint + format check together
uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/
```

Configuration is managed in the `[tool.ruff]` section of `pyproject.toml`. Enabled rule sets:

| Rule | Description |
|------|-------------|
| `E`, `W` | pycodestyle (style) |
| `F` | pyflakes (unused variables/imports) |
| `I` | isort (import order) |
| `B` | flake8-bugbear (bug-prone patterns) |
| `UP` | pyupgrade (modern Python syntax) |

### Adding a New Metric

Add a single entry to `_METRICS` in `src/fetch_market_data/fetcher.py`:

```python
_METRICS: dict[str, MetricDef] = {
    # existing metrics ...

    # Single-source metric
    "new-metric": MetricDef(("info",), lambda d: d.get("someKey")),

    # Multi-source metric (e.g. calculated from balance_sheet + income_stmt)
    "cross-metric": MetricDef(("balance_sheet", "income_stmt"), lambda bs, inc: ...),
}
```

The `--new-metric` option becomes available automatically after adding the entry.

Supported data sources:

| Source | Content | Speed |
|--------|---------|-------|
| `fast_info` | Price, volume, basic info | Fast |
| `info` | Valuation ratios, financial ratios | Medium |
| `income_stmt` | Income statement (annual/quarterly) | Slow |
| `balance_sheet` | Balance sheet (annual/quarterly) | Slow |
| `cashflow` | Cash flow statement (annual/quarterly) | Slow |
| `history_2d` / `history_5d` / `history_1mo` | Price history (by period) | Medium |
| `dividends` | Dividend history Series | Medium |
| `calendar` | Earnings calendar / guidance dict | Medium |
| `earnings_estimate` / `revenue_estimate` | Analyst estimate DataFrames | Medium |
| `analyst_price_targets` | Price target dict | Medium |
| `recommendations_summary` | Rating distribution DataFrame | Medium |
| `insider_transactions` | Insider transactions DataFrame | Slow |
| `major_holders` | Major holders DataFrame | Slow |

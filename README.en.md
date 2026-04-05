**Language:** [日本語](README.md) | English

# fetch-market-data

A CLI tool that accepts US and Japanese stock ticker symbols and returns specified metrics in JSON format.

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
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data AAPL MSFT 7203.T
```

## Usage

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
| `--revenue-growth` | Revenue YoY growth (decimal) |
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

---
name: fetch-market-data
description: This skill should be used when the user asks to "fetch stock data", "get financial metrics for a ticker", "retrieve market data", "analyze stock valuation", "check a company's financials", "get dividend yield", "look up PE ratio", "run fetch-market-data", or any task involving equity data for US or Japanese stocks.
version: 1.0.0
---

# fetch-market-data Skill

CLI tool that returns stock market data as JSON. Supports US equities (e.g. `AAPL`) and Japanese equities (e.g. `7203.T`). Data is sourced from Yahoo Finance via [yfinance](https://github.com/ranaroussi/yfinance).

## Prerequisites

[uv](https://github.com/astral-sh/uv) must be installed. Run `which uv` to verify.

## Command Syntax

```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data SYMBOL [SYMBOL ...] [OPTIONS]
```

Multiple symbols and multiple metric flags can be combined in a single call.

> **Development note**: if you have the repository cloned, use `uv run fetch-market-data` instead of the `uvx` form above.

## Output Format

Always outputs a JSON object to **stdout**, keyed by ticker symbol:

```json
{
  "AAPL": {
    "price": 213.49,
    "trailing-pe": 32.35,
    "dividend-yield": 0.0046,
    "currency": "USD",
    "error": null
  },
  "7203.T": {
    "price": 3255.0,
    "trailing-pe": 11.46,
    "dividend-yield": 0.0291,
    "currency": "JPY",
    "error": null
  }
}
```

- `currency`: always present — `"USD"` for US stocks, `"JPY"` for Japanese stocks (`.T` suffix)
- `error`: `null` on success; error message string if the ticker failed entirely
- metric fields: numeric value, or `null` if unavailable for that ticker
- numeric values are rounded to 4 decimal places

## Unit Conventions

**Critical**: ratio/percentage metrics are returned as **decimals**, not percentages.

| Metric | Unit | Example | Meaning |
|--------|------|---------|---------|
| `price-change-pct` | decimal | `0.0312` | +3.12% |
| `weekly-change` | decimal | `-0.0215` | -2.15% |
| `monthly-change` | decimal | `0.0841` | +8.41% |
| `dividend-yield` | decimal | `0.0046` | 0.46% |
| `operating-margin` | decimal | `0.2973` | 29.73% |
| `gross-margin` | decimal | `0.4563` | 45.63% |
| `equity-ratio` | decimal | `0.3120` | 31.20% |
| `fcf-margin` | decimal | `0.2241` | 22.41% |
| `revenue-growth` | decimal | `0.0623` | +6.23% YoY |
| `dividend-growth` | decimal | `0.0400` | +4.00% YoY |
| `roe` / `roa` | decimal | `1.4732` | 147.32% |
| `price`, `market-cap`, `revenue`, etc. | absolute | `213.49` | currency units |
| `buyback` | absolute, usually negative | `-89000000000` | cash outflow |

## Analysis Patterns

All examples use the full `uvx` invocation. Replace `uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data` with `uv run fetch-market-data` if running from the cloned repository.

### Valuation check
```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data AAPL MSFT \
  --price --trailing-pe --forward-pe --pbr --peg --ev-ebitda
```

### Dividend income evaluation
```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data 7203.T 6758.T \
  --price --dividend-yield --payout-ratio --dividend-growth
```

### Growth quality
```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data NVDA AMZN \
  --revenue-growth --operating-margin --gross-margin --fcf-margin
```

### Financial health
```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data 9984.T \
  --equity-ratio --debt-ebitda --cash --operating-cf
```

### Shareholder returns
```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data AAPL \
  --buyback --dividend-history --total-return-ratio --payout-ratio
```

### Analyst consensus
```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data TSLA \
  --price-target --ratings --eps-estimate --revenue-estimate
```

### Upcoming events
```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data AAPL \
  --next-earnings --guidance
```

### Compare US + Japan
```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data AAPL 6758.T \
  --price --trailing-pe --pbr --roe --dividend-yield
```

## Error Handling

| Situation | What you see | Action |
|-----------|-------------|--------|
| Invalid ticker | `"error": "Ticker not found"` | Check symbol; add `.T` for Japanese stocks |
| Data unavailable | metric is `null`, `"error": null` | Normal — not all metrics exist for all tickers |
| Source fetch failed | metric is `null`, `"error": "..."` | Transient network issue; retry |
| Japanese stocks missing analyst data | `null` on `--ratings`, `--price-target`, etc. | Expected — Yahoo Finance analyst coverage is US-centric |

`[warn]` lines on stderr are informational and do not affect JSON output.

## Structured Metrics

Some metrics return nested JSON instead of a scalar:

- `--dividend-history` → `{"2023-12-15T00:00:00": 0.24, ...}` (date → amount)
- `--ratings` → `[{"strongBuy": 28, "buy": 12, ...}]`
- `--guidance` → full calendar dict including revenue/EPS estimates
- `--eps-estimate` / `--revenue-estimate` → list of analyst estimate records
- `--price-target` → `{"current": 240.0, "low": 180.0, "mean": 255.0, "high": 320.0}`
- `--insider-trades` / `--major-holders` → list of records

## Supported Markets

| Market | Format | Example |
|--------|--------|---------|
| US equities | Symbol as-is | `AAPL`, `MSFT`, `NVDA` |
| Japanese equities | Code + `.T` | `7203.T`, `6758.T`, `9984.T` |

## Full Metrics Reference

See `references/metrics-reference.md` for the complete list of all 48 supported options.

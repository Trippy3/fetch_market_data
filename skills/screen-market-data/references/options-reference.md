# Options Reference — screen-market-data

Complete list of all supported options. All filter options are optional and combined with AND logic.

## Market Selection (one required)

| Option | Values | Scope | Exchange codes |
|--------|--------|-------|----------------|
| `--region jp` | `jp` | All Tokyo Stock Exchange | `JPX` |
| `--region us` | `us` | NYSE + NASDAQ | `NYQ`, `NMS` |
| `--exchange nasdaq` | `nasdaq` | NASDAQ only | `NMS` |
| `--exchange nyse` | `nyse` | NYSE only | `NYQ` |
| `--exchange us` | `us` | NYSE + NASDAQ | `NYQ`, `NMS` |

> `--region` and `--exchange` are mutually exclusive.

---

## Filter Options

### Profitability

| Option | Description | Unit | EquityQuery field |
|--------|-------------|------|------------------|
| `--roe-min PCT` | Minimum Return on Equity | % (e.g. `10` = 10%) | `returnonequity.lasttwelvemonths` |
| `--gross-margin-min PCT` | Minimum gross profit margin | % (e.g. `50` = 50%) | `grossprofitmargin.lasttwelvemonths` |

### Dividend

| Option | Description | Unit | EquityQuery field |
|--------|-------------|------|------------------|
| `--div-yield-min PCT` | Minimum forward dividend yield | % (e.g. `1.5` = 1.5%) | `forward_dividend_yield` |
| `--div-growth-years N` | Minimum consecutive years of dividend growth | integer | `consecutive_years_of_dividend_growth_count` |

### Growth

| Option | Description | Unit | EquityQuery field |
|--------|-------------|------|------------------|
| `--revenue-growth-min PCT` | Minimum YoY revenue growth (TTM) | % (e.g. `15` = 15%) | `totalrevenues1yrgrowth.lasttwelvemonths` |

### Cash Flow

| Option | Description | Unit | EquityQuery field |
|--------|-------------|------|------------------|
| `--fcf-positive` | Require positive levered free cash flow | flag (no value) | `leveredfreecashflow.lasttwelvemonths > 0` |

### Leverage

| Option | Description | Unit | EquityQuery field |
|--------|-------------|------|------------------|
| `--debt-ebitda-max RATIO` | Maximum Total Debt / EBITDA | ratio (e.g. `5` = 5x) | `totaldebtebitda.lasttwelvemonths` |

### Valuation

| Option | Description | Unit | EquityQuery field |
|--------|-------------|------|------------------|
| `--peg-max RATIO` | Maximum PEG ratio (5-year) | ratio (e.g. `1.0`) | `pegratio_5y` |

### Ownership

| Option | Description | Unit | EquityQuery field |
|--------|-------------|------|------------------|
| `--insider-min PCT` | Minimum insider ownership | % (e.g. `5` = 5%) | `pctheldinsider` |

### Market Filter

| Option | Description | Unit | EquityQuery field |
|--------|-------------|------|------------------|
| `--market-cap-min VALUE` | Minimum market capitalisation | base currency (JPY or USD) | `intradaymarketcap` |
| `--sector SECTOR` | Sector filter | exact Yahoo Finance name (see below) | `sector` |

#### Valid sector names

```
Technology, Healthcare, Financial Services, Consumer Cyclical, Consumer Defensive,
Industrials, Communication Services, Energy, Basic Materials, Utilities, Real Estate
```

---

## Output Control

| Option | Default | Description |
|--------|---------|-------------|
| `--size N` | `50` | Maximum number of results per page |
| `--offset N` | `0` | Starting index for pagination |
| `--sort-by FIELD` | `intradaymarketcap` | EquityQuery field to sort by (see below) |
| `--sort-asc` | `false` (descending) | Sort ascending when flag is set |

#### Useful `--sort-by` values

| Field | Meaning |
|-------|---------|
| `intradaymarketcap` | Market cap (default) |
| `forward_dividend_yield` | Dividend yield |
| `returnonequity.lasttwelvemonths` | ROE |
| `totalrevenues1yrgrowth.lasttwelvemonths` | Revenue growth |
| `grossprofitmargin.lasttwelvemonths` | Gross margin |
| `consecutive_years_of_dividend_growth_count` | Consecutive dividend growth years |
| `percentchange` | Day change % |
| `eodvolume` | Volume |

---

## Notes

- All `PCT` values are entered as numbers (e.g. `10` means 10%, not `0.10`).
- Conditions are combined with AND. There is no OR between filter options.
- `--fcf-positive` is a boolean flag — it takes no value.
- Results are capped by Yahoo Finance's screener API. Use `--size` to control the limit (max varies by API).
- For Japanese stocks, analyst-oriented fields (PEG ratio etc.) may return no results due to limited Yahoo Finance coverage of Japanese equities.
- Data is sourced from Yahoo Finance via [yfinance](https://github.com/ranaroussi/yfinance), an unofficial API. Field availability may vary.

---

## Complementary fetch-market-data Options (post-screen filtering)

The following metrics are **not available in `screen-market-data`** but can be fetched per-ticker with `fetch-market-data` for further filtering:

| fetch-market-data option | Use case |
|--------------------------|----------|
| `--payout-ratio` | Dividend payout ratio 20–60% check |
| `--equity-ratio` | Self-equity ratio ≥ 30% check |
| `--operating-margin` | Operating margin ≥ 10% check |
| `--price-target` | Analyst upside ≥ 20% check |
| `--dividend-history` | Dividend cut detection (last 5 years) |
| `--revenue-growth` | Single-year revenue growth (decimal) |

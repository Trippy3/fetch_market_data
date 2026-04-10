---
name: screen-market-data
description: This skill should be used when the user asks to "screen stocks", "filter stocks by condition", "find stocks with high ROE", "search for dividend stocks", "find growth stocks", "narrow down candidates", "run a stock screener", "find undervalued stocks", "screen Japanese stocks", "screen US stocks", "run screen-market-data", or any task involving filtering equities by financial metrics to get a list of matching tickers.
version: 1.1.0
---

# screen-market-data Skill

CLI tool that screens equities by financial conditions and returns matching ticker symbols as JSON.
Supports Japanese stocks (Tokyo Stock Exchange) and US stocks (NYSE / NASDAQ).
Data is sourced from Yahoo Finance via [yfinance](https://github.com/ranaroussi/yfinance) `EquityQuery`.

## Prerequisites

[uv](https://github.com/astral-sh/uv) must be installed. Run `which uv` to verify.

## Command Syntax

```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  (--region jp|us | --exchange nasdaq|nyse|us) [FILTER OPTIONS]
```

Either `--region` or `--exchange` is required. All filter options are optional and combined with AND logic.

> **Development note**: if you have the repository cloned, use `uvx --from . screen-market-data` instead.

## Output Format

Always outputs a JSON object to **stdout**:

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
  "count": 8,
  "tickers": ["4776.T", "6036.T", "3854.T", "4482.T", "3064.T", "3939.T", "3916.T", "3482.T"]
}
```

- `query.conditions`: only set options are included (unset options are omitted)
- `query.offset`: starting index used for this page
- `total`: total number of matches in Yahoo Finance (for pagination calculation); `null` if not returned by API
- `count`: number of tickers returned in this response
- `tickers`: list of matching ticker symbols, sorted by `--sort-by` (default: market cap descending)

## Market Selection

| Option | Scope | Notes |
|--------|-------|-------|
| `--region jp` | All Tokyo Stock Exchange stocks | Prime / Standard / Growth are **not** distinguished — all return as `JPX` |
| `--region us` | NYSE + NASDAQ combined | Equivalent to `--exchange us` |
| `--exchange nasdaq` | NASDAQ only (`NMS`) | |
| `--exchange nyse` | NYSE only (`NYQ`) | |
| `--exchange us` | NYSE + NASDAQ combined | |

## Filter Options

> **Full option reference with EquityQuery field mapping**: See `references/options-reference.md`.

| Option | Description | Example |
|--------|-------------|---------|
| `--roe-min PCT` | Minimum ROE (%) | `--roe-min 10` |
| `--div-yield-min PCT` | Minimum forward dividend yield (%) | `--div-yield-min 1.5` |
| `--div-growth-years N` | Minimum consecutive years of dividend growth | `--div-growth-years 3` |
| `--revenue-growth-min PCT` | Minimum YoY revenue growth (%) | `--revenue-growth-min 15` |
| `--debt-ebitda-max RATIO` | Maximum Total Debt / EBITDA | `--debt-ebitda-max 5` |
| `--fcf-positive` | Require positive free cash flow (flag) | `--fcf-positive` |
| `--gross-margin-min PCT` | Minimum gross margin (%) | `--gross-margin-min 50` |
| `--peg-max RATIO` | Maximum PEG ratio (5-year) | `--peg-max 1.0` |
| `--insider-min PCT` | Minimum insider ownership (%) | `--insider-min 5` |
| `--market-cap-min VALUE` | Minimum market cap in base currency | `--market-cap-min 100000000000` |
| `--sector SECTOR` | Sector filter (exact Yahoo Finance name) | `--sector Technology` |
| `--size N` | Max results per page (default: 50) | `--size 20` |
| `--offset N` | Starting index for pagination (default: 0) | `--offset 50` |
| `--sort-by FIELD` | EquityQuery sort field | `--sort-by forward_dividend_yield` |
| `--sort-asc` | Sort ascending (default: descending) | `--sort-asc` |

## Screening Patterns

All examples use the full `uvx` invocation. Replace with `uvx --from . screen-market-data` when running locally.

### JP: ROE & dividend income strategy
ROE 10%+、配当利回り 1.5%+、連続増配 3年以上の国内高配当株

```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  --region jp \
  --roe-min 10 \
  --div-yield-min 1.5 \
  --div-growth-years 3
```

### JP: Conservative dividend + financial health
配当性向・財務健全性を重視した絞り込み（必須フィルタ後に fetch-market-data で精査）

```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  --region jp \
  --roe-min 10 \
  --div-yield-min 1.5 \
  --div-growth-years 3 \
  --revenue-growth-min 3 \
  --debt-ebitda-max 5 \
  --fcf-positive
```

### JP: Growth-oriented domestic stocks
売上成長・FCF プラスの国内成長株

```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  --region jp \
  --revenue-growth-min 10 \
  --gross-margin-min 30 \
  --fcf-positive \
  --size 30
```

### US: High-growth tech (NASDAQ)
売上成長 15%+・粗利率 50%+ の米国グロース株

```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  --exchange nasdaq \
  --revenue-growth-min 15 \
  --gross-margin-min 50 \
  --fcf-positive
```

### US: GARP (Growth At Reasonable Price)
成長性と割安感を両立するバランス型

```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  --region us \
  --revenue-growth-min 15 \
  --gross-margin-min 50 \
  --peg-max 1.5 \
  --fcf-positive
```

### US: Founder-led growth
インサイダー保有 5%以上（経営陣の利益一致）の成長株

```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  --region us \
  --revenue-growth-min 15 \
  --gross-margin-min 50 \
  --insider-min 5
```

### US: Sector-specific screen
特定セクターに絞った基礎フィルタ

```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  --region us \
  --sector Technology \
  --revenue-growth-min 20 \
  --gross-margin-min 60 \
  --fcf-positive \
  --size 20
```

### Sorted by dividend yield
配当利回り順ソート

```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  --region jp \
  --div-yield-min 2.0 \
  --roe-min 8 \
  --sort-by forward_dividend_yield \
  --sort-asc false \
  --size 30
```

## Recommended Workflow

`screen-market-data` はティッカーリストを返すだけです。各銘柄の詳細指標は `fetch-market-data` で取得します。

```bash
# Step 1: 候補を絞る
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  --region jp --roe-min 10 --div-yield-min 1.5 --div-growth-years 3

# Step 2: 候補銘柄の詳細指標を取得（配当性向・自己資本比率など）
uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data \
  4776.T 6036.T 3064.T \
  --payout-ratio --equity-ratio --operating-margin --price-target --dividend-history
```

### Pagination

`total` フィールドを使ってマッチ総件数を確認し、`--offset` でページをめくれます。

```bash
# 1ページ目（0〜49件目）
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  --region jp --roe-min 10 --size 50 --offset 0

# 2ページ目（50〜99件目）
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data \
  --region jp --roe-min 10 --size 50 --offset 50
```

## Error Handling

| Situation | What you see | Action |
|-----------|-------------|--------|
| No market specified | `error: one of the arguments --region/--exchange is required` | Add `--region jp` or `--exchange nasdaq` |
| Invalid region/exchange | `Error: Unknown region 'xx'` (stderr, exit 1) | Use `jp`, `us`, `nasdaq`, `nyse` |
| 0 results | `"count": 0, "tickers": []` | Relax one or more filter conditions |
| Too few results | `"count": N` where N < expected | Lower thresholds or remove a filter |

When `count` is 0, try removing conditions one at a time (strictest first) to identify the bottleneck.

## Data Discrepancy Warning

`screen-market-data` と `fetch-market-data` では、同名に見える指標でも参照フィールドが異なる場合がある。**数値が食い違った場合は `fetch-market-data` の値を正とすること。**

| Metric | screen-market-data (EquityQuery) | fetch-market-data |
|--------|----------------------------------|-------------------|
| 売上成長 | `totalrevenues1yrgrowth.lasttwelvemonths`（TTM） | `--revenue-growth`: 年次財務諸表の2期比較 |
| 売上成長（比較用） | — | `--revenue-growth-ttm`: `info["revenueGrowth"]`（TTMベース、screenerと同一ソース） |

スクリーナー通過後に `fetch-market-data` で確認する際は `--revenue-growth-ttm` を使うと、screener と同じ基準で比較できる。

## Limitations

| Limitation | Detail |
|-----------|--------|
| TSE market segments | Prime / Standard / Growth cannot be filtered — all TSE stocks return `exchange=JPX` |
| Multi-period filters | ROE 3-year consecutive improvement, 3-year average revenue growth — not supported by `EquityQuery`; use `fetch-market-data` for post-filtering |
| Payout ratio filter | `--payout-ratio-min/max` は EquityQuery の valid_fields に存在しないため実装不可 — `fetch-market-data --payout-ratio` で後絞り |
| Equity ratio filter | 自己資本比率フィールドが EquityQuery に存在しないため実装不可 — `fetch-market-data --equity-ratio` で後絞り |
| Operating margin filter | `operatingmargin` フィールドが EquityQuery に存在しないため実装不可 — `fetch-market-data --operating-margin` で後絞り |
| TAM / competitive moat | Qualitative — not automatable |
| Net Revenue Retention | Non-public data — not available in Yahoo Finance |
| Result cap | Yahoo Finance screener API caps results; use `--size` to control |

## Full Options Reference

See `references/options-reference.md` for the complete list of all filter options with valid values and underlying EquityQuery field names.

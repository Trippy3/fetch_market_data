#!/usr/bin/env bash
# screen-market-data — screening pattern examples
#
# Requires: uv  (https://github.com/astral-sh/uv)
#
# Run any example directly — no local installation needed:
#   bash screening-patterns.sh
#
# If you have the repository cloned locally, replace CMD with:
#   CMD="uvx --from . screen-market-data"

CMD="uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data"

# ---------------------------------------------------------------------------
# JP-1. ROE & Dividend income strategy (国内高配当・ROE戦略)
# ROE 10%+, 配当利回り 1.5%+, 連続増配 3年以上
# ---------------------------------------------------------------------------
$CMD \
  --region jp \
  --roe-min 10 \
  --div-yield-min 1.5 \
  --div-growth-years 3

# ---------------------------------------------------------------------------
# JP-2. Conservative dividend + financial health (保守的高配当・財務健全)
# 上記に売上成長・FCFプラス・低レバレッジを追加
# Follow up with: fetch-market-data <tickers> --payout-ratio --equity-ratio
# ---------------------------------------------------------------------------
$CMD \
  --region jp \
  --roe-min 10 \
  --div-yield-min 1.5 \
  --div-growth-years 3 \
  --revenue-growth-min 3 \
  --debt-ebitda-max 5 \
  --fcf-positive

# ---------------------------------------------------------------------------
# JP-3. Domestic growth stocks (国内成長株)
# 売上成長10%+, 粗利率30%+, FCFプラス
# ---------------------------------------------------------------------------
$CMD \
  --region jp \
  --revenue-growth-min 10 \
  --gross-margin-min 30 \
  --fcf-positive \
  --size 30

# ---------------------------------------------------------------------------
# JP-4. Sorted by dividend yield (配当利回り順)
# 配当利回り2%以上を利回り降順で取得
# ---------------------------------------------------------------------------
$CMD \
  --region jp \
  --div-yield-min 2.0 \
  --roe-min 8 \
  --sort-by forward_dividend_yield \
  --size 30

# ---------------------------------------------------------------------------
# US-1. High-growth tech — NASDAQ (米国ハイグロース・NASDAQ)
# 売上成長15%+, 粗利率50%+, FCFプラス
# ---------------------------------------------------------------------------
$CMD \
  --exchange nasdaq \
  --revenue-growth-min 15 \
  --gross-margin-min 50 \
  --fcf-positive

# ---------------------------------------------------------------------------
# US-2. GARP — Growth At Reasonable Price (成長×割安)
# 売上成長15%+, 粗利率50%+, PEG1.5以下, FCFプラス
# ---------------------------------------------------------------------------
$CMD \
  --region us \
  --revenue-growth-min 15 \
  --gross-margin-min 50 \
  --peg-max 1.5 \
  --fcf-positive

# ---------------------------------------------------------------------------
# US-3. Founder-led growth (インサイダー保有×成長)
# 経営陣保有5%以上, 売上成長15%+, 粗利率50%+
# ---------------------------------------------------------------------------
$CMD \
  --region us \
  --revenue-growth-min 15 \
  --gross-margin-min 50 \
  --insider-min 5

# ---------------------------------------------------------------------------
# US-4. Technology sector deep screen (テックセクター精密スクリーン)
# Technologyセクターで成長・利益率・FCFを同時チェック
# ---------------------------------------------------------------------------
$CMD \
  --region us \
  --sector Technology \
  --revenue-growth-min 20 \
  --gross-margin-min 60 \
  --fcf-positive \
  --size 20

# ---------------------------------------------------------------------------
# US-5. NYSE value screen (NYSE割安スクリーン)
# PEG1.0以下, 有利子負債/EBITDA 5倍以下
# ---------------------------------------------------------------------------
$CMD \
  --exchange nyse \
  --peg-max 1.0 \
  --debt-ebitda-max 5

# ---------------------------------------------------------------------------
# WORKFLOW: screen → fetch detailed metrics
# Step 1 でティッカーを絞り、Step 2 で詳細指標を取得
# ---------------------------------------------------------------------------

# Step 1: screen candidates
TICKERS=$($CMD \
  --region jp \
  --roe-min 10 \
  --div-yield-min 1.5 \
  --div-growth-years 3 \
  | python3 -c "import json,sys; data=json.load(sys.stdin); print(' '.join(data['tickers']))")

# Step 2: fetch detailed metrics for candidates
FETCH="uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data"
$FETCH $TICKERS \
  --payout-ratio --equity-ratio --operating-margin --price-target --dividend-history

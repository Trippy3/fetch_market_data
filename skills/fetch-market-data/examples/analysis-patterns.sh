#!/usr/bin/env bash
# fetch-market-data — analysis pattern examples
#
# Requires: uv  (https://github.com/astral-sh/uv)
#
# Run any example directly — no local installation needed:
#   bash analysis-patterns.sh
#
# If you have the repository cloned, replace CMD with:
#   CMD="uv run fetch-market-data"

CMD="uvx --from git+https://github.com/Trippy3/fetch_market_data fetch-market-data"

# ---------------------------------------------------------------------------
# 1. Quick price check (default behaviour — no flags needed)
# ---------------------------------------------------------------------------
$CMD AAPL MSFT 7203.T

# ---------------------------------------------------------------------------
# 2. Valuation — is the stock cheap or expensive?
# ---------------------------------------------------------------------------
$CMD AAPL MSFT GOOGL \
  --price --trailing-pe --forward-pe --pbr --peg --ev-ebitda

# ---------------------------------------------------------------------------
# 3. Dividend income — sustainable income analysis
# ---------------------------------------------------------------------------
$CMD 7203.T 6758.T 9984.T \
  --price --dividend-yield --payout-ratio --dividend-growth

# ---------------------------------------------------------------------------
# 4. Growth quality — top-line and margin trend
# ---------------------------------------------------------------------------
$CMD NVDA AMZN META \
  --revenue --revenue-growth --operating-margin --gross-margin --fcf-margin

# ---------------------------------------------------------------------------
# 5. Financial health — balance sheet strength
# ---------------------------------------------------------------------------
$CMD AAPL 7203.T \
  --equity-ratio --debt-ebitda --cash --goodwill

# ---------------------------------------------------------------------------
# 6. Cash generation — how much real cash does the business produce?
# ---------------------------------------------------------------------------
$CMD AAPL MSFT \
  --operating-cf --fcf --fcf-margin --revenue

# ---------------------------------------------------------------------------
# 7. Shareholder returns — total capital return picture
# ---------------------------------------------------------------------------
$CMD AAPL MSFT \
  --dividend-yield --buyback --total-return-ratio --payout-ratio

# ---------------------------------------------------------------------------
# 8. Analyst consensus — what does the Street think?
# ---------------------------------------------------------------------------
$CMD TSLA NVDA \
  --price --price-target --ratings --eps-estimate --revenue-estimate

# ---------------------------------------------------------------------------
# 9. Event calendar — upcoming catalysts
# ---------------------------------------------------------------------------
$CMD AAPL MSFT \
  --next-earnings --guidance

# ---------------------------------------------------------------------------
# 10. Cross-market comparison — US vs Japan on the same metrics
# ---------------------------------------------------------------------------
$CMD AAPL 6758.T \
  --price --trailing-pe --pbr --roe --roa --dividend-yield

# ---------------------------------------------------------------------------
# 11. Insider activity — are insiders buying or selling?
# ---------------------------------------------------------------------------
$CMD AAPL \
  --insider-trades --major-holders

# ---------------------------------------------------------------------------
# 12. Full fundamental snapshot (combines multiple slow sources — slower)
# ---------------------------------------------------------------------------
$CMD AAPL \
  --price --market-cap \
  --trailing-pe --forward-pe --pbr --psr --ev-ebitda \
  --revenue --revenue-growth --operating-margin --gross-margin \
  --net-income --trailing-eps --forward-eps \
  --equity-ratio --debt-ebitda --cash \
  --operating-cf --fcf --fcf-margin \
  --roe --roa --beta \
  --dividend-yield --payout-ratio

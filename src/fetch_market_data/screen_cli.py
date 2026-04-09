from __future__ import annotations

import argparse
import json
import sys

from fetch_market_data.screener import ScreenParams, run_screen


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="screen-market-data",
        description=(
            "Screen stocks by financial metrics using yfinance EquityQuery. "
            "Returns matching ticker symbols as JSON."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Japanese stocks: ROE 10%+, dividend yield 1.5%+, 3+ years consecutive dividend growth
  screen-market-data --region jp --roe-min 10 --div-yield-min 1.5 --div-growth-years 3

  # US NASDAQ: revenue growth 15%+, gross margin 50%+, FCF positive
  screen-market-data --exchange nasdaq --revenue-growth-min 15 --gross-margin-min 50 --fcf-positive

  # US NYSE+NASDAQ Technology, insider ownership 5%+
  screen-market-data --region us --sector Technology --insider-min 5
        """,
    )

    # --- Market selection ---
    market_group = parser.add_argument_group("market selection (one required)")
    market_ex = market_group.add_mutually_exclusive_group(required=True)
    market_ex.add_argument(
        "--region",
        choices=["jp", "us"],
        help="Region: 'jp' (Japan/JPX) or 'us' (NYSE + NASDAQ)",
    )
    market_ex.add_argument(
        "--exchange",
        choices=["nasdaq", "nyse", "us"],
        help="Exchange: 'nasdaq' (NMS), 'nyse' (NYQ), 'us' (both)",
    )

    # --- Filter conditions ---
    filt = parser.add_argument_group("filter conditions")
    filt.add_argument("--roe-min", type=float, metavar="PCT",
                      help="Minimum ROE %% (e.g. 10 for 10%%%%)")
    filt.add_argument("--div-yield-min", type=float, metavar="PCT",
                      help="Minimum forward dividend yield %% (e.g. 1.5)")
    filt.add_argument("--div-growth-years", type=int, metavar="N",
                      help="Minimum consecutive years of dividend growth")
    filt.add_argument("--revenue-growth-min", type=float, metavar="PCT",
                      help="Minimum YoY revenue growth %% (e.g. 3)")
    filt.add_argument("--debt-ebitda-max", type=float, metavar="RATIO",
                      help="Maximum total debt / EBITDA ratio (e.g. 5)")
    filt.add_argument("--fcf-positive", action="store_true",
                      help="Require positive free cash flow (levered)")
    filt.add_argument("--gross-margin-min", type=float, metavar="PCT",
                      help="Minimum gross profit margin %% (e.g. 50)")
    filt.add_argument("--peg-max", type=float, metavar="RATIO",
                      help="Maximum PEG ratio (5-year, e.g. 1.0)")
    filt.add_argument("--insider-min", type=float, metavar="PCT",
                      help="Minimum insider ownership %% (e.g. 5)")
    filt.add_argument("--market-cap-min", type=float, metavar="VALUE",
                      help="Minimum market cap in base currency (JPY or USD)")
    filt.add_argument("--sector", metavar="SECTOR",
                      help=(
                          "Sector filter (e.g. Technology, Healthcare, Financials). "
                          "Use exact Yahoo Finance sector name."
                      ))

    # --- Output control ---
    out = parser.add_argument_group("output control")
    out.add_argument("--size", type=int, default=50, metavar="N",
                     help="Maximum number of results to return (default: 50)")
    out.add_argument("--sort-by", default="intradaymarketcap", metavar="FIELD",
                     help="EquityQuery field to sort by (default: intradaymarketcap)")
    out.add_argument("--sort-asc", action="store_true",
                     help="Sort ascending (default: descending)")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    params = ScreenParams(
        region=args.region,
        exchange=args.exchange,
        roe_min=args.roe_min,
        div_yield_min=args.div_yield_min,
        div_growth_years=args.div_growth_years,
        revenue_growth_min=args.revenue_growth_min,
        debt_ebitda_max=args.debt_ebitda_max,
        fcf_positive=args.fcf_positive,
        gross_margin_min=args.gross_margin_min,
        peg_max=args.peg_max,
        insider_min=args.insider_min,
        market_cap_min=args.market_cap_min,
        sector=args.sector,
        size=args.size,
        sort_by=args.sort_by,
        sort_asc=args.sort_asc,
    )

    try:
        result = run_screen(params)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())

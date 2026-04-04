from __future__ import annotations

import argparse
import json
import sys

from fetch_market_data.fetcher import DEFAULT_METRIC, SUPPORTED_METRICS, fetch_metrics

# argparse converts hyphens to underscores in dest names; pre-compute the mapping.
_METRIC_DEST = {m: m.replace("-", "_") for m in SUPPORTED_METRICS}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="fetch-market-data",
        description="Fetch market data for given ticker symbols",
    )
    parser.add_argument(
        "symbols",
        nargs="+",
        metavar="SYMBOL",
        help="Ticker symbol(s) to fetch (e.g. AAPL MSFT 7203.T)",
    )
    for metric in SUPPORTED_METRICS:
        parser.add_argument(
            f"--{metric}",
            action="store_true",
            default=False,
            help=f"Fetch {metric}",
        )
    args = parser.parse_args()

    active_metrics = [m for m, dest in _METRIC_DEST.items() if getattr(args, dest)]
    if not active_metrics:
        active_metrics = [DEFAULT_METRIC]

    results = fetch_metrics(args.symbols, active_metrics)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())

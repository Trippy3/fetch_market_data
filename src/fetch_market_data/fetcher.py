from __future__ import annotations

import math
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import yfinance as yf

try:
    import numpy as np

    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


def _stmt_latest(df: Any, *rows: str) -> Any:
    """Return the most recent annual value for the first matching row in a
    financial-statement DataFrame.  Tries each candidate row name in order."""
    if df is None or getattr(df, "empty", True):
        return None
    for row in rows:
        try:
            val = df.loc[row].iloc[0]
            if val is not None:
                return val
        except (KeyError, IndexError):
            continue
    return None


def _to_python(value: Any) -> Any:
    """Convert numpy/pandas scalars to JSON-serialisable Python types."""
    if value is None:
        return None
    if _HAS_NUMPY:
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            return None if np.isnan(value) else round(float(value), 4)
    if isinstance(value, float):
        return None if math.isnan(value) else round(value, 4)
    return value


@dataclass(frozen=True)
class MetricDef:
    source: str
    extract: Callable[[Any], Any]


_SOURCES: dict[str, Callable] = {
    "fast_info": lambda t: t.fast_info,
    "info": lambda t: t.info,
    "income_stmt": lambda t: t.income_stmt,
    "balance_sheet": lambda t: t.balance_sheet,
    "cashflow": lambda t: t.cashflow,
}

_METRICS: dict[str, MetricDef] = {
    # fast_info
    "price": MetricDef("fast_info", lambda d: d.last_price),
    "volume": MetricDef("fast_info", lambda d: d.last_volume),
    "avg-volume": MetricDef("fast_info", lambda d: d.three_month_average_volume),
    # info
    "week52-high": MetricDef("info", lambda d: d.get("fiftyTwoWeekHigh")),
    "week52-low": MetricDef("info", lambda d: d.get("fiftyTwoWeekLow")),
    "market-cap": MetricDef("info", lambda d: d.get("marketCap")),
    "trailing-pe": MetricDef("info", lambda d: d.get("trailingPE")),
    "forward-pe": MetricDef("info", lambda d: d.get("forwardPE")),
    "pbr": MetricDef("info", lambda d: d.get("priceToBook")),
    "psr": MetricDef("info", lambda d: d.get("priceToSalesTrailing12Months")),
    "ev-ebitda": MetricDef("info", lambda d: d.get("enterpriseToEbitda")),
    "peg": MetricDef("info", lambda d: d.get("pegRatio")),
    "dividend-yield": MetricDef("info", lambda d: d.get("dividendYield")),
    "payout-ratio": MetricDef("info", lambda d: d.get("payoutRatio")),
    "trailing-eps": MetricDef("info", lambda d: d.get("trailingEps")),
    "forward-eps": MetricDef("info", lambda d: d.get("forwardEps")),
    "roe": MetricDef("info", lambda d: d.get("returnOnEquity")),
    "roa": MetricDef("info", lambda d: d.get("returnOnAssets")),
    "beta": MetricDef("info", lambda d: d.get("beta")),
    "fcf": MetricDef("info", lambda d: d.get("freeCashflow")),
    # income_stmt
    "revenue": MetricDef("income_stmt", lambda d: _stmt_latest(d, "Total Revenue")),
    "operating-income": MetricDef("income_stmt", lambda d: _stmt_latest(d, "Operating Income")),
    "net-income": MetricDef("income_stmt", lambda d: _stmt_latest(d, "Net Income")),
    # balance_sheet
    "cash": MetricDef(
        "balance_sheet",
        lambda d: _stmt_latest(
            d, "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"
        ),
    ),
    "goodwill": MetricDef(
        "balance_sheet",
        lambda d: _stmt_latest(d, "Goodwill", "Goodwill And Other Intangible Assets"),
    ),
    "intangible-assets": MetricDef(
        "balance_sheet",
        lambda d: _stmt_latest(
            d,
            "Other Intangible Assets",
            "Intangible Assets",
            "Goodwill And Other Intangible Assets",
        ),
    ),
    # cashflow
    "operating-cf": MetricDef(
        "cashflow",
        lambda d: _stmt_latest(d, "Operating Cash Flow", "Cash Flows From Operations"),
    ),
}

SUPPORTED_METRICS: list[str] = list(_METRICS.keys())
DEFAULT_METRIC = "price"


def _is_japanese(symbol: str) -> bool:
    return symbol.endswith(".T")


def _failed_entry(metrics: list[str], error: str) -> dict[str, Any]:
    entry = {m: None for m in metrics}
    entry["currency"] = None
    entry["error"] = error
    return entry


def fetch_metrics(symbols: list[str], metrics: list[str]) -> dict[str, dict]:
    """Fetch the requested metrics for each symbol.

    Returns a dict keyed by symbol::

        {
            "AAPL":   {"price": 255.92, "market-cap": 3920000000000, "currency": "USD", "error": null},
            "7203.T": {"price": 3255.0,                              "currency": "JPY", "error": null},
        }

    Only the sources required by the requested metrics are fetched per ticker,
    and each source is fetched at most once per ticker.
    """
    for metric in metrics:
        if metric not in _METRICS:
            raise ValueError(f"Unsupported metric: {metric!r}. Choose from: {SUPPORTED_METRICS}")

    if not symbols:
        return {}

    sources_needed = {_METRICS[m].source for m in metrics}
    results: dict[str, dict] = {}
    tickers = yf.Tickers(" ".join(symbols))

    for symbol in symbols:
        symbol_upper = symbol.upper()
        try:
            ticker = tickers.tickers.get(symbol_upper)
            if ticker is None:
                results[symbol] = _failed_entry(metrics, "Ticker not found")
                continue

            source_data: dict[str, Any] = {}
            first_error: str | None = None
            for source in sources_needed:
                try:
                    source_data[source] = _SOURCES[source](ticker)
                except Exception as exc:
                    print(f"[warn] {symbol} source={source}: {exc}", file=sys.stderr)
                    source_data[source] = None
                    if first_error is None:
                        first_error = str(exc)

            currency = "JPY" if _is_japanese(symbol_upper) else "USD"
            entry: dict[str, Any] = {"currency": currency, "error": first_error}

            for metric in metrics:
                defn = _METRICS[metric]
                data = source_data.get(defn.source)
                try:
                    raw = defn.extract(data) if data is not None else None
                    entry[metric] = _to_python(raw)
                except Exception as exc:
                    print(f"[warn] {symbol} metric={metric}: {exc}", file=sys.stderr)
                    entry[metric] = None

            results[symbol] = entry

        except Exception as exc:
            print(f"[warn] {symbol}: {exc}", file=sys.stderr)
            results[symbol] = _failed_entry(metrics, str(exc))

    return results

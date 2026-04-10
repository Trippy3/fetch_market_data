from __future__ import annotations

import datetime
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

try:
    import pandas as pd

    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False


# ---------------------------------------------------------------------------
# Data-extraction helpers
# ---------------------------------------------------------------------------


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


def _stmt_yoy_growth(df: Any, *rows: str) -> Any:
    """YoY growth for a financial-statement row: (current - previous) / abs(previous).

    Tries each candidate row name in order.  Returns None when fewer than two
    periods are available or the previous period is zero.
    """
    if df is None or getattr(df, "empty", True):
        return None
    for row in rows:
        try:
            series = df.loc[row]
            if len(series) < 2:
                return None
            current, previous = series.iloc[0], series.iloc[1]
            if previous is None or previous == 0:
                return None
            return (current - previous) / abs(previous)
        except (KeyError, IndexError):
            continue
    return None


def _stmt_ratio(df: Any, numerator_row: str, denominator_row: str) -> Any:
    """Ratio of two rows from the same financial statement (latest period)."""
    num = _stmt_latest(df, numerator_row)
    den = _stmt_latest(df, denominator_row)
    if num is None or den is None or den == 0:
        return None
    return num / den


def _history_change(df: Any, pct: bool = False) -> Any:
    """Compute price change between first and last Close in a history DataFrame.

    Returns the absolute change when *pct* is False, or the relative change
    (as a fraction) when *pct* is True.  Returns None when fewer than two
    rows are present or the base price is zero.
    """
    if df is None or getattr(df, "empty", True) or len(df) < 2:
        return None
    try:
        first = df["Close"].iloc[0]
        last = df["Close"].iloc[-1]
        diff = last - first
        if pct:
            return None if first == 0 else diff / first
        return diff
    except (KeyError, IndexError, TypeError):
        return None


def _cross_debt_ebitda(bs: Any, inc: Any) -> Any:
    """Total Debt / EBITDA (Operating Income + Depreciation & Amortization)."""
    debt = _stmt_latest(bs, "Total Debt", "Long Term Debt And Capital Lease Obligation")
    op_income = _stmt_latest(inc, "Operating Income", "EBIT")
    da = _stmt_latest(
        inc,
        "Reconciled Depreciation",
        "Depreciation And Amortization",
        "Depreciation",
    )
    if debt is None or op_income is None:
        return None
    ebitda = op_income + (da or 0)
    if ebitda == 0:
        return None
    return debt / ebitda


def _cross_fcf_margin(info: Any, inc: Any) -> Any:
    """Free Cash Flow / Total Revenue."""
    fcf = info.get("freeCashflow") if isinstance(info, dict) else None
    revenue = _stmt_latest(inc, "Total Revenue")
    if fcf is None or revenue is None or revenue == 0:
        return None
    return fcf / revenue


def _dividend_growth(dividends: Any) -> Any:
    """Year-over-year growth of the annual dividend total (fraction)."""
    if dividends is None or getattr(dividends, "empty", True):
        return None
    try:
        annual = dividends.resample("YE").sum()
        if len(annual) < 2:
            return None
        current, previous = annual.iloc[-1], annual.iloc[-2]
        if previous == 0:
            return None
        return (current - previous) / abs(previous)
    except Exception:
        return None


def _total_return_ratio(dividends: Any, cf: Any, inc: Any) -> Any:
    """(total annual dividends + abs(buyback)) / net_income."""
    total_div: float = 0.0
    if dividends is not None and not getattr(dividends, "empty", True):
        try:
            annual = dividends.resample("YE").sum()
            if len(annual) > 0:
                total_div = float(annual.iloc[-1])
        except Exception:
            pass
    buyback_val = _stmt_latest(cf, "Repurchase Of Capital Stock")
    buyback_abs = abs(float(buyback_val)) if buyback_val is not None else 0.0
    net_inc = _stmt_latest(inc, "Net Income")
    if net_inc is None or net_inc == 0:
        return None
    return (total_div + buyback_abs) / net_inc


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------


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


def _to_json_safe(value: Any) -> Any:
    """Recursively convert any value (scalar, DataFrame, Series, dict, list)
    to a JSON-serialisable Python structure."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if _HAS_PANDAS:
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        if isinstance(value, pd.DataFrame):
            records = value.reset_index().to_dict(orient="records")
            return [{k: _to_json_safe(v) for k, v in row.items()} for row in records]
        if isinstance(value, pd.Series):
            return {str(k): _to_json_safe(v) for k, v in value.items()}
    if _HAS_NUMPY:
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            return None if np.isnan(value) else round(float(value), 4)
    if isinstance(value, float):
        return None if math.isnan(value) else round(value, 4)
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(v) for v in value]
    return value


# ---------------------------------------------------------------------------
# Metric registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MetricDef:
    sources: tuple[str, ...]
    extract: Callable[..., Any]


_SOURCES: dict[str, Callable] = {
    "fast_info": lambda t: t.fast_info,
    "info": lambda t: t.info,
    "income_stmt": lambda t: t.income_stmt,
    "balance_sheet": lambda t: t.balance_sheet,
    "cashflow": lambda t: t.cashflow,
    # price history (different periods are distinct source keys)
    "history_2d": lambda t: t.history(period="2d"),
    "history_5d": lambda t: t.history(period="5d"),
    "history_1mo": lambda t: t.history(period="1mo"),
    # shareholder / analyst data
    "dividends": lambda t: t.dividends,
    "calendar": lambda t: t.calendar,
    "earnings_estimate": lambda t: t.earnings_estimate,
    "revenue_estimate": lambda t: t.revenue_estimate,
    "analyst_price_targets": lambda t: t.analyst_price_targets,
    "recommendations_summary": lambda t: t.recommendations_summary,
    "insider_transactions": lambda t: t.insider_transactions,
    "major_holders": lambda t: t.major_holders,
}

_METRICS: dict[str, MetricDef] = {
    # --- fast_info ---
    "price": MetricDef(("fast_info",), lambda d: d.last_price),
    "volume": MetricDef(("fast_info",), lambda d: d.last_volume),
    "avg-volume": MetricDef(("fast_info",), lambda d: d.three_month_average_volume),
    # --- info ---
    "week52-high": MetricDef(("info",), lambda d: d.get("fiftyTwoWeekHigh")),
    "week52-low": MetricDef(("info",), lambda d: d.get("fiftyTwoWeekLow")),
    "market-cap": MetricDef(("info",), lambda d: d.get("marketCap")),
    "trailing-pe": MetricDef(("info",), lambda d: d.get("trailingPE")),
    "forward-pe": MetricDef(("info",), lambda d: d.get("forwardPE")),
    "pbr": MetricDef(("info",), lambda d: d.get("priceToBook")),
    "psr": MetricDef(("info",), lambda d: d.get("priceToSalesTrailing12Months")),
    "ev-ebitda": MetricDef(("info",), lambda d: d.get("enterpriseToEbitda")),
    "peg": MetricDef(("info",), lambda d: d.get("pegRatio")),
    "dividend-yield": MetricDef(("info",), lambda d: d.get("dividendYield")),
    "payout-ratio": MetricDef(("info",), lambda d: d.get("payoutRatio")),
    "trailing-eps": MetricDef(("info",), lambda d: d.get("trailingEps")),
    "forward-eps": MetricDef(("info",), lambda d: d.get("forwardEps")),
    "roe": MetricDef(("info",), lambda d: d.get("returnOnEquity")),
    "roa": MetricDef(("info",), lambda d: d.get("returnOnAssets")),
    "beta": MetricDef(("info",), lambda d: d.get("beta")),
    "fcf": MetricDef(("info",), lambda d: d.get("freeCashflow")),
    # --- income_stmt ---
    "revenue": MetricDef(("income_stmt",), lambda d: _stmt_latest(d, "Total Revenue")),
    "operating-income": MetricDef(("income_stmt",), lambda d: _stmt_latest(d, "Operating Income")),
    "net-income": MetricDef(("income_stmt",), lambda d: _stmt_latest(d, "Net Income")),
    # --- balance_sheet ---
    "cash": MetricDef(
        ("balance_sheet",),
        lambda d: _stmt_latest(
            d, "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"
        ),
    ),
    "goodwill": MetricDef(
        ("balance_sheet",),
        lambda d: _stmt_latest(d, "Goodwill", "Goodwill And Other Intangible Assets"),
    ),
    "intangible-assets": MetricDef(
        ("balance_sheet",),
        lambda d: _stmt_latest(
            d,
            "Other Intangible Assets",
            "Intangible Assets",
            "Goodwill And Other Intangible Assets",
        ),
    ),
    # --- cashflow ---
    "operating-cf": MetricDef(
        ("cashflow",),
        lambda d: _stmt_latest(d, "Operating Cash Flow", "Cash Flows From Operations"),
    ),
    # --- Group A: price history ---
    "price-change": MetricDef(("history_2d",), lambda d: _history_change(d, pct=False)),
    "price-change-pct": MetricDef(("history_2d",), lambda d: _history_change(d, pct=True)),
    "weekly-change": MetricDef(("history_5d",), lambda d: _history_change(d, pct=True)),
    "monthly-change": MetricDef(("history_1mo",), lambda d: _history_change(d, pct=True)),
    # --- Group B: income statement calculations ---
    "revenue-growth": MetricDef(
        ("income_stmt",), lambda d: _stmt_yoy_growth(d, "Total Revenue")
    ),
    # TTM revenue growth from info (same data source as screen-market-data's EquityQuery field
    # totalrevenues1yrgrowth.lasttwelvemonths — use this for apples-to-apples comparison)
    "revenue-growth-ttm": MetricDef(("info",), lambda d: d.get("revenueGrowth")),
    "operating-margin": MetricDef(
        ("income_stmt",), lambda d: _stmt_ratio(d, "Operating Income", "Total Revenue")
    ),
    "gross-margin": MetricDef(
        ("income_stmt",), lambda d: _stmt_ratio(d, "Gross Profit", "Total Revenue")
    ),
    # --- Group C: cross-statement calculations ---
    "equity-ratio": MetricDef(
        ("balance_sheet",),
        lambda d: _stmt_ratio(d, "Stockholders Equity", "Total Assets"),
    ),
    "debt-ebitda": MetricDef(("balance_sheet", "income_stmt"), _cross_debt_ebitda),
    "fcf-margin": MetricDef(("info", "income_stmt"), _cross_fcf_margin),
    # --- Group D: cashflow lookup ---
    "buyback": MetricDef(
        ("cashflow",),
        lambda d: _stmt_latest(d, "Repurchase Of Capital Stock"),
    ),
    # --- Group E: shareholder return calculations ---
    "dividend-history": MetricDef(("dividends",), lambda d: d),
    "dividend-growth": MetricDef(("dividends",), _dividend_growth),
    "total-return-ratio": MetricDef(
        ("dividends", "cashflow", "income_stmt"), _total_return_ratio
    ),
    # --- Group F: structured analyst / event data ---
    "guidance": MetricDef(("calendar",), lambda d: d),
    "eps-estimate": MetricDef(("earnings_estimate",), lambda d: d),
    "revenue-estimate": MetricDef(("revenue_estimate",), lambda d: d),
    "price-target": MetricDef(("analyst_price_targets",), lambda d: d),
    "ratings": MetricDef(("recommendations_summary",), lambda d: d),
    "next-earnings": MetricDef(
        ("calendar",),
        lambda d: d.get("Earnings Date") if isinstance(d, dict) else None,
    ),
    "insider-trades": MetricDef(("insider_transactions",), lambda d: d),
    "major-holders": MetricDef(("major_holders",), lambda d: d),
}

SUPPORTED_METRICS: list[str] = list(_METRICS.keys())
DEFAULT_METRIC = "price"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


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

    sources_needed = {s for m in metrics for s in _METRICS[m].sources}
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
                args = [source_data.get(s) for s in defn.sources]
                try:
                    raw = defn.extract(*args) if any(a is not None for a in args) else None
                    entry[metric] = _to_json_safe(raw)
                except Exception as exc:
                    print(f"[warn] {symbol} metric={metric}: {exc}", file=sys.stderr)
                    entry[metric] = None

            results[symbol] = entry

        except Exception as exc:
            print(f"[warn] {symbol}: {exc}", file=sys.stderr)
            results[symbol] = _failed_entry(metrics, str(exc))

    return results

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yfinance as yf
from yfinance import EquityQuery

# ---------------------------------------------------------------------------
# Exchange code mapping
# ---------------------------------------------------------------------------

_EXCHANGE_CODES: dict[str, list[str]] = {
    "nasdaq": ["NMS"],
    "nyse": ["NYQ"],
    "us": ["NMS", "NYQ"],
}

_REGION_CODES: dict[str, str] = {
    "jp": "jp",
    "us": "us",
}

# ---------------------------------------------------------------------------
# Screen parameters dataclass
# ---------------------------------------------------------------------------


@dataclass
class ScreenParams:
    """Parameters for equity screening."""

    # Market selection (one of region or exchange must be set)
    region: str | None = None          # "jp" or "us"
    exchange: str | None = None        # "nasdaq", "nyse", "us"

    # Filter conditions
    roe_min: float | None = None
    div_yield_min: float | None = None
    div_growth_years: int | None = None
    revenue_growth_min: float | None = None
    debt_ebitda_max: float | None = None
    fcf_positive: bool = False
    gross_margin_min: float | None = None
    peg_max: float | None = None
    insider_min: float | None = None
    market_cap_min: float | None = None  # in base currency units (JPY/USD)
    sector: str | None = None

    # Output control
    size: int = 50
    offset: int = 0
    sort_by: str = "intradaymarketcap"
    sort_asc: bool = False

    # Collected unknown conditions (for future extension)
    extra: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Query builder
# ---------------------------------------------------------------------------


def _build_query(params: ScreenParams) -> EquityQuery:
    """Build an EquityQuery from ScreenParams. Raises ValueError on invalid input."""
    conditions: list[EquityQuery] = []

    # --- Market filter ---
    if params.exchange is not None:
        codes = _EXCHANGE_CODES.get(params.exchange.lower())
        if codes is None:
            raise ValueError(
                f"Unknown exchange '{params.exchange}'. "
                f"Choices: {', '.join(_EXCHANGE_CODES)}"
            )
        conditions.append(EquityQuery("is-in", ["exchange", *codes]))
    elif params.region is not None:
        region_code = _REGION_CODES.get(params.region.lower())
        if region_code is None:
            raise ValueError(
                f"Unknown region '{params.region}'. "
                f"Choices: {', '.join(_REGION_CODES)}"
            )
        conditions.append(EquityQuery("eq", ["region", region_code]))
    else:
        raise ValueError("Either --region or --exchange must be specified.")

    # --- Sector ---
    if params.sector is not None:
        conditions.append(EquityQuery("eq", ["sector", params.sector]))

    # --- Profitability ---
    if params.roe_min is not None:
        conditions.append(
            EquityQuery("gte", ["returnonequity.lasttwelvemonths", params.roe_min])
        )
    if params.gross_margin_min is not None:
        conditions.append(
            EquityQuery("gte", ["grossprofitmargin.lasttwelvemonths", params.gross_margin_min])
        )

    # --- Dividend ---
    if params.div_yield_min is not None:
        conditions.append(
            EquityQuery("gte", ["forward_dividend_yield", params.div_yield_min])
        )
    if params.div_growth_years is not None:
        conditions.append(
            EquityQuery(
                "gte",
                ["consecutive_years_of_dividend_growth_count", params.div_growth_years],
            )
        )

    # --- Growth ---
    if params.revenue_growth_min is not None:
        conditions.append(
            EquityQuery(
                "gte",
                ["totalrevenues1yrgrowth.lasttwelvemonths", params.revenue_growth_min],
            )
        )

    # --- Cash flow ---
    if params.fcf_positive:
        conditions.append(
            EquityQuery("gt", ["leveredfreecashflow.lasttwelvemonths", 0])
        )

    # --- Leverage ---
    if params.debt_ebitda_max is not None:
        conditions.append(
            EquityQuery("lte", ["totaldebtebitda.lasttwelvemonths", params.debt_ebitda_max])
        )

    # --- Valuation ---
    if params.peg_max is not None:
        conditions.append(EquityQuery("lte", ["pegratio_5y", params.peg_max]))

    # --- Ownership ---
    if params.insider_min is not None:
        conditions.append(EquityQuery("gte", ["pctheldinsider", params.insider_min]))

    # --- Market cap ---
    if params.market_cap_min is not None:
        conditions.append(
            EquityQuery("gte", ["intradaymarketcap", params.market_cap_min])
        )

    if len(conditions) == 1:
        return conditions[0]
    return EquityQuery("and", conditions)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_screen(params: ScreenParams) -> dict[str, Any]:
    """Execute screening and return structured result dict.

    Returns:
        {
            "query": {"region": ..., "exchange": ..., "conditions": {...}},
            "count": int,
            "tickers": [str, ...]
        }
    """
    query = _build_query(params)

    response = yf.screen(
        query,
        sortField=params.sort_by,
        sortAsc=params.sort_asc,
        size=params.size,
        offset=params.offset,
        count=True,
    )

    quotes: list[dict[str, Any]] = response.get("quotes", [])
    tickers = [q["symbol"] for q in quotes if "symbol" in q]
    total: int | None = response.get("total")

    conditions: dict[str, Any] = {}
    if params.roe_min is not None:
        conditions["roe_min"] = params.roe_min
    if params.div_yield_min is not None:
        conditions["div_yield_min"] = params.div_yield_min
    if params.div_growth_years is not None:
        conditions["div_growth_years"] = params.div_growth_years
    if params.revenue_growth_min is not None:
        conditions["revenue_growth_min"] = params.revenue_growth_min
    if params.debt_ebitda_max is not None:
        conditions["debt_ebitda_max"] = params.debt_ebitda_max
    if params.fcf_positive:
        conditions["fcf_positive"] = True
    if params.gross_margin_min is not None:
        conditions["gross_margin_min"] = params.gross_margin_min
    if params.peg_max is not None:
        conditions["peg_max"] = params.peg_max
    if params.insider_min is not None:
        conditions["insider_min"] = params.insider_min
    if params.market_cap_min is not None:
        conditions["market_cap_min"] = params.market_cap_min
    if params.sector is not None:
        conditions["sector"] = params.sector

    result: dict[str, Any] = {
        "query": {
            "region": params.region,
            "exchange": params.exchange,
            "offset": params.offset,
            "conditions": conditions,
        },
        "total": total,
        "count": len(tickers),
        "tickers": tickers,
    }
    return result

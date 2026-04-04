from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

import pandas as pd
import pytest

from fetch_market_data.fetcher import fetch_metrics

# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _make_fast_info(last_price=172.45, last_volume=50_000_000, avg_volume=45_000_000):
    fi = MagicMock()
    fi.last_price = last_price
    fi.last_volume = last_volume
    fi.three_month_average_volume = avg_volume
    return fi


def _make_info(**kwargs):
    defaults = {
        "fiftyTwoWeekHigh": 200.0,
        "fiftyTwoWeekLow": 130.0,
        "marketCap": 2_700_000_000_000,
        "trailingPE": 28.5,
        "forwardPE": 25.0,
        "priceToBook": 45.0,
        "priceToSalesTrailing12Months": 8.5,
        "enterpriseToEbitda": 22.0,
        "pegRatio": 2.1,
        "dividendYield": 0.0055,
        "payoutRatio": 0.15,
        "trailingEps": 6.43,
        "forwardEps": 7.20,
        "returnOnEquity": 1.47,
        "returnOnAssets": 0.28,
        "beta": 1.24,
        "freeCashflow": 90_000_000_000,
    }
    defaults.update(kwargs)
    return defaults


def _make_stmt_df(row: str, value) -> pd.DataFrame:
    """Create a minimal financial-statement DataFrame with one row and one column."""
    import numpy as np

    return pd.DataFrame({pd.Timestamp("2024-09-30"): [np.int64(value)]}, index=[row])


def _make_ticker(
    fast_info=None,
    info=None,
    income_stmt=None,
    balance_sheet=None,
    cashflow=None,
):
    t = MagicMock()
    t.fast_info = fast_info or _make_fast_info()
    t.info = info if info is not None else _make_info()
    t.income_stmt = income_stmt if income_stmt is not None else pd.DataFrame()
    t.balance_sheet = balance_sheet if balance_sheet is not None else pd.DataFrame()
    t.cashflow = cashflow if cashflow is not None else pd.DataFrame()
    return t


def _make_tickers(symbol_map: dict[str, MagicMock]) -> MagicMock:
    mock = MagicMock()
    mock.tickers = symbol_map
    return mock


# ---------------------------------------------------------------------------
# Tests: empty / error cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_symbols_returns_empty(self):
        assert fetch_metrics([], ["price"]) == {}

    def test_unsupported_metric_raises(self):
        with pytest.raises(ValueError, match="Unsupported metric"):
            fetch_metrics(["AAPL"], ["unknown"])

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_ticker_not_found_returns_error(self, mock_cls):
        mock_cls.return_value = _make_tickers({})
        result = fetch_metrics(["NOTEXIST"], ["price"])
        assert result["NOTEXIST"]["price"] is None
        assert "not found" in result["NOTEXIST"]["error"].lower()

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_source_exception_sets_metric_to_none(self, mock_cls):
        ticker = MagicMock()
        type(ticker).fast_info = PropertyMock(side_effect=RuntimeError("network error"))
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["price"])
        assert result["AAPL"]["price"] is None
        assert result["AAPL"]["error"] is not None


# ---------------------------------------------------------------------------
# Tests: fast_info source
# ---------------------------------------------------------------------------


class TestFastInfoMetrics:
    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_price(self, mock_cls):
        mock_cls.return_value = _make_tickers({"AAPL": _make_ticker()})
        result = fetch_metrics(["AAPL"], ["price"])
        assert result["AAPL"]["price"] == 172.45
        assert result["AAPL"]["currency"] == "USD"

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_volume(self, mock_cls):
        mock_cls.return_value = _make_tickers({"AAPL": _make_ticker()})
        result = fetch_metrics(["AAPL"], ["volume"])
        assert result["AAPL"]["volume"] == 50_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_avg_volume(self, mock_cls):
        mock_cls.return_value = _make_tickers({"AAPL": _make_ticker()})
        result = fetch_metrics(["AAPL"], ["avg-volume"])
        assert result["AAPL"]["avg-volume"] == 45_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_japanese_stock_currency_jpy(self, mock_cls):
        mock_cls.return_value = _make_tickers({"7203.T": _make_ticker(_make_fast_info(3255.0))})
        result = fetch_metrics(["7203.T"], ["price"])
        assert result["7203.T"]["currency"] == "JPY"


# ---------------------------------------------------------------------------
# Tests: info source
# ---------------------------------------------------------------------------


class TestInfoMetrics:
    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_week52_high_low(self, mock_cls):
        mock_cls.return_value = _make_tickers({"AAPL": _make_ticker()})
        result = fetch_metrics(["AAPL"], ["week52-high", "week52-low"])
        assert result["AAPL"]["week52-high"] == 200.0
        assert result["AAPL"]["week52-low"] == 130.0

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_market_cap(self, mock_cls):
        mock_cls.return_value = _make_tickers({"AAPL": _make_ticker()})
        result = fetch_metrics(["AAPL"], ["market-cap"])
        assert result["AAPL"]["market-cap"] == 2_700_000_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_valuation_metrics(self, mock_cls):
        mock_cls.return_value = _make_tickers({"AAPL": _make_ticker()})
        result = fetch_metrics(
            ["AAPL"], ["trailing-pe", "forward-pe", "pbr", "psr", "ev-ebitda", "peg"]
        )
        assert result["AAPL"]["trailing-pe"] == 28.5
        assert result["AAPL"]["forward-pe"] == 25.0
        assert result["AAPL"]["pbr"] == 45.0
        assert result["AAPL"]["psr"] == 8.5
        assert result["AAPL"]["ev-ebitda"] == 22.0
        assert result["AAPL"]["peg"] == 2.1

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_dividend_metrics(self, mock_cls):
        mock_cls.return_value = _make_tickers({"AAPL": _make_ticker()})
        result = fetch_metrics(["AAPL"], ["dividend-yield", "payout-ratio"])
        assert result["AAPL"]["dividend-yield"] == round(0.0055, 4)
        assert result["AAPL"]["payout-ratio"] == round(0.15, 4)

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_eps_metrics(self, mock_cls):
        mock_cls.return_value = _make_tickers({"AAPL": _make_ticker()})
        result = fetch_metrics(["AAPL"], ["trailing-eps", "forward-eps"])
        assert result["AAPL"]["trailing-eps"] == 6.43
        assert result["AAPL"]["forward-eps"] == 7.20

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_roe_roa_beta_fcf(self, mock_cls):
        mock_cls.return_value = _make_tickers({"AAPL": _make_ticker()})
        result = fetch_metrics(["AAPL"], ["roe", "roa", "beta", "fcf"])
        assert result["AAPL"]["roe"] == round(1.47, 4)
        assert result["AAPL"]["roa"] == round(0.28, 4)
        assert result["AAPL"]["beta"] == round(1.24, 4)
        assert result["AAPL"]["fcf"] == 90_000_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_missing_info_key_returns_none(self, mock_cls):
        ticker = _make_ticker(info={})  # empty info dict
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["trailing-pe"])
        assert result["AAPL"]["trailing-pe"] is None


# ---------------------------------------------------------------------------
# Tests: financial statement sources
# ---------------------------------------------------------------------------


class TestFinancialStatementMetrics:
    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_revenue(self, mock_cls):
        stmt = _make_stmt_df("Total Revenue", 391_035_000_000)
        ticker = _make_ticker(income_stmt=stmt)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["revenue"])
        assert result["AAPL"]["revenue"] == 391_035_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_operating_income(self, mock_cls):
        stmt = _make_stmt_df("Operating Income", 114_301_000_000)
        ticker = _make_ticker(income_stmt=stmt)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["operating-income"])
        assert result["AAPL"]["operating-income"] == 114_301_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_net_income(self, mock_cls):
        stmt = _make_stmt_df("Net Income", 96_995_000_000)
        ticker = _make_ticker(income_stmt=stmt)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["net-income"])
        assert result["AAPL"]["net-income"] == 96_995_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_cash(self, mock_cls):
        bs = _make_stmt_df("Cash And Cash Equivalents", 29_965_000_000)
        ticker = _make_ticker(balance_sheet=bs)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["cash"])
        assert result["AAPL"]["cash"] == 29_965_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_goodwill(self, mock_cls):
        bs = _make_stmt_df("Goodwill", 67_000_000_000)
        ticker = _make_ticker(balance_sheet=bs)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["goodwill"])
        assert result["AAPL"]["goodwill"] == 67_000_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_operating_cf(self, mock_cls):
        cf = _make_stmt_df("Operating Cash Flow", 118_254_000_000)
        ticker = _make_ticker(cashflow=cf)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["operating-cf"])
        assert result["AAPL"]["operating-cf"] == 118_254_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_empty_dataframe_returns_none(self, mock_cls):
        ticker = _make_ticker(income_stmt=pd.DataFrame())
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["revenue"])
        assert result["AAPL"]["revenue"] is None


# ---------------------------------------------------------------------------
# Tests: multi-source / multi-symbol
# ---------------------------------------------------------------------------


class TestMultiSourceAndSymbol:
    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_multiple_sources_in_one_call(self, mock_cls):
        stmt = _make_stmt_df("Total Revenue", 391_035_000_000)
        ticker = _make_ticker(income_stmt=stmt)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["price", "market-cap", "revenue"])
        assert result["AAPL"]["price"] == 172.45
        assert result["AAPL"]["market-cap"] == 2_700_000_000_000
        assert result["AAPL"]["revenue"] == 391_035_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_multiple_symbols(self, mock_cls):
        mock_cls.return_value = _make_tickers(
            {
                "AAPL": _make_ticker(),
                "7203.T": _make_ticker(_make_fast_info(3255.0)),
            }
        )
        result = fetch_metrics(["AAPL", "7203.T"], ["price"])
        assert result["AAPL"]["currency"] == "USD"
        assert result["7203.T"]["currency"] == "JPY"

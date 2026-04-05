"""Tests for the calculated metrics added in Phase 2-6."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from fetch_market_data.fetcher import (
    _cross_debt_ebitda,
    _cross_fcf_margin,
    _dividend_growth,
    _history_change,
    _stmt_ratio,
    _stmt_yoy_growth,
    _to_json_safe,
    _total_return_ratio,
    fetch_metrics,
)


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _make_history_df(closes: list[float]) -> pd.DataFrame:
    """Build a minimal history DataFrame with the given Close prices."""
    dates = pd.date_range("2024-01-01", periods=len(closes), freq="D")
    return pd.DataFrame({"Close": closes}, index=dates)


def _make_2col_stmt(row: str, recent: float, prev: float) -> pd.DataFrame:
    """Build a 2-column financial-statement DataFrame (two annual periods)."""
    return pd.DataFrame(
        {
            pd.Timestamp("2024-09-30"): [np.int64(recent)],
            pd.Timestamp("2023-09-30"): [np.int64(prev)],
        },
        index=[row],
    )


def _make_stmt_df(row: str, value: float) -> pd.DataFrame:
    return pd.DataFrame({pd.Timestamp("2024-09-30"): [np.int64(value)]}, index=[row])


def _make_ticker(**overrides) -> MagicMock:
    t = MagicMock()
    t.fast_info = MagicMock(last_price=172.45)
    t.info = {"freeCashflow": 90_000_000_000}
    t.income_stmt = pd.DataFrame()
    t.balance_sheet = pd.DataFrame()
    t.cashflow = pd.DataFrame()
    t.dividends = pd.Series(dtype=float)
    t.calendar = {}
    for attr, val in overrides.items():
        setattr(t, attr, val)
    return t


def _make_tickers(symbol_map: dict) -> MagicMock:
    mock = MagicMock()
    mock.tickers = symbol_map
    return mock


# ---------------------------------------------------------------------------
# _to_json_safe
# ---------------------------------------------------------------------------


class TestToJsonSafe:
    def test_none_returns_none(self):
        assert _to_json_safe(None) is None

    def test_float_rounded(self):
        assert _to_json_safe(1.23456789) == 1.2346

    def test_nan_returns_none(self):
        assert _to_json_safe(float("nan")) is None

    def test_numpy_integer(self):
        assert _to_json_safe(np.int64(42)) == 42
        assert isinstance(_to_json_safe(np.int64(42)), int)

    def test_numpy_float_nan(self):
        assert _to_json_safe(np.float64("nan")) is None

    def test_dict_recursive(self):
        result = _to_json_safe({"a": 1.23456, "b": None})
        assert result["a"] == 1.2346
        assert result["b"] is None

    def test_list_recursive(self):
        result = _to_json_safe([1.0, None, np.int64(5)])
        assert result == [1.0, None, 5]

    def test_dataframe_to_records(self):
        df = pd.DataFrame({"col": [1, 2]})
        result = _to_json_safe(df)
        assert isinstance(result, list)
        assert result[0]["col"] == 1

    def test_series_to_dict(self):
        s = pd.Series({"a": 1.0, "b": 2.0})
        result = _to_json_safe(s)
        assert result["a"] == 1.0
        assert result["b"] == 2.0

    def test_timestamp_to_isoformat(self):
        ts = pd.Timestamp("2024-01-15")
        result = _to_json_safe(ts)
        assert result == "2024-01-15T00:00:00"

    def test_string_passthrough(self):
        assert _to_json_safe("hello") == "hello"

    def test_int_passthrough(self):
        assert _to_json_safe(42) == 42


# ---------------------------------------------------------------------------
# _history_change
# ---------------------------------------------------------------------------


class TestHistoryChange:
    def test_absolute_change(self):
        df = _make_history_df([100.0, 105.0])
        assert _history_change(df, pct=False) == 5.0

    def test_percent_change(self):
        df = _make_history_df([100.0, 110.0])
        result = _history_change(df, pct=True)
        assert abs(result - 0.1) < 1e-9

    def test_negative_change(self):
        df = _make_history_df([100.0, 90.0])
        assert _history_change(df, pct=False) == -10.0

    def test_zero_base_pct_returns_none(self):
        df = _make_history_df([0.0, 10.0])
        assert _history_change(df, pct=True) is None

    def test_single_row_returns_none(self):
        df = _make_history_df([100.0])
        assert _history_change(df, pct=False) is None

    def test_empty_df_returns_none(self):
        assert _history_change(pd.DataFrame(), pct=False) is None

    def test_none_returns_none(self):
        assert _history_change(None, pct=False) is None

    def test_uses_first_and_last(self):
        # 5-row df: change is last - first, not adjacent
        df = _make_history_df([100.0, 90.0, 95.0, 80.0, 120.0])
        assert _history_change(df, pct=False) == 20.0

    def test_weekly_change_pct(self):
        df = _make_history_df([200.0, 195.0, 205.0, 198.0, 210.0])
        result = _history_change(df, pct=True)
        assert abs(result - 0.05) < 1e-9


# ---------------------------------------------------------------------------
# _stmt_yoy_growth
# ---------------------------------------------------------------------------


class TestStmtYoyGrowth:
    def test_positive_growth(self):
        df = _make_2col_stmt("Total Revenue", 110, 100)
        result = _stmt_yoy_growth(df, "Total Revenue")
        assert abs(result - 0.1) < 1e-9

    def test_negative_growth(self):
        df = _make_2col_stmt("Total Revenue", 90, 100)
        result = _stmt_yoy_growth(df, "Total Revenue")
        assert abs(result - (-0.1)) < 1e-9

    def test_negative_base_absolute_denominator(self):
        # previous = -100, current = -80 → growth = (-80 - -100) / 100 = 0.2
        df = _make_2col_stmt("Net Income", -80, -100)
        result = _stmt_yoy_growth(df, "Net Income")
        assert abs(result - 0.2) < 1e-9

    def test_zero_previous_returns_none(self):
        df = _make_2col_stmt("Total Revenue", 100, 0)
        assert _stmt_yoy_growth(df, "Total Revenue") is None

    def test_single_period_returns_none(self):
        df = _make_stmt_df("Total Revenue", 100)
        assert _stmt_yoy_growth(df, "Total Revenue") is None

    def test_missing_row_returns_none(self):
        df = _make_2col_stmt("Total Revenue", 100, 90)
        assert _stmt_yoy_growth(df, "Operating Income") is None

    def test_empty_df_returns_none(self):
        assert _stmt_yoy_growth(pd.DataFrame(), "Total Revenue") is None

    def test_none_returns_none(self):
        assert _stmt_yoy_growth(None, "Total Revenue") is None

    def test_first_candidate_row_wins(self):
        df = _make_2col_stmt("Total Revenue", 200, 100)
        result = _stmt_yoy_growth(df, "Total Revenue", "Revenues")
        assert abs(result - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# _stmt_ratio
# ---------------------------------------------------------------------------


class TestStmtRatio:
    def _make_two_row_df(self, num_row: str, num_val, den_row: str, den_val) -> pd.DataFrame:
        return pd.DataFrame(
            {pd.Timestamp("2024-09-30"): [np.int64(num_val), np.int64(den_val)]},
            index=[num_row, den_row],
        )

    def test_basic_ratio(self):
        df = self._make_two_row_df("Operating Income", 50, "Total Revenue", 200)
        result = _stmt_ratio(df, "Operating Income", "Total Revenue")
        assert abs(result - 0.25) < 1e-9

    def test_zero_denominator_returns_none(self):
        df = self._make_two_row_df("Operating Income", 50, "Total Revenue", 0)
        assert _stmt_ratio(df, "Operating Income", "Total Revenue") is None

    def test_missing_numerator_returns_none(self):
        df = _make_stmt_df("Total Revenue", 200)
        assert _stmt_ratio(df, "Operating Income", "Total Revenue") is None

    def test_missing_denominator_returns_none(self):
        df = _make_stmt_df("Operating Income", 50)
        assert _stmt_ratio(df, "Operating Income", "Total Revenue") is None

    def test_none_df_returns_none(self):
        assert _stmt_ratio(None, "A", "B") is None


# ---------------------------------------------------------------------------
# _cross_debt_ebitda
# ---------------------------------------------------------------------------


class TestCrossDebtEbitda:
    def _make_bs(self, debt: float) -> pd.DataFrame:
        return pd.DataFrame(
            {pd.Timestamp("2024-09-30"): [np.int64(debt)]},
            index=["Total Debt"],
        )

    def _make_inc(self, op_income: float, da: float | None = None) -> pd.DataFrame:
        rows = {"Operating Income": np.int64(op_income)}
        if da is not None:
            rows["Reconciled Depreciation"] = np.int64(da)
        return pd.DataFrame(
            {pd.Timestamp("2024-09-30"): list(rows.values())},
            index=list(rows.keys()),
        )

    def test_basic_with_da(self):
        # debt=100, ebitda = 40 + 10 = 50 → ratio = 2.0
        result = _cross_debt_ebitda(self._make_bs(100), self._make_inc(40, 10))
        assert abs(result - 2.0) < 1e-9

    def test_without_da_uses_op_income_only(self):
        # debt=100, ebitda = 50 (no D&A) → ratio = 2.0
        result = _cross_debt_ebitda(self._make_bs(100), self._make_inc(50))
        assert abs(result - 2.0) < 1e-9

    def test_zero_ebitda_returns_none(self):
        result = _cross_debt_ebitda(self._make_bs(100), self._make_inc(0))
        assert result is None

    def test_missing_debt_returns_none(self):
        result = _cross_debt_ebitda(pd.DataFrame(), self._make_inc(50, 10))
        assert result is None

    def test_missing_income_stmt_returns_none(self):
        result = _cross_debt_ebitda(self._make_bs(100), pd.DataFrame())
        assert result is None

    def test_both_none_returns_none(self):
        assert _cross_debt_ebitda(None, None) is None


# ---------------------------------------------------------------------------
# _cross_fcf_margin
# ---------------------------------------------------------------------------


class TestCrossFcfMargin:
    def test_basic(self):
        info = {"freeCashflow": 50}
        inc = _make_stmt_df("Total Revenue", 200)
        result = _cross_fcf_margin(info, inc)
        assert abs(result - 0.25) < 1e-9

    def test_zero_revenue_returns_none(self):
        info = {"freeCashflow": 50}
        inc = _make_stmt_df("Total Revenue", 0)
        assert _cross_fcf_margin(info, inc) is None

    def test_missing_fcf_returns_none(self):
        result = _cross_fcf_margin({}, _make_stmt_df("Total Revenue", 200))
        assert result is None

    def test_missing_revenue_returns_none(self):
        result = _cross_fcf_margin({"freeCashflow": 50}, pd.DataFrame())
        assert result is None

    def test_non_dict_info_returns_none(self):
        result = _cross_fcf_margin(None, _make_stmt_df("Total Revenue", 200))
        assert result is None


# ---------------------------------------------------------------------------
# _dividend_growth
# ---------------------------------------------------------------------------


class TestDividendGrowth:
    def _make_dividends(self, years_values: dict[int, float]) -> pd.Series:
        """Build a dividend Series with one payment per year."""
        idx = [pd.Timestamp(f"{yr}-12-15") for yr in sorted(years_values)]
        vals = [years_values[yr] for yr in sorted(years_values)]
        return pd.Series(vals, index=idx, dtype=float)

    def test_positive_growth(self):
        s = self._make_dividends({2022: 0.80, 2023: 0.88})
        result = _dividend_growth(s)
        assert abs(result - 0.1) < 1e-9

    def test_negative_growth(self):
        s = self._make_dividends({2022: 1.00, 2023: 0.80})
        result = _dividend_growth(s)
        assert abs(result - (-0.2)) < 1e-9

    def test_single_year_returns_none(self):
        s = self._make_dividends({2023: 1.0})
        assert _dividend_growth(s) is None

    def test_zero_previous_returns_none(self):
        s = self._make_dividends({2022: 0.0, 2023: 1.0})
        assert _dividend_growth(s) is None

    def test_empty_series_returns_none(self):
        assert _dividend_growth(pd.Series(dtype=float)) is None

    def test_none_returns_none(self):
        assert _dividend_growth(None) is None


# ---------------------------------------------------------------------------
# _total_return_ratio
# ---------------------------------------------------------------------------


class TestTotalReturnRatio:
    def _make_dividends(self, annual_amount: float) -> pd.Series:
        idx = [pd.Timestamp("2023-12-15")]
        return pd.Series([annual_amount], index=idx, dtype=float)

    def test_basic(self):
        # dividends=20, buyback=abs(-30)=30, net_income=100 → ratio=0.5
        div = self._make_dividends(20.0)
        cf = _make_stmt_df("Repurchase Of Capital Stock", -30)
        inc = _make_stmt_df("Net Income", 100)
        result = _total_return_ratio(div, cf, inc)
        assert abs(result - 0.5) < 1e-9

    def test_no_dividends(self):
        # Only buyback counts; dividends series empty → total_div=0
        cf = _make_stmt_df("Repurchase Of Capital Stock", -50)
        inc = _make_stmt_df("Net Income", 100)
        result = _total_return_ratio(pd.Series(dtype=float), cf, inc)
        assert abs(result - 0.5) < 1e-9

    def test_no_buyback(self):
        div = self._make_dividends(30.0)
        inc = _make_stmt_df("Net Income", 100)
        result = _total_return_ratio(div, pd.DataFrame(), inc)
        assert abs(result - 0.3) < 1e-9

    def test_zero_net_income_returns_none(self):
        div = self._make_dividends(20.0)
        inc = _make_stmt_df("Net Income", 0)
        assert _total_return_ratio(div, pd.DataFrame(), inc) is None

    def test_missing_net_income_returns_none(self):
        div = self._make_dividends(20.0)
        assert _total_return_ratio(div, pd.DataFrame(), pd.DataFrame()) is None


# ---------------------------------------------------------------------------
# Integration: fetch_metrics for new metrics via mocked yf.Tickers
# ---------------------------------------------------------------------------


class TestNewMetricsIntegration:
    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_price_change(self, mock_cls):
        ticker = _make_ticker()
        ticker.history = MagicMock(return_value=_make_history_df([100.0, 103.0]))
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["price-change"])
        assert result["AAPL"]["price-change"] == 3.0

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_price_change_pct(self, mock_cls):
        ticker = _make_ticker()
        ticker.history = MagicMock(return_value=_make_history_df([200.0, 210.0]))
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["price-change-pct"])
        assert abs(result["AAPL"]["price-change-pct"] - 0.05) < 1e-4

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_weekly_change(self, mock_cls):
        ticker = _make_ticker()
        ticker.history = MagicMock(return_value=_make_history_df([100.0, 102.0, 98.0, 105.0, 110.0]))
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["weekly-change"])
        assert abs(result["AAPL"]["weekly-change"] - 0.1) < 1e-4

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_revenue_growth(self, mock_cls):
        inc = _make_2col_stmt("Total Revenue", 110_000_000_000, 100_000_000_000)
        ticker = _make_ticker(income_stmt=inc)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["revenue-growth"])
        assert abs(result["AAPL"]["revenue-growth"] - 0.1) < 1e-4

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_operating_margin(self, mock_cls):
        inc = pd.DataFrame(
            {pd.Timestamp("2024-09-30"): [np.int64(50_000_000_000), np.int64(200_000_000_000)]},
            index=["Operating Income", "Total Revenue"],
        )
        ticker = _make_ticker(income_stmt=inc)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["operating-margin"])
        assert abs(result["AAPL"]["operating-margin"] - 0.25) < 1e-4

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_gross_margin(self, mock_cls):
        inc = pd.DataFrame(
            {pd.Timestamp("2024-09-30"): [np.int64(60_000_000_000), np.int64(200_000_000_000)]},
            index=["Gross Profit", "Total Revenue"],
        )
        ticker = _make_ticker(income_stmt=inc)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["gross-margin"])
        assert abs(result["AAPL"]["gross-margin"] - 0.3) < 1e-4

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_equity_ratio(self, mock_cls):
        bs = pd.DataFrame(
            {pd.Timestamp("2024-09-30"): [np.int64(80_000_000_000), np.int64(320_000_000_000)]},
            index=["Stockholders Equity", "Total Assets"],
        )
        ticker = _make_ticker(balance_sheet=bs)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["equity-ratio"])
        assert abs(result["AAPL"]["equity-ratio"] - 0.25) < 1e-4

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_debt_ebitda(self, mock_cls):
        bs = pd.DataFrame(
            {pd.Timestamp("2024-09-30"): [np.int64(100_000_000_000)]},
            index=["Total Debt"],
        )
        inc = pd.DataFrame(
            {pd.Timestamp("2024-09-30"): [np.int64(40_000_000_000), np.int64(10_000_000_000)]},
            index=["Operating Income", "Reconciled Depreciation"],
        )
        ticker = _make_ticker(balance_sheet=bs, income_stmt=inc)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["debt-ebitda"])
        assert abs(result["AAPL"]["debt-ebitda"] - 2.0) < 1e-4

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_fcf_margin(self, mock_cls):
        inc = _make_stmt_df("Total Revenue", 400_000_000_000)
        ticker = _make_ticker(
            info={"freeCashflow": 100_000_000_000},
            income_stmt=inc,
        )
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["fcf-margin"])
        assert abs(result["AAPL"]["fcf-margin"] - 0.25) < 1e-4

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_buyback(self, mock_cls):
        cf = _make_stmt_df("Repurchase Of Capital Stock", -90_000_000_000)
        ticker = _make_ticker(cashflow=cf)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["buyback"])
        assert result["AAPL"]["buyback"] == -90_000_000_000

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_dividend_growth_integration(self, mock_cls):
        idx = [pd.Timestamp("2022-12-15"), pd.Timestamp("2023-12-15")]
        divs = pd.Series([0.88, 0.96], index=idx, dtype=float)
        ticker = _make_ticker(dividends=divs)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["dividend-growth"])
        expected = (0.96 - 0.88) / 0.88
        assert abs(result["AAPL"]["dividend-growth"] - expected) < 1e-4

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_guidance_returns_dict(self, mock_cls):
        calendar = {
            "Earnings Date": [pd.Timestamp("2024-07-30")],
            "Revenue High": 90_000_000_000,
        }
        ticker = _make_ticker(calendar=calendar)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["guidance"])
        assert isinstance(result["AAPL"]["guidance"], dict)
        assert "Earnings Date" in result["AAPL"]["guidance"]

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_next_earnings_extracts_date_list(self, mock_cls):
        calendar = {"Earnings Date": [pd.Timestamp("2024-07-30"), pd.Timestamp("2024-08-05")]}
        ticker = _make_ticker(calendar=calendar)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["next-earnings"])
        assert isinstance(result["AAPL"]["next-earnings"], list)
        assert result["AAPL"]["next-earnings"][0] == "2024-07-30T00:00:00"

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_ratings_returns_list_of_records(self, mock_cls):
        df = pd.DataFrame(
            {"strongBuy": [10], "buy": [20], "hold": [5], "sell": [2], "strongSell": [1]}
        )
        ticker = _make_ticker(recommendations_summary=df)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["ratings"])
        assert isinstance(result["AAPL"]["ratings"], list)
        assert result["AAPL"]["ratings"][0]["buy"] == 20

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_history_insufficient_data_returns_none(self, mock_cls):
        ticker = _make_ticker()
        ticker.history = MagicMock(return_value=_make_history_df([100.0]))
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["price-change"])
        assert result["AAPL"]["price-change"] is None

    @patch("fetch_market_data.fetcher.yf.Tickers")
    def test_multiple_new_metrics_in_one_call(self, mock_cls):
        inc = pd.DataFrame(
            {
                pd.Timestamp("2024-09-30"): [
                    np.int64(110_000_000_000),
                    np.int64(30_000_000_000),
                    np.int64(60_000_000_000),
                ],
                pd.Timestamp("2023-09-30"): [
                    np.int64(100_000_000_000),
                    np.int64(25_000_000_000),
                    np.int64(55_000_000_000),
                ],
            },
            index=["Total Revenue", "Operating Income", "Gross Profit"],
        )
        ticker = _make_ticker(income_stmt=inc)
        mock_cls.return_value = _make_tickers({"AAPL": ticker})
        result = fetch_metrics(["AAPL"], ["revenue-growth", "operating-margin", "gross-margin"])
        assert abs(result["AAPL"]["revenue-growth"] - 0.1) < 1e-4
        assert abs(result["AAPL"]["operating-margin"] - (30 / 110)) < 1e-4
        assert abs(result["AAPL"]["gross-margin"] - (60 / 110)) < 1e-4

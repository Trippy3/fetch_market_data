from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fetch_market_data.screener import ScreenParams, _build_query, run_screen


# ---------------------------------------------------------------------------
# _build_query tests
# ---------------------------------------------------------------------------


class TestBuildQueryMarket:
    def test_region_jp(self):
        params = ScreenParams(region="jp")
        q = _build_query(params)
        d = q.to_dict()
        assert d["operator"] == "EQ"
        assert d["operands"] == ["region", "jp"]

    def test_region_us(self):
        # region="us" uses EquityQuery eq on region field
        params = ScreenParams(region="us")
        q = _build_query(params)
        d = q.to_dict()
        assert d["operator"] == "EQ"
        assert d["operands"] == ["region", "us"]

    def test_exchange_nasdaq(self):
        # is-in is internally converted to OR of EQ conditions by yfinance
        params = ScreenParams(exchange="nasdaq")
        q = _build_query(params)
        d = q.to_dict()
        assert d["operator"] == "OR"
        exchange_codes = [op["operands"][1] for op in d["operands"]]
        assert "NMS" in exchange_codes
        assert "NYQ" not in exchange_codes

    def test_exchange_nyse(self):
        params = ScreenParams(exchange="nyse")
        q = _build_query(params)
        d = q.to_dict()
        assert d["operator"] == "OR"
        exchange_codes = [op["operands"][1] for op in d["operands"]]
        assert "NYQ" in exchange_codes
        assert "NMS" not in exchange_codes

    def test_exchange_us(self):
        params = ScreenParams(exchange="us")
        q = _build_query(params)
        d = q.to_dict()
        assert d["operator"] == "OR"
        exchange_codes = [op["operands"][1] for op in d["operands"]]
        assert "NMS" in exchange_codes
        assert "NYQ" in exchange_codes

    def test_no_market_raises(self):
        params = ScreenParams()
        with pytest.raises(ValueError, match="Either --region or --exchange"):
            _build_query(params)

    def test_unknown_region_raises(self):
        params = ScreenParams(region="xx")
        with pytest.raises(ValueError, match="Unknown region"):
            _build_query(params)

    def test_unknown_exchange_raises(self):
        params = ScreenParams(exchange="lse")
        with pytest.raises(ValueError, match="Unknown exchange"):
            _build_query(params)


class TestBuildQueryFilters:
    def _and_operands(self, params: ScreenParams) -> list[dict]:
        q = _build_query(params)
        d = q.to_dict()
        assert d["operator"] == "AND"
        return d["operands"]

    def test_roe_min(self):
        ops = self._and_operands(ScreenParams(region="jp", roe_min=10.0))
        fields = [op["operands"][0] for op in ops if "operands" in op]
        assert "returnonequity.lasttwelvemonths" in fields

    def test_div_yield_min(self):
        ops = self._and_operands(ScreenParams(region="jp", div_yield_min=1.5))
        fields = [op["operands"][0] for op in ops if "operands" in op]
        assert "forward_dividend_yield" in fields

    def test_div_growth_years(self):
        ops = self._and_operands(ScreenParams(region="jp", div_growth_years=3))
        fields = [op["operands"][0] for op in ops if "operands" in op]
        assert "consecutive_years_of_dividend_growth_count" in fields

    def test_revenue_growth_min(self):
        ops = self._and_operands(ScreenParams(region="jp", revenue_growth_min=3.0))
        fields = [op["operands"][0] for op in ops if "operands" in op]
        assert "totalrevenues1yrgrowth.lasttwelvemonths" in fields

    def test_debt_ebitda_max(self):
        ops = self._and_operands(ScreenParams(region="jp", debt_ebitda_max=5.0))
        fields = [op["operands"][0] for op in ops if "operands" in op]
        assert "totaldebtebitda.lasttwelvemonths" in fields

    def test_fcf_positive(self):
        ops = self._and_operands(ScreenParams(region="jp", fcf_positive=True))
        fields = [op["operands"][0] for op in ops if "operands" in op]
        assert "leveredfreecashflow.lasttwelvemonths" in fields

    def test_gross_margin_min(self):
        ops = self._and_operands(ScreenParams(exchange="nasdaq", gross_margin_min=50.0))
        fields = [op["operands"][0] for op in ops if "operands" in op]
        assert "grossprofitmargin.lasttwelvemonths" in fields

    def test_peg_max(self):
        ops = self._and_operands(ScreenParams(region="us", peg_max=1.0))
        fields = [op["operands"][0] for op in ops if "operands" in op]
        assert "pegratio_5y" in fields

    def test_insider_min(self):
        ops = self._and_operands(ScreenParams(exchange="nyse", insider_min=5.0))
        fields = [op["operands"][0] for op in ops if "operands" in op]
        assert "pctheldinsider" in fields

    def test_market_cap_min(self):
        ops = self._and_operands(ScreenParams(region="jp", market_cap_min=1_000_000_000))
        fields = [op["operands"][0] for op in ops if "operands" in op]
        assert "intradaymarketcap" in fields

    def test_sector(self):
        ops = self._and_operands(ScreenParams(region="us", sector="Technology"))
        fields = [op["operands"][0] for op in ops if "operands" in op]
        assert "sector" in fields

    def test_single_filter_no_and_wrapper(self):
        # Only market condition → no AND wrapper
        params = ScreenParams(region="jp")
        q = _build_query(params)
        d = q.to_dict()
        assert d["operator"] == "EQ"

    def test_multiple_filters_use_and(self):
        params = ScreenParams(region="jp", roe_min=10.0, div_yield_min=1.5)
        q = _build_query(params)
        d = q.to_dict()
        assert d["operator"] == "AND"
        assert len(d["operands"]) == 3  # region + roe + div_yield


# ---------------------------------------------------------------------------
# run_screen tests
# ---------------------------------------------------------------------------

_MOCK_RESPONSE = {
    "quotes": [
        {"symbol": "4776.T", "shortName": "CYBOZU INC"},
        {"symbol": "6036.T", "shortName": "KEEPER TECHNICAL"},
        {"symbol": "3064.T", "shortName": "MONOTARO CO.LTD"},
    ],
    "total": 42,
}


class TestRunScreen:
    @patch("fetch_market_data.screener.yf.screen")
    def test_returns_tickers(self, mock_screen: MagicMock):
        mock_screen.return_value = _MOCK_RESPONSE
        params = ScreenParams(region="jp", roe_min=10.0)
        result = run_screen(params)

        assert result["count"] == 3
        assert result["tickers"] == ["4776.T", "6036.T", "3064.T"]
        assert result["total"] == 42

    @patch("fetch_market_data.screener.yf.screen")
    def test_total_none_when_absent(self, mock_screen: MagicMock):
        mock_screen.return_value = {"quotes": []}
        params = ScreenParams(region="jp")
        result = run_screen(params)
        assert result["total"] is None

    @patch("fetch_market_data.screener.yf.screen")
    def test_query_metadata_region(self, mock_screen: MagicMock):
        mock_screen.return_value = _MOCK_RESPONSE
        params = ScreenParams(region="jp", roe_min=10.0, div_yield_min=1.5)
        result = run_screen(params)

        assert result["query"]["region"] == "jp"
        assert result["query"]["exchange"] is None
        assert result["query"]["conditions"]["roe_min"] == 10.0
        assert result["query"]["conditions"]["div_yield_min"] == 1.5

    @patch("fetch_market_data.screener.yf.screen")
    def test_query_metadata_exchange(self, mock_screen: MagicMock):
        mock_screen.return_value = {"quotes": []}
        params = ScreenParams(exchange="nasdaq", gross_margin_min=50.0)
        result = run_screen(params)

        assert result["query"]["region"] is None
        assert result["query"]["exchange"] == "nasdaq"
        assert result["query"]["conditions"]["gross_margin_min"] == 50.0

    @patch("fetch_market_data.screener.yf.screen")
    def test_empty_result(self, mock_screen: MagicMock):
        mock_screen.return_value = {"quotes": []}
        params = ScreenParams(region="jp")
        result = run_screen(params)

        assert result["count"] == 0
        assert result["tickers"] == []

    @patch("fetch_market_data.screener.yf.screen")
    def test_screen_called_with_correct_args(self, mock_screen: MagicMock):
        mock_screen.return_value = _MOCK_RESPONSE
        params = ScreenParams(region="jp", size=10, offset=50, sort_by="forward_dividend_yield", sort_asc=True)
        run_screen(params)

        mock_screen.assert_called_once()
        _, kwargs = mock_screen.call_args
        assert kwargs["sortField"] == "forward_dividend_yield"
        assert kwargs["sortAsc"] is True
        assert kwargs["size"] == 10
        assert kwargs["offset"] == 50
        assert kwargs["count"] is True

    @patch("fetch_market_data.screener.yf.screen")
    def test_offset_in_query_metadata(self, mock_screen: MagicMock):
        mock_screen.return_value = {"quotes": [], "total": 100}
        params = ScreenParams(region="jp", offset=25)
        result = run_screen(params)
        assert result["query"]["offset"] == 25

    @patch("fetch_market_data.screener.yf.screen")
    def test_fcf_positive_in_conditions(self, mock_screen: MagicMock):
        mock_screen.return_value = {"quotes": []}
        params = ScreenParams(region="jp", fcf_positive=True)
        result = run_screen(params)
        assert result["query"]["conditions"]["fcf_positive"] is True

    @patch("fetch_market_data.screener.yf.screen")
    def test_conditions_only_set_values(self, mock_screen: MagicMock):
        mock_screen.return_value = {"quotes": []}
        params = ScreenParams(region="jp")
        result = run_screen(params)
        # No conditions set → conditions dict should be empty
        assert result["query"]["conditions"] == {}

    def test_invalid_region_raises(self):
        params = ScreenParams(region="xx")
        with pytest.raises(ValueError):
            run_screen(params)

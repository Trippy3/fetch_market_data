from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from fetch_market_data.screen_cli import _build_parser, main


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestParser:
    def setup_method(self):
        self.parser = _build_parser()

    def test_region_jp(self):
        args = self.parser.parse_args(["--region", "jp"])
        assert args.region == "jp"
        assert args.exchange is None

    def test_region_us(self):
        args = self.parser.parse_args(["--region", "us"])
        assert args.region == "us"

    def test_exchange_nasdaq(self):
        args = self.parser.parse_args(["--exchange", "nasdaq"])
        assert args.exchange == "nasdaq"
        assert args.region is None

    def test_exchange_nyse(self):
        args = self.parser.parse_args(["--exchange", "nyse"])
        assert args.exchange == "nyse"

    def test_region_and_exchange_mutually_exclusive(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args(["--region", "jp", "--exchange", "nasdaq"])

    def test_no_market_exits(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args([])

    def test_filter_options(self):
        args = self.parser.parse_args([
            "--region", "jp",
            "--roe-min", "10",
            "--div-yield-min", "1.5",
            "--div-growth-years", "3",
            "--revenue-growth-min", "3",
            "--debt-ebitda-max", "5",
            "--fcf-positive",
            "--gross-margin-min", "50",
            "--peg-max", "1.0",
            "--insider-min", "5",
            "--market-cap-min", "1000000000",
            "--sector", "Technology",
        ])
        assert args.roe_min == 10.0
        assert args.div_yield_min == 1.5
        assert args.div_growth_years == 3
        assert args.revenue_growth_min == 3.0
        assert args.debt_ebitda_max == 5.0
        assert args.fcf_positive is True
        assert args.gross_margin_min == 50.0
        assert args.peg_max == 1.0
        assert args.insider_min == 5.0
        assert args.market_cap_min == 1_000_000_000.0
        assert args.sector == "Technology"

    def test_output_defaults(self):
        args = self.parser.parse_args(["--region", "jp"])
        assert args.size == 50
        assert args.sort_by == "intradaymarketcap"
        assert args.sort_asc is False

    def test_output_overrides(self):
        args = self.parser.parse_args([
            "--region", "jp",
            "--size", "20",
            "--sort-by", "forward_dividend_yield",
            "--sort-asc",
        ])
        assert args.size == 20
        assert args.sort_by == "forward_dividend_yield"
        assert args.sort_asc is True


# ---------------------------------------------------------------------------
# main() integration tests
# ---------------------------------------------------------------------------

_MOCK_RESULT = {
    "query": {"region": "jp", "exchange": None, "conditions": {"roe_min": 10.0}},
    "count": 2,
    "tickers": ["4776.T", "6036.T"],
}


class TestMain:
    @patch("fetch_market_data.screen_cli.run_screen")
    def test_outputs_json(self, mock_run: MagicMock, capsys):
        mock_run.return_value = _MOCK_RESULT
        with patch("sys.argv", ["screen-market-data", "--region", "jp", "--roe-min", "10"]):
            main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["count"] == 2
        assert data["tickers"] == ["4776.T", "6036.T"]

    @patch("fetch_market_data.screen_cli.run_screen")
    def test_passes_params_correctly(self, mock_run: MagicMock, capsys):
        mock_run.return_value = _MOCK_RESULT
        with patch("sys.argv", [
            "screen-market-data",
            "--exchange", "nasdaq",
            "--gross-margin-min", "50",
            "--fcf-positive",
            "--size", "20",
        ]):
            main()

        called_params = mock_run.call_args[0][0]
        assert called_params.exchange == "nasdaq"
        assert called_params.region is None
        assert called_params.gross_margin_min == 50.0
        assert called_params.fcf_positive is True
        assert called_params.size == 20

    @patch("fetch_market_data.screen_cli.run_screen")
    def test_error_exits_with_code_1(self, mock_run: MagicMock, capsys):
        mock_run.side_effect = ValueError("Unknown region 'xx'")
        with patch("sys.argv", ["screen-market-data", "--region", "jp"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    @patch("fetch_market_data.screen_cli.run_screen")
    def test_json_ensure_ascii_false(self, mock_run: MagicMock, capsys):
        mock_run.return_value = {
            "query": {"region": "jp", "exchange": None, "conditions": {}},
            "count": 1,
            "tickers": ["7203.T"],
        }
        with patch("sys.argv", ["screen-market-data", "--region", "jp"]):
            main()
        captured = capsys.readouterr()
        # Should be valid JSON
        json.loads(captured.out)

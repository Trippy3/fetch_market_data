from __future__ import annotations

import json
import sys
from unittest.mock import patch

import pytest

from fetch_market_data.cli import main


def _run_main(argv: list[str]) -> None:
    orig = sys.argv
    sys.argv = ["fetch-market-data"] + argv
    try:
        main()
    finally:
        sys.argv = orig


class TestCLI:
    @patch("fetch_market_data.cli.fetch_metrics")
    def test_default_fetches_price(self, mock_fetch, capsys):
        mock_fetch.return_value = {"AAPL": {"price": 172.45, "currency": "USD", "error": None}}
        _run_main(["AAPL"])
        mock_fetch.assert_called_once_with(["AAPL"], ["price"])

    @patch("fetch_market_data.cli.fetch_metrics")
    def test_explicit_price_flag(self, mock_fetch, capsys):
        mock_fetch.return_value = {"AAPL": {"price": 172.45, "currency": "USD", "error": None}}
        _run_main(["AAPL", "--price"])
        mock_fetch.assert_called_once_with(["AAPL"], ["price"])

    @patch("fetch_market_data.cli.fetch_metrics")
    def test_hyphenated_flag_avg_volume(self, mock_fetch, capsys):
        mock_fetch.return_value = {
            "AAPL": {"avg-volume": 45_000_000, "currency": "USD", "error": None}
        }
        _run_main(["AAPL", "--avg-volume"])
        mock_fetch.assert_called_once_with(["AAPL"], ["avg-volume"])

    @patch("fetch_market_data.cli.fetch_metrics")
    def test_multiple_flags(self, mock_fetch, capsys):
        mock_fetch.return_value = {
            "AAPL": {
                "price": 172.45,
                "market-cap": 2_700_000_000_000,
                "currency": "USD",
                "error": None,
            }
        }
        _run_main(["AAPL", "--price", "--market-cap"])
        called_metrics = mock_fetch.call_args[0][1]
        assert "price" in called_metrics
        assert "market-cap" in called_metrics

    @patch("fetch_market_data.cli.fetch_metrics")
    def test_output_is_symbol_keyed_json(self, mock_fetch, capsys):
        mock_fetch.return_value = {
            "AAPL": {"price": 172.45, "currency": "USD", "error": None},
            "7203.T": {"price": 3255.0, "currency": "JPY", "error": None},
        }
        _run_main(["AAPL", "7203.T"])
        data = json.loads(capsys.readouterr().out)
        assert data["AAPL"]["price"] == 172.45
        assert data["7203.T"]["currency"] == "JPY"

    @patch("fetch_market_data.cli.fetch_metrics")
    def test_error_symbol_in_output(self, mock_fetch, capsys):
        mock_fetch.return_value = {
            "INVALID": {"price": None, "currency": None, "error": "Ticker not found"}
        }
        _run_main(["INVALID"])
        data = json.loads(capsys.readouterr().out)
        assert data["INVALID"]["error"] == "Ticker not found"

    @patch("fetch_market_data.cli.fetch_metrics")
    def test_output_is_valid_json(self, mock_fetch, capsys):
        mock_fetch.return_value = {"MSFT": {"price": 415.20, "currency": "USD", "error": None}}
        _run_main(["MSFT"])
        json.loads(capsys.readouterr().out)  # must not raise

    def test_no_symbols_exits_with_error(self):
        with pytest.raises(SystemExit) as exc_info:
            _run_main([])
        assert exc_info.value.code != 0

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

import requests

from src import ingestion


def make_response(status_code: int, payload: dict | list | None = None) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload

    def raise_for_status() -> None:
        if status_code >= 400:
            raise requests.HTTPError(f"HTTP {status_code}")

    response.raise_for_status.side_effect = raise_for_status
    return response


class IngestionRetryTests(unittest.TestCase):
    @patch("src.ingestion.time.sleep")
    @patch("src.ingestion.requests.get")
    def test_retries_rate_limit_then_returns_json(self, get, sleep):
        payload = {"prices": []}
        get.side_effect = [
            make_response(429),
            make_response(429),
            make_response(200, payload),
        ]

        result = ingestion.fetch_market_chart("bitcoin")

        self.assertEqual(result, payload)
        self.assertEqual(
            sleep.call_args_list,
            [call(30.0), call(60.0)],
        )
        self.assertEqual(get.call_count, 3)

    @patch("src.ingestion.time.sleep")
    @patch("src.ingestion.requests.get")
    def test_raises_after_retry_budget_is_exhausted(self, get, sleep):
        get.side_effect = [
            make_response(429),
            make_response(429),
            make_response(429),
        ]

        with self.assertRaisesRegex(requests.HTTPError, "HTTP 429"):
            ingestion.fetch_current_market_snapshot(["bitcoin"])

        self.assertEqual(sleep.call_args_list, [call(30.0), call(60.0)])
        self.assertEqual(get.call_count, 3)

    @patch("src.ingestion.time.sleep")
    @patch("src.ingestion.fetch_market_chart", return_value={"prices": []})
    @patch("src.ingestion.fetch_current_market_snapshot", return_value=[])
    def test_paces_requests_between_snapshot_and_charts(self, snapshot, chart, sleep):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ingestion, "RAW_DATA_DIR", Path(temp_dir)):
                ingestion.run_ingestion(["bitcoin", "ethereum"])

        self.assertEqual(sleep.call_args_list, [call(15.0), call(15.0)])
        self.assertEqual(snapshot.call_count, 1)
        self.assertEqual(chart.call_count, 2)


if __name__ == "__main__":
    unittest.main()

"""
Ingestion step: pulls market data from CoinGecko's free, keyless public API.

Kept as a plain, standalone function (not an ADK agent) so it can be tested and
debugged on its own before being wrapped as a tool in tools.py.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# --- Configuration -----------------------------------------------------

# CoinGecko coin IDs (not ticker symbols). Find more at:
# https://api.coingecko.com/api/v3/coins/list
COIN_IDS = ["bitcoin", "ethereum", "solana", "cardano", "dogecoin"]

VS_CURRENCY = "usd"
DAYS_OF_HISTORY = 30  # how many days of daily history to pull per coin

BASE_URL = "https://api.coingecko.com/api/v3"
RAW_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Pace requests and use bounded backoff on HTTP 429 responses.
REQUEST_DELAY_SECONDS = 15.0
RATE_LIMIT_RETRY_DELAYS_SECONDS = (30.0, 60.0)


def _get_json(url: str, params: dict[str, str | int]) -> dict | list:
    """Make a CoinGecko request, retrying rate limits with bounded backoff."""
    retry_number = 0
    while True:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 429:
            response.raise_for_status()
            return response.json()

        if retry_number == len(RATE_LIMIT_RETRY_DELAYS_SECONDS):
            response.raise_for_status()
            raise requests.HTTPError("CoinGecko returned HTTP 429 after retries", response=response)

        delay = RATE_LIMIT_RETRY_DELAYS_SECONDS[retry_number]
        print(
            f"[ingestion] CoinGecko rate limit reached; "
            f"retrying in {delay:g}s ({retry_number + 1}/{len(RATE_LIMIT_RETRY_DELAYS_SECONDS)})"
        )
        time.sleep(delay)
        retry_number += 1

    raise RuntimeError("CoinGecko request retry loop exited unexpectedly")


def fetch_current_market_snapshot(coin_ids: list[str] = COIN_IDS, vs_currency: str = VS_CURRENCY) -> list[dict]:
    """Fetch current price/market-cap/volume snapshot for a list of coins in ONE call."""
    url = f"{BASE_URL}/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "ids": ",".join(coin_ids),
        "order": "market_cap_desc",
        "price_change_percentage": "24h",
    }
    return _get_json(url, params)


def fetch_market_chart(coin_id: str, days: int = DAYS_OF_HISTORY, vs_currency: str = VS_CURRENCY) -> dict:
    """Fetch daily historical price series for a single coin."""
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days, "interval": "daily"}
    return _get_json(url, params)


def run_ingestion(coin_ids: list[str] = COIN_IDS) -> dict:
    """
    Full ingestion step: snapshot + historical chart for each coin.
    Saves raw JSON to data/raw/ and returns the combined payload for the next step.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    snapshot = fetch_current_market_snapshot(coin_ids)

    charts = {}
    for coin_id in coin_ids:
        time.sleep(REQUEST_DELAY_SECONDS)
        charts[coin_id] = fetch_market_chart(coin_id)

    payload = {
        "fetched_at": timestamp,
        "vs_currency": VS_CURRENCY,
        "snapshot": snapshot,
        "charts": charts,
    }

    raw_path = RAW_DATA_DIR / f"raw_{timestamp}.json"
    with open(raw_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[ingestion] Saved raw data for {len(coin_ids)} coins to {raw_path}")
    return payload


if __name__ == "__main__":
    # Quick manual test: `python src/ingestion.py`
    data = run_ingestion()
    print(f"[ingestion] Snapshot entries: {len(data['snapshot'])}")
    print(f"[ingestion] Charts pulled for: {list(data['charts'].keys())}")

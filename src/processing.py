"""
Processing step: turns raw CoinGecko payloads into a tidy processed DataFrame with
moving averages, day-over-day % change, and rolling volatility.

Kept as a plain, standalone function so it can be tested independently of ADK.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROCESSED_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

MOVING_AVG_WINDOW = 7       # days
VOLATILITY_WINDOW = 7       # days (rolling std of daily % change)


def _chart_to_dataframe(coin_id: str, chart: dict) -> pd.DataFrame:
    """Convert one coin's CoinGecko market_chart response into a daily price DataFrame."""
    prices = chart.get("prices", [])  # list of [timestamp_ms, price]
    df = pd.DataFrame(prices, columns=["timestamp_ms", "price"])
    df["date"] = pd.to_datetime(df["timestamp_ms"], unit="ms").dt.date
    df["coin_id"] = coin_id
    # CoinGecko sometimes includes a partial "today" point — keep one row per date (last wins)
    df = df.drop_duplicates(subset="date", keep="last").reset_index(drop=True)
    return df[["coin_id", "date", "price"]]


def process_payload(payload: dict) -> pd.DataFrame:
    """
    Takes the raw payload from ingestion.run_ingestion() and returns a processed
    DataFrame: one row per (coin_id, date) with price, moving average, % change,
    and rolling volatility.
    """
    frames = []
    for coin_id, chart in payload["charts"].items():
        df = _chart_to_dataframe(coin_id, chart)
        df = df.sort_values("date").reset_index(drop=True)

        df["pct_change"] = df["price"].pct_change() * 100
        df["moving_avg"] = df["price"].rolling(window=MOVING_AVG_WINDOW, min_periods=1).mean()
        df["volatility"] = df["pct_change"].rolling(window=VOLATILITY_WINDOW, min_periods=2).std()

        frames.append(df)

    processed = pd.concat(frames, ignore_index=True)
    processed["processed_at"] = datetime.now(timezone.utc).isoformat()
    return processed


def summarize(processed: pd.DataFrame) -> pd.DataFrame:
    """One summary row per coin: latest price, latest % change, avg volatility over the window."""
    latest = processed.sort_values("date").groupby("coin_id").tail(1)
    avg_volatility = processed.groupby("coin_id")["volatility"].mean().rename("avg_volatility")

    summary = latest.merge(avg_volatility, on="coin_id")
    return summary[["coin_id", "date", "price", "pct_change", "moving_avg", "avg_volatility"]].sort_values(
        "price", ascending=False
    )


def run_processing(payload: dict) -> dict:
    """
    Full processing step. Saves processed + summary CSVs to data/processed/ and
    returns both as a dict of DataFrames for the next step (storage).
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = payload.get("fetched_at", datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))

    processed = process_payload(payload)
    summary = summarize(processed)

    processed_path = PROCESSED_DATA_DIR / f"processed_{timestamp}.csv"
    summary_path = PROCESSED_DATA_DIR / f"summary_{timestamp}.csv"
    processed.to_csv(processed_path, index=False)
    summary.to_csv(summary_path, index=False)

    print(f"[processing] Saved processed data to {processed_path}")
    print(f"[processing] Saved summary to {summary_path}")

    return {
        "processed_df": processed,
        "summary_df": summary,
        "processed_path": str(processed_path),
        "summary_path": str(summary_path),
        "timestamp": timestamp,
    }


if __name__ == "__main__":
    # Quick manual test: run ingestion then processing end-to-end.
    from ingestion import run_ingestion

    payload = run_ingestion()
    result = run_processing(payload)
    print(result["summary_df"])

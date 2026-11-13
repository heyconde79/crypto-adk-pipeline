"""
Wraps the plain, independently-testable functions from ingestion.py, processing.py,
storage.py, and visualize.py as tools an ADK agent can call.

NOTE: google-adk's exact tool-registration API (decorator vs. plain function passed
into an Agent's `tools=[...]` list, expected return types, etc.) can differ between
versions. The pattern below — a plain Python function with a clear docstring and
type-hinted arguments, passed directly into `tools=[...]` on an Agent — matches how
ADK's "function tool" support has typically worked, but check `pip show google-adk`
and the installed version's docs if an import below doesn't resolve.

A module-level dict (`_PIPELINE_STATE`) is used to pass data between tool calls within
one pipeline run, since ADK tools are typically expected to take/return simple,
JSON-serializable values rather than passing pandas DataFrames directly.
"""

from ingestion import COIN_IDS, run_ingestion
from processing import run_processing
from storage import run_storage
from visualize import run_visualization

# Holds the non-JSON-serializable intermediate results (DataFrames, raw payload)
# between tool calls within a single pipeline run.
_PIPELINE_STATE: dict = {}


def ingest_crypto_data(coin_ids: list[str] = None) -> dict:
    """
    Tool: pulls current + historical market data for the configured coins from
    CoinGecko's free public API and saves the raw JSON locally.

    Args:
        coin_ids: optional list of CoinGecko coin IDs to override the default set.

    Returns:
        A small JSON-serializable summary (not the full payload) confirming what
        was fetched, for the agent to report back.
    """
    ids = coin_ids or COIN_IDS
    payload = run_ingestion(ids)
    _PIPELINE_STATE["payload"] = payload
    _PIPELINE_STATE["raw_json_path"] = None  # set below

    # Re-derive the raw file path (run_ingestion prints it but returns the payload only)
    from pathlib import Path

    from ingestion import RAW_DATA_DIR

    matches = sorted(RAW_DATA_DIR.glob(f"raw_{payload['fetched_at']}*.json"))
    if matches:
        _PIPELINE_STATE["raw_json_path"] = str(matches[0])

    return {
        "status": "success",
        "coins_fetched": list(payload["charts"].keys()),
        "fetched_at": payload["fetched_at"],
    }


def process_crypto_data() -> dict:
    """
    Tool: transforms the most recently ingested raw data into moving averages,
    % change, and volatility, and saves processed + summary CSVs locally.

    Returns:
        A JSON-serializable summary of the processing step for the agent to report back.
    """
    payload = _PIPELINE_STATE.get("payload")
    if payload is None:
        return {"status": "error", "message": "No ingested data found. Run ingest_crypto_data first."}

    result = run_processing(payload)
    _PIPELINE_STATE["processing_result"] = result

    return {
        "status": "success",
        "rows_processed": len(result["processed_df"]),
        "processed_path": result["processed_path"],
        "summary_path": result["summary_path"],
    }


def store_crypto_data() -> dict:
    """
    Tool: uploads the raw JSON and processed/summary CSVs to the configured GCS bucket.

    Returns:
        A JSON-serializable dict of the GCS URIs written, for the agent to report back.
    """
    result = _PIPELINE_STATE.get("processing_result")
    if result is None:
        return {"status": "error", "message": "No processed data found. Run process_crypto_data first."}

    raw_json_path = _PIPELINE_STATE.get("raw_json_path")
    uploaded = run_storage(result, raw_json_path=raw_json_path)

    return {"status": "success", "uploaded": uploaded}


def visualize_crypto_data() -> dict:
    """
    Tool: renders the processed data as output/report.html (chart + summary table).

    Returns:
        A JSON-serializable dict with the local path to the generated report.
    """
    result = _PIPELINE_STATE.get("processing_result")
    if result is None:
        return {"status": "error", "message": "No processed data found. Run process_crypto_data first."}

    report_path = run_visualization(result)
    return {"status": "success", "report_path": report_path}

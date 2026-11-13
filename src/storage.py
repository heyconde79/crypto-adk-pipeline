"""
Storage step: uploads raw + processed data to Google Cloud Storage.

Kept as a plain, standalone function so it can be tested independently of ADK.
Uses Application Default Credentials rather than hardcoded credentials.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud.storage import Bucket, Client

load_dotenv()

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")


def _get_gcs_bucket() -> Bucket:
    bucket_name = GCS_BUCKET_NAME
    if not bucket_name:
        raise RuntimeError(
            "GCS_BUCKET_NAME is not set. Copy .env.example to .env and enter your bucket name."
        )
    project_id = GOOGLE_CLOUD_PROJECT
    if not project_id:
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT is not set. Add your Google Cloud project ID to .env."
        )
    return Client(project=project_id).bucket(bucket_name)


def upload_file(local_path: str, object_name: str, content_type: str | None = None) -> str:
    """Upload a local file to Google Cloud Storage. Returns its gs:// URI."""
    bucket = _get_gcs_bucket()
    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_path, content_type=content_type)
    gcs_uri = f"gs://{bucket.name}/{object_name}"
    print(f"[storage] Uploaded {local_path} -> {gcs_uri}")
    return gcs_uri


def run_storage(processing_result: dict, raw_json_path: str | None = None) -> dict:
    """
    Upload processed + summary CSVs (and raw JSON if provided) to GCS under a
    timestamp-prefixed object name, so each run's artifacts are kept separately.
    """
    timestamp = processing_result["timestamp"]
    prefix = f"crypto-pipeline/{timestamp}"

    uploaded = {}

    if raw_json_path and Path(raw_json_path).exists():
        uploaded["raw"] = upload_file(raw_json_path, f"{prefix}/raw.json", "application/json")

    uploaded["processed"] = upload_file(
        processing_result["processed_path"], f"{prefix}/processed.csv", "text/csv"
    )
    uploaded["summary"] = upload_file(
        processing_result["summary_path"], f"{prefix}/summary.csv", "text/csv"
    )

    return uploaded


if __name__ == "__main__":
    # Quick manual test: run the full pipeline up through storage.
    from ingestion import RAW_DATA_DIR, run_ingestion
    from processing import run_processing

    payload = run_ingestion()
    result = run_processing(payload)

    # Find the raw file we just wrote (ingestion prints its path; here we re-derive it)
    raw_path = sorted(RAW_DATA_DIR.glob(f"raw_{payload['fetched_at']}*.json"))
    raw_path = str(raw_path[0]) if raw_path else None

    run_storage(result, raw_json_path=raw_path)

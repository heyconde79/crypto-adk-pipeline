"""Command-line entry point for the ADK-orchestrated crypto pipeline."""

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

APP_NAME = "crypto_pipeline"
USER_ID = "local_user"


def _validate_model_auth() -> None:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    use_vertex_ai = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower() in {
        "true",
        "1",
        "yes",
    }

    if api_key and api_key != "your_google_api_key_here":
        return
    if use_vertex_ai:
        missing = [
            name
            for name in ("GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION")
            if not os.getenv(name)
        ]
        if not missing:
            return
        raise SystemExit(
            "Vertex AI is enabled, but these settings are missing: " + ", ".join(missing)
        )
    raise SystemExit(
        "Configure Gemini access before running the ADK workflow: set GOOGLE_API_KEY "
        "in .env, or enable Vertex AI with GOOGLE_GENAI_USE_VERTEXAI=true, "
        "GOOGLE_CLOUD_PROJECT, and GOOGLE_CLOUD_LOCATION."
    )


def run_direct() -> None:
    """Run the same pipeline tools directly for debugging without ADK."""
    from tools import (
        ingest_crypto_data,
        process_crypto_data,
        store_crypto_data,
        visualize_crypto_data,
    )

    for label, tool in (
        ("Ingestion", ingest_crypto_data),
        ("Processing", process_crypto_data),
        ("Storage", store_crypto_data),
        ("Visualization", visualize_crypto_data),
    ):
        print(f"\n== {label} ==")
        result = tool()
        print(result)
        if result.get("status") != "success":
            raise RuntimeError(f"{label} failed: {result.get('message', 'unknown error')}")


async def _run_via_adk() -> None:
    from agents import pipeline_agent
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    async with InMemoryRunner(agent=pipeline_agent, app_name=APP_NAME) as runner:
        session = await runner.session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
        )
        request = types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        "Run the complete crypto pipeline now. Execute ingestion, then "
                        "processing, then Google Cloud Storage upload, then visualization. "
                        "Call your assigned tool for each step, do not skip steps, and "
                        "report any tool errors instead of claiming success."
                    )
                )
            ],
        )
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=request,
        ):
            if event.error_code:
                details = event.error_message or event.error_code
                raise RuntimeError(f"ADK workflow failed: {details}")
            if event.content:
                for part in event.content.parts or []:
                    if part.text:
                        print(f"[{event.author}] {part.text}")


def run_via_adk() -> None:
    """Run the configured SequentialAgent through ADK's session runner."""
    _validate_model_auth()
    asyncio.run(_run_via_adk())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the crypto data pipeline.")
    parser.add_argument(
        "--direct",
        action="store_true",
        help="bypass ADK and run the tool functions directly for debugging",
    )
    args = parser.parse_args()

    if args.direct:
        run_direct()
    else:
        run_via_adk()


if __name__ == "__main__":
    main()

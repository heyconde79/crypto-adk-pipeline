"""ADK agents for the ordered crypto ingestion, processing, storage, and report workflow."""

import os

from google.adk.agents import Agent, SequentialAgent

from tools import (
    ingest_crypto_data,
    process_crypto_data,
    store_crypto_data,
    visualize_crypto_data,
)

MODEL = os.getenv("GOOGLE_ADK_MODEL", "gemini-3.5-flash-lite")

ingestion_agent = Agent(
    name="ingestion_agent",
    model=MODEL,
    description="Pulls current and historical crypto market data from CoinGecko's public API.",
    instruction=(
        "Call ingest_crypto_data exactly once to fetch historical market data for the "
        "configured coins. Report the tool result and do not claim success if its status "
        "is not success."
    ),
    tools=[ingest_crypto_data],
)

processing_agent = Agent(
    name="processing_agent",
    model=MODEL,
    description="Transforms raw crypto data into moving averages, % change, and volatility.",
    instruction=(
        "Call process_crypto_data exactly once to process the data produced by the "
        "ingestion step. Report the tool result and do not claim success if its status "
        "is not success."
    ),
    tools=[process_crypto_data],
)

storage_agent = Agent(
    name="storage_agent",
    model=MODEL,
    description="Uploads raw and processed crypto data to Google Cloud Storage.",
    instruction=(
        "Call store_crypto_data exactly once to upload the artifacts produced by "
        "processing to Google Cloud Storage. Report the tool result and do not claim "
        "success if its status is not success."
    ),
    tools=[store_crypto_data],
)

visualization_agent = Agent(
    name="visualization_agent",
    model=MODEL,
    description="Renders the processed crypto data as an HTML report (chart + summary table).",
    instruction=(
        "Call visualize_crypto_data exactly once to generate the HTML report from the "
        "processed data. Report the tool result and do not claim success if its status "
        "is not success."
    ),
    tools=[visualize_crypto_data],
)

pipeline_agent = SequentialAgent(
    name="crypto_pipeline_agent",
    description="End-to-end crypto data pipeline: ingest -> process -> store -> visualize.",
    sub_agents=[ingestion_agent, processing_agent, storage_agent, visualization_agent],
)

root_agent = pipeline_agent

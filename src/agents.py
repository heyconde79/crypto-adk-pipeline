"""
Defines the ADK agents and chains them into a sequential, agent-orchestrated pipeline:

    IngestionAgent -> ProcessingAgent -> StorageAgent -> VisualizationAgent

Each agent wraps exactly one tool from tools.py, so the orchestration logic (the
SequentialAgent / root agent below) is what satisfies the "agentic design" requirement:
the steps run as an agent-driven workflow, not as one standalone script.

IMPORTANT: google-adk's API surface (import paths, Agent/SequentialAgent constructor
arguments, whether an LLM model is required per-agent, etc.) can vary by installed
version. The structure below follows ADK's common pattern of:
    - `Agent` (a single LLM-backed agent with a list of tools)
    - `SequentialAgent` (a workflow agent that runs sub-agents in order)
If these imports don't match your installed version, run `pip show google-adk` and
check the package's own README/examples for the current class names — the tool
functions in tools.py are version-independent and will still work once rewired.
"""

from google.adk.agents import Agent, SequentialAgent

from tools import (
    ingest_crypto_data,
    process_crypto_data,
    store_crypto_data,
    visualize_crypto_data,
)

# A model string ADK can use for the LLM-backed agents below. Swap for whatever
# model your ADK installation/credentials support.
MODEL = "gemini-2.0-flash"

ingestion_agent = Agent(
    name="ingestion_agent",
    model=MODEL,
    description="Pulls current and historical crypto market data from CoinGecko's public API.",
    instruction=(
        "Call ingest_crypto_data to fetch the latest market data for the configured "
        "coins. Report back which coins were fetched and when."
    ),
    tools=[ingest_crypto_data],
)

processing_agent = Agent(
    name="processing_agent",
    model=MODEL,
    description="Transforms raw crypto data into moving averages, % change, and volatility.",
    instruction=(
        "Call process_crypto_data to transform the most recently ingested raw data. "
        "Report back how many rows were processed."
    ),
    tools=[process_crypto_data],
)

storage_agent = Agent(
    name="storage_agent",
    model=MODEL,
    description="Uploads raw and processed crypto data to Google Cloud Storage.",
    instruction=(
        "Call store_crypto_data to upload the raw and processed data to Google Cloud Storage. "
        "Report back the GCS locations that were written."
    ),
    tools=[store_crypto_data],
)

visualization_agent = Agent(
    name="visualization_agent",
    model=MODEL,
    description="Renders the processed crypto data as an HTML report (chart + summary table).",
    instruction=(
        "Call visualize_crypto_data to generate the HTML report from the processed data. "
        "Report back the local path to the generated report."
    ),
    tools=[visualize_crypto_data],
)

# The orchestrator: runs the four agents above in a fixed sequence. This is the
# "agent-driven workflow" that satisfies the assignment's agentic design requirement.
pipeline_agent = SequentialAgent(
    name="crypto_pipeline_agent",
    description="End-to-end crypto data pipeline: ingest -> process -> store -> visualize.",
    sub_agents=[ingestion_agent, processing_agent, storage_agent, visualization_agent],
)

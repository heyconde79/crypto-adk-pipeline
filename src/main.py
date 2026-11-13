"""
Entry point: runs the agent-orchestrated crypto pipeline end to end.

Usage:
    python src/main.py            # run via the ADK SequentialAgent
    python src/main.py --direct   # bypass ADK and call the tool functions directly,
                                   # in the same order the agents would call them.
                                   # Useful for debugging ingestion/processing/storage/
                                   # visualization independently of the ADK runner setup.
"""

import sys


def run_direct():
    """Calls the same tool functions the agents call, in sequence, with no ADK layer.
    Good for verifying the pipeline logic itself works before wiring up ADK's runner."""
    from tools import (
        ingest_crypto_data,
        process_crypto_data,
        store_crypto_data,
        visualize_crypto_data,
    )

    print("== Step 1: Ingestion ==")
    print(ingest_crypto_data())

    print("\n== Step 2: Processing ==")
    print(process_crypto_data())

    print("\n== Step 3: Storage ==")
    print(store_crypto_data())

    print("\n== Step 4: Visualization ==")
    print(visualize_crypto_data())


def run_via_adk():
    """
    Runs the pipeline through ADK's SequentialAgent (agents.pipeline_agent).

    ADK typically requires a Runner (e.g. google.adk.runners.InMemoryRunner) to
    actually execute an agent against a user message/session. The exact Runner
    API can vary by installed ADK version, so check `pip show google-adk` / the
    package's own quickstart if this needs adjusting. A minimal example runner
    call is sketched below, commented out, as a starting point.
    """
    from agents import pipeline_agent

    print(f"Loaded ADK pipeline agent: {pipeline_agent.name}")
    print("Sub-agents:", [a.name for a in pipeline_agent.sub_agents])

    # --- Example of how you'd typically invoke an ADK agent (adjust to your ADK version) ---
    # from google.adk.runners import InMemoryRunner
    # runner = InMemoryRunner(agent=pipeline_agent, app_name="crypto_pipeline")
    # session = runner.session_service.create_session(app_name="crypto_pipeline", user_id="student")
    # for event in runner.run(user_id="student", session_id=session.id,
    #                          new_message="Run the full crypto data pipeline now."):
    #     print(event)

    print(
        "\nNOTE: wire up an ADK Runner above (see the commented example) to actually "
        "execute this agent. Until then, use `python src/main.py --direct` to run the "
        "pipeline logic without the ADK execution layer."
    )


if __name__ == "__main__":
    if "--direct" in sys.argv:
        run_direct()
    else:
        run_via_adk()

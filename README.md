# Crypto Pipeline — ADK Agentic Data Engineering

An end-to-end agentic data pipeline: pulls crypto market data from CoinGecko's free public
API, computes moving averages / volatility / % change, stores raw + processed data in
Google Cloud Storage, and renders an HTML page with a chart and summary table — orchestrated by
Google ADK agents.

## Project layout

```
crypto-adk-pipeline/
├── README.md
├── requirements.txt
├── .env.example          # copy to .env and fill in your own values
├── .gitignore
├── data/
│   ├── raw/               # raw API responses land here (local fallback / debug)
│   └── processed/         # processed CSVs land here (local fallback / debug)
├── output/
│   └── report.html        # generated local visualization
└── src/
    ├── ingestion.py        # plain function: calls CoinGecko, returns/saves raw JSON
    ├── processing.py       # plain function: moving avg, % change, volatility
    ├── storage.py           # plain function: upload raw + processed data to GCS
    ├── visualize.py          # plain function: renders output/report.html
    ├── tools.py               # wraps the above as ADK-callable tools
    ├── agents.py               # defines the ADK agents + SequentialAgent pipeline
    └── main.py                  # entry point — runs the agent pipeline
```

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # on Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a Google Cloud Storage bucket, then copy `.env.example` to `.env` and set the
   bucket name and Google Cloud project ID. Configure Gemini access with either a
   Google AI Studio API key or Vertex AI:
   ```bash
   cp .env.example .env
   ```
   For an API key, uncomment and set `GOOGLE_API_KEY`. For Vertex AI, set
   `GOOGLE_GENAI_USE_VERTEXAI=true` and `GOOGLE_CLOUD_LOCATION`; authenticate with ADC
   as described below.
   **Never commit `.env`** — it's already in `.gitignore`.

4. Install the Google Cloud CLI, then authenticate locally with Application Default Credentials:
   ```bash
   gcloud auth application-default login
   ```
   Enable the Cloud Storage API for the configured project and grant the signed-in
   account `Storage Object Creator` access to the bucket. The storage client uses ADC;
   do not put service-account keys or other credentials in `.env`.

## Running it

```bash
python src/main.py
```

This runs the full agent-orchestrated pipeline: ingest → process → store → visualize.
Open `output/report.html` in a browser to see the result.

### Configuring which coins to track

Edit the `COIN_IDS` list at the top of `src/ingestion.py` (CoinGecko coin IDs, e.g.
`bitcoin`, `ethereum`, `solana` — find IDs at https://api.coingecko.com/api/v3/coins/list).

## Notes on the CoinGecko API

This project uses CoinGecko's fully public, keyless endpoints
(`https://api.coingecko.com/api/v3/...`). No signup or API key is required, but the
free tier is rate-limited (roughly 5–15 requests/minute per IP). `ingestion.py` waits
15 seconds between calls and retries HTTP 429 responses after 30 and 60 seconds. A run
can still fail if the shared IP quota remains exhausted.

## Agent workflow

`src/agents.py` defines four ADK agents in a `SequentialAgent`: ingestion, processing,
storage, and visualization. Each agent invokes its assigned tool in `src/tools.py`.
Run the workflow with `python src/main.py`. Use `python src/main.py --direct` only to
debug the tool functions without ADK.

## Tests

Run the focused unit tests with:

```bash
python -m unittest discover -s tests -v
```

## Future improvements

See [FUTURE_IMPROVEMENTS.md](./FUTURE_IMPROVEMENTS.md) for proposed improvements to
scalability, reliability, observability, testing, security, cost, and data quality.

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
   bucket name and Google Cloud project ID:
   ```bash
   cp .env.example .env
   ```
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
free tier is rate-limited (roughly 5–15 requests/minute per IP), so `ingestion.py`
paces its requests and only pulls the coins you configure. If you start seeing HTTP 429
responses, increase the delay between calls in `ingestion.py`.

## A note on google-adk

This scaffold writes ingestion/processing/storage/visualization as **plain, independently
testable Python functions first** (`src/ingestion.py` etc.), then wraps them as ADK tools
in `src/tools.py` and chains them in `src/agents.py`. This split exists so you can debug
each step on its own before adding the agent layer on top — check `pip show google-adk`
and the ADK docs for the exact current Agent / SequentialAgent import paths and
constructor signatures, since the API surface can change between versions and this
scaffold was written without being able to verify against the live package.

## Future Improvements doc

Don't forget the second deliverable: a short Word/PDF doc on future improvements
(scalability, error handling, monitoring, scheduling, testing, security, cost, data
quality). A few starter ideas based on this pipeline:
- Replace local credentials with a proper secrets manager (Google Secret Manager)
  before any real deployment.
- Add retry/backoff logic around CoinGecko 429s instead of failing the run.
- Schedule the pipeline (cron, Google Cloud Scheduler, or Airflow) instead of manual runs.
- Add a data quality check (e.g. reject a day's data if price is null or zero) before
  it's written to GCS.
- Add logging/monitoring (Google Cloud Logging) so failed runs are visible without checking manually.

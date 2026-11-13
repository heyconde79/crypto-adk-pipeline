# Future Improvements

**Author:** Heyder Conde

**Project repository:** [https://github.com/heyconde79/crypto-adk-pipeline](https://github.com/heyconde79/crypto-adk-pipeline)

## Project summary

The crypto pipeline uses Google ADK agents to coordinate CoinGecko data ingestion,
processing, Google Cloud Storage uploads, and HTML report generation. The current
workflow tracks five coins, calculates daily indicators, spaces API requests, retries
rate-limit responses, and includes focused unit tests.

## Potential improvements

### Scalability and scheduling

The current workflow is designed for a small number of coins and a manually started
run. A future version could run on Cloud Run Jobs and use Cloud Scheduler for regular,
managed executions. If the dataset or number of tracked assets grows, a queue or
workflow service could coordinate work while limiting concurrent CoinGecko requests.
Processed history could also be loaded into BigQuery for larger analytical queries.

### Reliability and monitoring

The ingestion step already waits between API requests and applies bounded retries for
HTTP 429 responses. Future work could extend retry handling to transient network and
server errors, honor the API's `Retry-After` header, and record per-stage run status so
failed runs can resume safely. Structured logs, run IDs, duration metrics, and alerts
through Google Cloud Monitoring would make failures easier to diagnose.

### Testing and data quality

The project has focused unit tests for rate-limit retries, request pacing, and storage
configuration. Additional tests could cover processing edge cases and tool-to-agent
integration. Before uploading results, data-quality checks could detect missing or
duplicate timestamps, null or nonpositive prices, incomplete coin responses, and
unexpected gaps in the historical series.

### Security and cost management

Credentials should remain outside the public repository. The existing `.env` exclusion
and Application Default Credentials approach should be retained; a deployed service
should use a dedicated service identity with only the permissions it needs. A production
version could add secret rotation where API secrets are required, storage lifecycle
rules to remove obsolete objects, and budget/quota alerts to track API and cloud costs.

### Reporting

The generated HTML report is useful for a local run. A future version could publish the
report to a private or authenticated hosting service, add data freshness indicators, and
show longer-term comparisons while preserving the current lightweight local option.

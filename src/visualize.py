"""
Visualization step: renders the processed data as a static HTML page with a line
chart (Chart.js via CDN, no build step) and a summary table.

Kept as a plain, standalone function so it can be tested independently of ADK.
"""

import json
from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_PATH = OUTPUT_DIR / "report.html"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Crypto Pipeline Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    color-scheme: light dark;
  }}
  body {{
    font-family: -apple-system, Segoe UI, Roboto, sans-serif;
    max-width: 960px;
    margin: 2rem auto;
    padding: 0 1rem;
  }}
  h1 {{ margin-bottom: 0.25rem; }}
  .meta {{ color: #888; margin-bottom: 2rem; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 2rem; }}
  th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #ddd; }}
  th {{ font-weight: 600; }}
  .positive {{ color: #1a7f37; }}
  .negative {{ color: #cf222e; }}
  canvas {{ max-width: 100%; }}
</style>
</head>
<body>
  <h1>Crypto Market Pipeline</h1>
  <p class="meta">Generated {generated_at} &middot; coins tracked: {coin_list}</p>

  <canvas id="priceChart" height="100"></canvas>

  <h2>Summary</h2>
  {summary_table}

  <script>
    const chartData = {chart_data_json};
    const ctx = document.getElementById('priceChart');
    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: chartData.labels,
        datasets: chartData.datasets
      }},
      options: {{
        responsive: true,
        plugins: {{ title: {{ display: true, text: 'Price (last {days} days)' }} }},
        scales: {{ y: {{ title: {{ display: true, text: 'Price (USD)' }} }} }}
      }}
    }});
  </script>
</body>
</html>
"""


def _summary_to_html_table(summary_df: pd.DataFrame) -> str:
    rows = []
    for _, row in summary_df.iterrows():
        pct_class = "positive" if row["pct_change"] >= 0 else "negative"
        rows.append(
            "<tr>"
            f"<td>{row['coin_id']}</td>"
            f"<td>${row['price']:,.2f}</td>"
            f"<td class='{pct_class}'>{row['pct_change']:+.2f}%</td>"
            f"<td>${row['moving_avg']:,.2f}</td>"
            f"<td>{row['avg_volatility']:.2f}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>Coin</th><th>Latest Price</th><th>24h-step % Change</th>"
        "<th>7-day Moving Avg</th><th>Avg Volatility</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


def _build_chart_data(processed_df: pd.DataFrame) -> dict:
    labels = sorted(processed_df["date"].astype(str).unique().tolist())
    datasets = []
    for coin_id, group in processed_df.groupby("coin_id"):
        series_by_date = dict(zip(group["date"].astype(str), group["price"]))
        datasets.append(
            {
                "label": coin_id,
                "data": [series_by_date.get(d) for d in labels],
                "fill": False,
                "tension": 0.2,
            }
        )
    return {"labels": labels, "datasets": datasets}


def run_visualization(processing_result: dict) -> str:
    """
    Builds output/report.html from the processed + summary DataFrames.
    Returns the local path to the generated HTML file.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    processed_df = processing_result["processed_df"]
    summary_df = processing_result["summary_df"]

    chart_data = _build_chart_data(processed_df)
    summary_table = _summary_to_html_table(summary_df)
    coin_list = ", ".join(sorted(processed_df["coin_id"].unique()))
    num_days = processed_df["date"].nunique()

    html = HTML_TEMPLATE.format(
        generated_at=processing_result["timestamp"],
        coin_list=coin_list,
        summary_table=summary_table,
        chart_data_json=json.dumps(chart_data),
        days=num_days,
    )

    with open(OUTPUT_PATH, "w") as f:
        f.write(html)

    print(f"[visualize] Report written to {OUTPUT_PATH}")
    return str(OUTPUT_PATH)


if __name__ == "__main__":
    # Quick manual test: run the full pipeline up through visualization.
    from ingestion import run_ingestion
    from processing import run_processing

    payload = run_ingestion()
    result = run_processing(payload)
    run_visualization(result)

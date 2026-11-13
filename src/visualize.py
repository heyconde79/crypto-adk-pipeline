"""
Visualization step: renders processed market data as a responsive HTML dashboard.

The report uses Chart.js from a CDN and can be opened locally without a build step.
"""

import html
import json
from datetime import datetime
from pathlib import Path
from string import Template

import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_PATH = OUTPUT_DIR / "report.html"

HTML_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Crypto Market Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
      color: #17211d;
      background: #f5f7f6;
      font-synthesis: none;
      text-rendering: optimizeLegibility;
      --green: #15956b;
      --green-dark: #087a55;
      --green-soft: #e8f6f0;
      --muted: #78827d;
      --line: #e8ece9;
      --card: #ffffff;
    }
    * { box-sizing: border-box; }
    body { margin: 0; min-width: 320px; background: #f5f7f6; }
    button, input { font: inherit; }
    button { cursor: pointer; }
    .app-shell { display: grid; grid-template-columns: 220px minmax(0, 1fr); min-height: 100vh; }
    .sidebar {
      position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column;
      padding: 26px 16px 18px; background: #fff; border-right: 1px solid var(--line);
    }
    .brand { display: flex; align-items: center; gap: 11px; padding: 0 10px 34px; color: #17211d; text-decoration: none; }
    .brand-mark {
      display: grid; place-items: center; width: 34px; height: 34px; border-radius: 11px;
      background: #143b2c; color: white; font-size: 15px; font-weight: 800;
    }
    .brand-name { font-size: 14px; font-weight: 750; letter-spacing: -.02em; }
    .nav-label { padding: 0 11px 9px; color: #9aa39e; font-size: 10px; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
    .nav-link {
      display: flex; align-items: center; gap: 11px; margin: 2px 0; padding: 11px;
      border-radius: 9px; color: #68736d; font-size: 13px; font-weight: 600; text-decoration: none;
    }
    .nav-link.active { background: var(--green-soft); color: var(--green-dark); }
    .nav-icon { display: grid; place-items: center; width: 20px; font-size: 15px; }
    .sidebar-bottom { margin-top: auto; padding: 14px 11px 0; border-top: 1px solid var(--line); }
    .sidebar-bottom strong { display: block; margin-bottom: 5px; font-size: 12px; }
    .sidebar-bottom span { color: var(--muted); font-size: 11px; line-height: 1.5; }
    .main-shell { min-width: 0; }
    .topbar {
      display: flex; align-items: center; justify-content: space-between; min-height: 65px;
      padding: 0 34px; background: rgba(255,255,255,.84); border-bottom: 1px solid var(--line);
    }
    .crumb { color: #738078; font-size: 12px; }
    .top-status { display: flex; align-items: center; gap: 8px; color: #59665f; font-size: 11px; font-weight: 650; }
    .status-dot { width: 7px; height: 7px; border-radius: 50%; background: #35b783; box-shadow: 0 0 0 3px #e6f7ef; }
    .content { width: min(1440px, 100%); margin: 0 auto; padding: 30px 34px 40px; }
    .page-heading { display: flex; align-items: end; justify-content: space-between; gap: 20px; margin-bottom: 23px; }
    .eyebrow { margin: 0 0 7px; color: var(--green-dark); font-size: 10px; font-weight: 800; letter-spacing: .14em; }
    h1 { margin: 0; font-size: clamp(24px, 3vw, 31px); letter-spacing: -.045em; }
    .page-subtitle { margin: 8px 0 0; color: var(--muted); font-size: 13px; }
    .generated-meta { text-align: right; color: var(--muted); font-size: 10px; }
    .generated-meta strong { display: block; margin-top: 5px; color: #34413a; font-size: 12px; font-weight: 650; }
    .dashboard-grid { display: grid; grid-template-columns: minmax(0, 1fr) 275px; gap: 18px; align-items: start; }
    .main-column, .right-column { display: grid; gap: 16px; min-width: 0; }
    .card { background: var(--card); border: 1px solid #e9eeeb; border-radius: 13px; box-shadow: 0 3px 12px rgba(27, 49, 38, .035); }
    .chart-card { padding: 21px 22px 14px; }
    .asset-heading { display: flex; align-items: center; gap: 12px; min-width: 0; }
    .coin-avatar {
      flex: 0 0 auto; display: grid; place-items: center; width: 42px; height: 42px;
      border: 1px solid #e2ebe6; border-radius: 50%; background: #f0f7f3; color: var(--green-dark);
      font-size: 12px; font-weight: 800;
    }
    .asset-copy { min-width: 0; }
    .asset-title-row { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
    .asset-copy h2 { overflow: hidden; max-width: 300px; margin: 0; font-size: 18px; letter-spacing: -.025em; text-overflow: ellipsis; white-space: nowrap; }
    .tracked-badge { padding: 3px 7px; border: 1px solid #b8e4d1; border-radius: 5px; color: var(--green-dark); font-size: 9px; font-weight: 750; letter-spacing: .06em; }
    .asset-id { display: block; margin-top: 4px; color: var(--muted); font-size: 11px; }
    .asset-price { margin-left: auto; text-align: right; white-space: nowrap; }
    .asset-price strong { display: block; font-size: clamp(20px, 3vw, 27px); letter-spacing: -.04em; }
    .asset-price span { display: block; margin-top: 4px; font-size: 11px; font-weight: 650; }
    .positive { color: #138458; }
    .negative { color: #d34b56; }
    .neutral { color: var(--muted); }
    .selector-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 21px 0 13px; }
    .selector-label { color: #758079; font-size: 10px; font-weight: 750; letter-spacing: .08em; text-transform: uppercase; }
    .search-box { width: min(210px, 44%); padding: 8px 11px; border: 1px solid #e5eae7; border-radius: 8px; outline: none; background: #fbfcfb; color: #26332c; font-size: 11px; }
    .search-box:focus { border-color: #7bc8a7; box-shadow: 0 0 0 3px #e9f7f0; }
    .coin-list { display: flex; flex-wrap: wrap; gap: 7px; }
    .coin-option {
      display: inline-flex; align-items: center; gap: 7px; min-height: 34px; padding: 6px 11px;
      border: 1px solid #e7ece9; border-radius: 8px; background: #fff; color: #58645d;
      font-size: 11px; font-weight: 650; transition: background .15s, border-color .15s, color .15s;
    }
    .coin-option:hover { border-color: #b6dfcb; background: #f7fcf9; }
    .coin-option[aria-pressed="true"] { border-color: #9bd6b9; background: var(--green-soft); color: var(--green-dark); }
    .coin-option-mark { display: grid; place-items: center; width: 18px; height: 18px; border-radius: 50%; background: #edf2ef; font-size: 8px; font-weight: 800; }
    .coin-option[aria-pressed="true"] .coin-option-mark { background: #d0efdf; }
    .empty-search { margin: 10px 0 0; color: var(--muted); font-size: 11px; }
    .chart-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-top: 23px; }
    .chart-toolbar h3, .section-title { margin: 0; font-size: 13px; font-weight: 750; }
    .chart-subtitle { display: block; margin-top: 4px; color: var(--muted); font-size: 10px; }
    .range-switch { display: inline-flex; gap: 3px; padding: 3px; border: 1px solid #edf0ee; border-radius: 8px; background: #f7f9f8; }
    .range-switch button { min-width: 38px; padding: 6px 8px; border: 0; border-radius: 6px; background: transparent; color: #78827d; font-size: 10px; font-weight: 700; }
    .range-switch button[aria-pressed="true"] { background: #fff; color: var(--green-dark); box-shadow: 0 1px 3px rgba(20, 45, 32, .12); }
    .chart-wrap { position: relative; height: 290px; margin-top: 10px; }
    .chart-fallback { margin: 0; padding: 20px; border-radius: 8px; background: #f7f9f8; color: var(--muted); font-size: 12px; }
    .chart-footnote { margin-top: 3px; color: #89938e; font-size: 10px; }
    .table-card { padding: 19px 20px 8px; }
    .section-heading { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 14px; }
    .section-heading p { margin: 4px 0 0; color: var(--muted); font-size: 10px; }
    .count-badge { padding: 5px 8px; border-radius: 6px; background: #f3f6f4; color: #758079; font-size: 10px; font-weight: 650; }
    .table-scroll { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; white-space: nowrap; }
    th { padding: 9px 10px; border-bottom: 1px solid var(--line); color: #89938e; font-size: 9px; font-weight: 750; letter-spacing: .06em; text-align: right; text-transform: uppercase; }
    th:first-child, td:first-child { padding-left: 2px; text-align: left; }
    td { padding: 11px 10px; border-bottom: 1px solid #f0f2f1; color: #39453e; font-size: 11px; text-align: right; }
    tbody tr:last-child td { border-bottom: 0; }
    tbody tr.selected-row { background: #f8fcfa; }
    .table-coin {
      padding: 0; border: 0; background: transparent; color: #26332c; font-size: 11px; font-weight: 700; text-align: left;
    }
    .table-coin:hover { color: var(--green-dark); text-decoration: underline; }
    .stats-card, .info-card { padding: 18px; }
    .snapshot-date { color: var(--muted); font-size: 10px; }
    .live-label { display: inline-flex; align-items: center; gap: 5px; color: #718078; font-size: 8px; font-weight: 800; letter-spacing: .08em; }
    .live-label::before { width: 6px; height: 6px; border-radius: 50%; background: #39b77f; content: ""; }
    .stats-grid { display: grid; grid-template-columns: 1fr 1fr; margin-top: 13px; }
    .stat { min-height: 91px; padding: 13px 10px 10px 0; border-top: 1px solid var(--line); }
    .stat:nth-child(2n) { padding-left: 12px; border-left: 1px solid var(--line); }
    .stat-label { display: block; color: #7c8781; font-size: 9px; }
    .stat-value { display: block; overflow: hidden; margin-top: 8px; color: #27342d; font-size: 15px; font-weight: 750; letter-spacing: -.025em; text-overflow: ellipsis; }
    .stat-note { display: block; margin-top: 5px; color: #9aa39e; font-size: 9px; }
    .info-card p { margin: 8px 0 0; color: #77827c; font-size: 11px; line-height: 1.6; }
    .info-tag { display: inline-block; margin-top: 13px; padding: 5px 8px; border-radius: 6px; background: #f0f7f3; color: #247650; font-size: 9px; font-weight: 700; }
    .disclaimer { padding: 13px 15px; border: 1px solid #e8eeea; border-radius: 10px; background: #fbfcfb; color: #7f8983; font-size: 10px; line-height: 1.6; }
    .footer { margin-top: 22px; color: #9aa39e; font-size: 9px; text-align: center; }
    @media (max-width: 1050px) {
      .app-shell { grid-template-columns: 190px minmax(0, 1fr); }
      .dashboard-grid { grid-template-columns: minmax(0, 1fr) 240px; }
      .content { padding-right: 22px; padding-left: 22px; }
      .topbar { padding-right: 22px; padding-left: 22px; }
    }
    @media (max-width: 800px) {
      .app-shell { display: block; }
      .sidebar { position: static; width: 100%; height: auto; padding: 12px 16px; border-right: 0; border-bottom: 1px solid var(--line); }
      .brand { padding: 0 4px 10px; }
      .nav-label, .sidebar-bottom { display: none; }
      .sidebar nav { display: flex; gap: 6px; }
      .nav-link { margin: 0; padding: 8px 10px; }
      .topbar { min-height: 48px; }
      .content { padding-top: 23px; }
      .dashboard-grid { grid-template-columns: 1fr; }
      .right-column { grid-template-columns: 1fr 1fr; }
      .disclaimer { grid-column: 1 / -1; }
    }
    @media (max-width: 560px) {
      .topbar { padding: 0 16px; }
      .content { padding: 20px 13px 28px; }
      .page-heading { align-items: start; }
      .generated-meta { max-width: 120px; overflow-wrap: anywhere; }
      .chart-card { padding: 16px 13px 12px; }
      .asset-heading { gap: 9px; }
      .asset-price strong { font-size: 20px; }
      .coin-avatar { width: 36px; height: 36px; }
      .selector-row { align-items: start; flex-direction: column; }
      .search-box { width: 100%; }
      .chart-wrap { height: 235px; }
      .right-column { grid-template-columns: 1fr; }
      .disclaimer { grid-column: auto; }
      .table-card { padding-right: 13px; padding-left: 13px; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <a class="brand" href="#overview" aria-label="Crypto Pipeline home">
        <span class="brand-mark">C</span><span class="brand-name">Crypto Pipeline</span>
      </a>
      <div class="nav-label">Workspace</div>
      <nav aria-label="Main navigation">
        <a class="nav-link active" href="#overview"><span class="nav-icon">⌂</span>Overview</a>
        <a class="nav-link" href="#tracked-assets"><span class="nav-icon">◈</span>Tracked assets</a>
      </nav>
      <div class="sidebar-bottom">
        <strong>Market data</strong>
        <span>Historical prices in USD, prepared by your local pipeline.</span>
      </div>
    </aside>
    <div class="main-shell">
      <header class="topbar">
        <span class="crumb">Workspace&nbsp; / &nbsp;Markets</span>
        <span class="top-status"><span class="status-dot"></span>Daily market report</span>
      </header>
      <main class="content" id="overview">
        <section class="page-heading">
          <div>
            <p class="eyebrow">CRYPTO MARKETS</p>
            <h1>Explore assets</h1>
            <p class="page-subtitle">A closer look at your tracked coins and recent price history.</p>
          </div>
          <div class="generated-meta">Report generated<strong>$generated_at</strong></div>
        </section>

        <div class="dashboard-grid">
          <div class="main-column">
            <section class="card chart-card" aria-label="Selected coin price chart">
              <div class="asset-heading">
                <div class="coin-avatar" id="coinAvatar">$initial_mark</div>
                <div class="asset-copy">
                  <div class="asset-title-row"><h2 id="coinName">$initial_coin_name</h2><span class="tracked-badge">TRACKED</span></div>
                  <span class="asset-id" id="coinIdLabel">$initial_coin_id</span>
                </div>
                <div class="asset-price">
                  <strong id="currentPrice">$initial_price</strong>
                  <span id="changeLabel" class="$initial_change_class">$initial_change</span>
                </div>
              </div>

              <div class="selector-row">
                <span class="selector-label">Choose an asset</span>
                <input class="search-box" id="coinSearch" type="search" placeholder="Search tracked coins" aria-label="Search tracked coins">
              </div>
              <div class="coin-list" id="coinList" role="group" aria-label="Select a coin">
$coin_buttons
              </div>
              <p class="empty-search" id="emptySearch" hidden>No tracked coins match that search.</p>

              <div class="chart-toolbar">
                <div><h3>Price history</h3><span class="chart-subtitle">Daily price · USD</span></div>
                <div class="range-switch" role="group" aria-label="Chart date range">
                  <button type="button" data-range="7" aria-pressed="false">7D</button>
                  <button type="button" data-range="30" aria-pressed="true">30D</button>
                </div>
              </div>
              <div class="chart-wrap">
                <canvas id="priceChart" role="img" aria-label="Selected coin price history"></canvas>
                <p class="chart-fallback" id="chartFallback" hidden>Chart library unavailable. Coin prices and summary statistics are still shown below.</p>
              </div>
              <p class="chart-footnote">Historical prices are for informational purposes and may not reflect real-time market quotes.</p>
            </section>

            <section class="card table-card" id="tracked-assets">
              <div class="section-heading">
                <h3 class="section-title">All tracked assets</h3>
                <span class="count-badge">$coin_count coins</span>
              </div>
              <div class="table-scroll">
                <table>
                  <thead><tr><th scope="col">Coin</th><th scope="col">Latest price</th><th scope="col">Daily change</th><th scope="col">7-day avg</th><th scope="col">Avg volatility</th></tr></thead>
                  <tbody>
$summary_rows
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          <aside class="right-column" aria-label="Selected coin details">
            <section class="card stats-card">
              <div class="section-heading">
                <div><h3 class="section-title">Market snapshot</h3><p class="snapshot-date" id="snapshotDate">$initial_date</p></div>
                <span class="live-label">LAST POINT</span>
              </div>
              <div class="stats-grid">
                <div class="stat"><span class="stat-label">Window high</span><strong class="stat-value" id="windowHigh">$initial_high</strong><span class="stat-note">Selected period</span></div>
                <div class="stat"><span class="stat-label">Window low</span><strong class="stat-value" id="windowLow">$initial_low</strong><span class="stat-note">Selected period</span></div>
                <div class="stat"><span class="stat-label">7-day average</span><strong class="stat-value" id="movingAverage">$initial_average</strong><span class="stat-note">Moving price</span></div>
                <div class="stat"><span class="stat-label">Avg volatility</span><strong class="stat-value" id="avgVolatility">$initial_volatility</strong><span class="stat-note">Full history average</span></div>
              </div>
            </section>
            <section class="card info-card">
              <h3 class="section-title">About this view</h3>
              <p>Choose any tracked coin to update the chart and statistics. Use the date controls to focus on the last week or full available history.</p>
              <span class="info-tag">USD · $days daily points max</span>
            </section>
            <div class="disclaimer">This dashboard reports historical data from the pipeline. It does not execute trades or provide investment advice.</div>
          </aside>
        </div>
        <footer class="footer">Crypto Market Pipeline&nbsp; · &nbsp;Generated locally from processed market data</footer>
      </main>
    </div>
  </div>
  <script id="reportData" type="application/json">$report_data_json</script>
  <script>
    (function () {
      const report = JSON.parse(document.getElementById("reportData").textContent);
      const summaries = report.summary;
      const labels = report.chart.labels;
      const datasets = report.chart.datasets;
      const priceFormatter = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 2 });
      const smallPriceFormatter = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 6 });
      const dateFormatter = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" });
      const shortDateFormatter = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" });
      let selectedCoin = report.defaultCoin;
      let selectedRange = 30;
      let priceChart = null;
      const canvas = document.getElementById("priceChart");

      function formatPrice(value) {
        if (value === null || !Number.isFinite(value)) return "—";
        if (Math.abs(value) >= 1) return priceFormatter.format(value);
        return String.fromCharCode(36) + smallPriceFormatter.format(value).replace(/0+$$/, "").replace(/\\.$$/, "");
      }

      function formatChange(value) {
        if (value === null || !Number.isFinite(value)) return "—";
        return (value > 0 ? "+" : "") + value.toFixed(2) + "% vs previous point";
      }

      function coinName(coinId) {
        return coinId.replace(/[-_]/g, " ").replace(/\\b\\w/g, function (letter) { return letter.toUpperCase(); });
      }

      function setText(id, value) {
        document.getElementById(id).textContent = value;
      }

      function updateChart() {
        const source = datasets.find(function (dataset) { return dataset.label === selectedCoin; });
        if (!source) return;
        const start = Math.max(0, labels.length - selectedRange);
        const visibleLabels = labels.slice(start);
        const visibleValues = source.data.slice(start);
        const availablePrices = visibleValues.filter(function (value) { return Number.isFinite(value); });
        if (availablePrices.length) {
          setText("windowHigh", formatPrice(Math.max.apply(null, availablePrices)));
          setText("windowLow", formatPrice(Math.min.apply(null, availablePrices)));
        }
        if (typeof Chart === "undefined") {
          canvas.hidden = true;
          document.getElementById("chartFallback").hidden = false;
          return;
        }
        const isPositive = summaries[selectedCoin].pct_change === null || summaries[selectedCoin].pct_change >= 0;
        const color = isPositive ? "#15956b" : "#d34b56";
        const gradient = canvas.getContext("2d").createLinearGradient(0, 0, 0, 290);
        gradient.addColorStop(0, isPositive ? "rgba(21,149,107,.22)" : "rgba(211,75,86,.18)");
        gradient.addColorStop(1, "rgba(255,255,255,0)");
        const dataset = {
          label: coinName(selectedCoin),
          data: visibleValues,
          borderColor: color,
          backgroundColor: gradient,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          fill: true,
          tension: 0.32
        };
        const options = {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { intersect: false, mode: "index" },
          plugins: {
            legend: { display: false },
            tooltip: {
              displayColors: false,
              callbacks: {
                title: function (items) {
                  return dateFormatter.format(new Date(visibleLabels[items[0].dataIndex] + "T00:00:00"));
                },
                label: function (item) { return " " + formatPrice(item.raw); }
              }
            }
          },
          scales: {
            x: {
              grid: { display: false },
              border: { display: false },
              ticks: {
                color: "#89938e",
                maxTicksLimit: 6,
                maxRotation: 0,
                callback: function (value) {
                  const date = visibleLabels[value];
                  return date ? shortDateFormatter.format(new Date(date + "T00:00:00")) : "";
                }
              }
            },
            y: { grid: { color: "#edf1ee" }, border: { display: false }, ticks: { color: "#89938e", maxTicksLimit: 5, callback: formatPrice } }
          }
        };
        if (priceChart) {
          priceChart.data.labels = visibleLabels;
          priceChart.data.datasets = [dataset];
          priceChart.options = options;
          priceChart.update();
        } else {
          priceChart = new Chart(canvas, { type: "line", data: { labels: visibleLabels, datasets: [dataset] }, options: options });
        }
      }

      function selectCoin(coinId) {
        const metrics = summaries[coinId];
        if (!metrics) return;
        selectedCoin = coinId;
        setText("coinName", coinName(coinId));
        setText("coinIdLabel", coinId);
        setText("coinAvatar", coinId.slice(0, 2).toUpperCase());
        setText("currentPrice", formatPrice(metrics.price));
        setText("changeLabel", formatChange(metrics.pct_change));
        setText("windowHigh", formatPrice(metrics.window_high));
        setText("windowLow", formatPrice(metrics.window_low));
        setText("movingAverage", formatPrice(metrics.moving_avg));
        setText("avgVolatility", metrics.avg_volatility === null ? "—" : metrics.avg_volatility.toFixed(2) + "%");
        setText("snapshotDate", metrics.date ? "Data through " + dateFormatter.format(new Date(metrics.date + "T00:00:00")) : "Latest available data");
        const changeLabel = document.getElementById("changeLabel");
        changeLabel.className = metrics.pct_change === null ? "neutral" : (metrics.pct_change >= 0 ? "positive" : "negative");
        document.querySelectorAll("[data-select-coin]").forEach(function (button) {
          const isActive = button.dataset.selectCoin === coinId;
          button.setAttribute("aria-pressed", String(isActive));
          const row = button.closest("tr");
          if (row) row.classList.toggle("selected-row", isActive);
        });
        updateChart();
      }

      document.querySelectorAll("[data-select-coin]").forEach(function (button) {
        button.addEventListener("click", function () { selectCoin(button.dataset.selectCoin); });
      });
      document.querySelectorAll("[data-range]").forEach(function (button) {
        button.addEventListener("click", function () {
          selectedRange = Number(button.dataset.range);
          document.querySelectorAll("[data-range]").forEach(function (item) {
            item.setAttribute("aria-pressed", String(item === button));
          });
          updateChart();
        });
      });
      document.getElementById("coinSearch").addEventListener("input", function (event) {
        const query = event.target.value.trim().toLowerCase();
        let visibleCount = 0;
        document.querySelectorAll(".coin-option").forEach(function (button) {
          const matches = button.dataset.coinName.includes(query);
          button.hidden = !matches;
          if (matches) visibleCount += 1;
        });
        document.getElementById("emptySearch").hidden = visibleCount > 0;
      });
      selectCoin(selectedCoin);
    })();
  </script>
</body>
</html>
""")


def _display_coin_name(coin_id: str) -> str:
    return coin_id.replace("-", " ").replace("_", " ").title()


def _number_or_none(value) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _format_price(value: float | None) -> str:
    if value is None:
        return "—"
    if abs(value) >= 1:
        return f"${value:,.2f}"
    return "$" + f"{value:,.6f}".rstrip("0").rstrip(".")


def _format_change(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:+.2f}%"


def _format_generated_at(timestamp: str) -> str:
    try:
        generated_at = datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ")
    except ValueError:
        return timestamp
    return f"{generated_at.strftime('%b')} {generated_at.day}, {generated_at.year} · {generated_at.strftime('%I:%M %p')} UTC"


def _build_chart_data(processed_df: pd.DataFrame) -> dict:
    labels = sorted(processed_df["date"].astype(str).unique().tolist())
    datasets = []
    for coin_id, group in processed_df.groupby("coin_id"):
        series_by_date = dict(zip(group["date"].astype(str), group["price"]))
        datasets.append(
            {
                "label": str(coin_id),
                "data": [_number_or_none(series_by_date.get(date)) for date in labels],
            }
        )
    return {"labels": labels, "datasets": datasets}


def _build_summary_data(processed_df: pd.DataFrame, summary_df: pd.DataFrame) -> dict:
    summary = {}
    for _, row in summary_df.iterrows():
        coin_id = str(row["coin_id"])
        coin_prices = processed_df.loc[processed_df["coin_id"] == row["coin_id"], "price"]
        summary[coin_id] = {
            "price": _number_or_none(row["price"]),
            "pct_change": _number_or_none(row["pct_change"]),
            "moving_avg": _number_or_none(row["moving_avg"]),
            "avg_volatility": _number_or_none(row["avg_volatility"]),
            "window_high": _number_or_none(coin_prices.max()),
            "window_low": _number_or_none(coin_prices.min()),
            "date": str(row["date"])[:10],
        }
    return summary


def _coin_buttons_html(coin_ids: list[str], selected_coin: str) -> str:
    buttons = []
    for coin_id in coin_ids:
        escaped_id = html.escape(coin_id, quote=True)
        name = html.escape(_display_coin_name(coin_id))
        mark = html.escape(coin_id[:2].upper())
        pressed = "true" if coin_id == selected_coin else "false"
        buttons.append(
            f'<button type="button" class="coin-option" data-select-coin="{escaped_id}" '
            f'data-coin-name="{html.escape((coin_id + " " + name).lower(), quote=True)}" '
            f'aria-pressed="{pressed}"><span class="coin-option-mark">{mark}</span>{name}</button>'
        )
    return "\n".join(f"                {button}" for button in buttons)


def _summary_to_html_table(summary_df: pd.DataFrame, selected_coin: str) -> str:
    rows = []
    for _, row in summary_df.iterrows():
        coin_id = str(row["coin_id"])
        escaped_id = html.escape(coin_id, quote=True)
        name = html.escape(_display_coin_name(coin_id))
        pct_change = _number_or_none(row["pct_change"])
        pct_class = "positive" if pct_change is not None and pct_change >= 0 else "negative"
        if pct_change is None:
            pct_class = "neutral"
        selected_class = " selected-row" if coin_id == selected_coin else ""
        volatility = _number_or_none(row["avg_volatility"])
        volatility_text = "—" if volatility is None else f"{volatility:.2f}%"
        rows.append(
            f'<tr class="{selected_class.strip()}">'
            f'<td><button type="button" class="table-coin" data-select-coin="{escaped_id}" '
            f'aria-pressed="{str(coin_id == selected_coin).lower()}">{name}</button></td>'
            f"<td>{_format_price(_number_or_none(row['price']))}</td>"
            f'<td class="{pct_class}">{_format_change(pct_change)}</td>'
            f"<td>{_format_price(_number_or_none(row['moving_avg']))}</td>"
            f"<td>{volatility_text}</td>"
            "</tr>"
        )
    return "\n                    ".join(rows)


def _script_json(value: dict) -> str:
    return (
        json.dumps(value, ensure_ascii=True, allow_nan=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def run_visualization(processing_result: dict) -> str:
    """
    Builds output/report.html from the processed + summary DataFrames.
    Returns the local path to the generated HTML file.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    processed_df = processing_result["processed_df"]
    summary_df = processing_result["summary_df"]
    if summary_df.empty or processed_df.empty:
        raise ValueError("Cannot generate a market report without processed coin data.")

    coin_ids = [str(coin_id) for coin_id in summary_df["coin_id"].tolist()]
    selected_coin = coin_ids[0]
    summary_data = _build_summary_data(processed_df, summary_df)
    initial = summary_data[selected_coin]
    report_data = {
        "defaultCoin": selected_coin,
        "chart": _build_chart_data(processed_df),
        "summary": summary_data,
    }

    html_report = HTML_TEMPLATE.substitute(
        generated_at=html.escape(_format_generated_at(str(processing_result["timestamp"]))),
        coin_count=len(coin_ids),
        coin_buttons=_coin_buttons_html(coin_ids, selected_coin),
        summary_rows=_summary_to_html_table(summary_df, selected_coin),
        initial_mark=html.escape(selected_coin[:2].upper()),
        initial_coin_name=html.escape(_display_coin_name(selected_coin)),
        initial_coin_id=html.escape(selected_coin),
        initial_price=_format_price(initial["price"]),
        initial_change=_format_change(initial["pct_change"]),
        initial_change_class=(
            "neutral" if initial["pct_change"] is None
            else "positive" if initial["pct_change"] >= 0
            else "negative"
        ),
        initial_date=(
            "Data through " + html.escape(initial["date"]) if initial["date"] else "Latest available data"
        ),
        initial_high=_format_price(initial["window_high"]),
        initial_low=_format_price(initial["window_low"]),
        initial_average=_format_price(initial["moving_avg"]),
        initial_volatility=(
            "—" if initial["avg_volatility"] is None else f"{initial['avg_volatility']:.2f}%"
        ),
        days=processed_df["date"].nunique(),
        report_data_json=_script_json(report_data),
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as report_file:
        report_file.write(html_report)

    print(f"[visualize] Report written to {OUTPUT_PATH}")
    return str(OUTPUT_PATH)


if __name__ == "__main__":
    # Quick manual test: run the full pipeline up through visualization.
    from ingestion import run_ingestion
    from processing import run_processing

    payload = run_ingestion()
    result = run_processing(payload)
    run_visualization(result)

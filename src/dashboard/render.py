"""A self-contained HTML dashboard: no CDN, network, or raw customer records."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from html import escape
import json
from pathlib import Path
import re
from typing import TYPE_CHECKING, Mapping
from uuid import uuid4

from medallion.gold.sql_resources import render_sql

if TYPE_CHECKING:
    from pyspark.sql import DataFrame

_TABLES = (
    "sales_by_product", "revenue_by_customer",
    "daily_weekly_trends", "customer_segmentation",
)


def dashboard_queries(table_names: Mapping[str, str]) -> dict[str, str]:
    """Render five read-only datasets for local views or Unity Catalog tables.

    Required keys are the four Gold table names; values are strict
    one-to-three-part SQL identifiers.
    """
    sql = render_sql(
        "medallion.dashboard", "dashboard_queries.sql", identifiers=table_names
    )
    pieces = re.split(r"(?m)^-- dataset: ([a-z_]+)\s*\n", sql)
    if pieces[0].strip() or len(pieces) != 11:
        raise ValueError("Malformed dashboard SQL resource")
    queries = {
        pieces[index]: pieces[index + 1].strip().removesuffix(";")
        for index in range(1, len(pieces), 2)
    }
    if set(queries) != {
        "products", "categories", "trends", "segments",
        "customer_revenue_distribution",
    }:
        raise ValueError("Unexpected dashboard dataset names")
    return queries


def dashboard_datasets(gold: Mapping[str, DataFrame]) -> dict[str, DataFrame]:
    """Apply the same bundled SQL used by the Databricks setup guide.

    Unique input views live until the Spark session ends, so lazy Spark Connect
    plans remain resolvable. Only aggregated, explicitly selected columns leave
    Spark. revenue_by_customer is aggregated into histogram bins inside Spark;
    customer-level rows, names, IDs and source segments never leave Spark.
    """
    prefix = f"medallion_dashboard_{uuid4().hex}"
    views = {name: f"{prefix}_{name}" for name in _TABLES}
    for name in _TABLES:
        gold[name].createOrReplaceTempView(views[name])
    spark = gold["sales_by_product"].sparkSession
    return {
        name: spark.sql(sql) for name, sql in dashboard_queries(views).items()
    }


def _json_default(value: object) -> str:
    if isinstance(value, Decimal):
        return format(value, ".2f")
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Unsupported dashboard value: {type(value).__name__}")


def _safe_json(value: object) -> str:
    return (
        json.dumps(value, default=_json_default, ensure_ascii=True, allow_nan=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def _money(value: object) -> str:
    return f"{Decimal(str(value)):,.2f}"


def _chart(
    rows: list[dict], label: str, value: str, *, monetary: bool = True, limit: int = 20
) -> str:
    display = rows[:limit]
    maximum = max((Decimal(str(row[value])) for row in display), default=Decimal(0))
    bars = []
    for row in display:
        amount = Decimal(str(row[value]))
        width = Decimal(0) if maximum == 0 else amount / maximum * 100
        formatted = _money(amount) if monetary else str(row[value])
        text = f"{row[label]}: {formatted}"
        bars.append(
            '<div class="bar-row">'
            f'<span class="bar-label">{escape(str(row[label]))}</span>'
            '<span class="bar-track">'
            f'<span class="bar" style="width:{width:.2f}%"></span></span>'
            f'<span class="bar-value">{escape(formatted)}</span>'
            f'<span class="sr-only">{escape(text)}</span></div>'
        )
    return (
        f'<div class="bars" data-visible-limit="{limit}" role="img" aria-label="'
        + escape("; ".join(f"{row[label]}: {row[value]}" for row in display), quote=True)
        + '">'
        + ("".join(bars) if bars else "<p>No matching data.</p>")
        + "</div>"
    )


def _histogram(rows: list[dict]) -> str:
    maximum = max((row["customer_count"] for row in rows), default=0)
    description = "; ".join(
        f'{row["revenue_bin"]}: {row["customer_count"]} customers' for row in rows
    )
    parts = [
        '<svg class="histogram" viewBox="0 0 720 280" role="img" '
        'aria-labelledby="histogram-title histogram-description">',
        "<title id=\"histogram-title\">Customer revenue distribution histogram</title>",
        f'<desc id="histogram-description">{escape(description or "No valid customers")}</desc>',
        '<line class="axis" x1="60" y1="215" x2="690" y2="215"/>',
        '<line class="axis" x1="60" y1="25" x2="60" y2="215"/>',
        '<text class="chart-text" x="50" y="219" text-anchor="end">0</text>',
        '<text class="chart-text" x="60" y="15">Customers</text>',
    ]
    width = 630 / max(len(rows), 1)
    for index, row in enumerate(rows):
        count = row["customer_count"]
        height = count / maximum * 170 if maximum else 0
        x = 60 + index * width
        parts.extend(
            (
                f'<rect class="histogram-bin" data-bin-order="{row["bin_order"]}" '
                f'x="{x:.2f}" y="{215-height:.2f}" width="{width:.2f}" height="{height:.2f}"/>',
                f'<text class="chart-text" x="{x+width/2:.2f}" y="{205-height:.2f}" '
                f'text-anchor="middle">{count}</text>',
                f'<text class="chart-text" x="{x+width/2:.2f}" y="238" '
                f'text-anchor="middle">{escape(row["revenue_bin"])}</text>',
            )
        )
    parts.append(
        '<text class="chart-text" x="375" y="270" text-anchor="middle">'
        "Customer revenue (source currency units; final bin is overflow)</text></svg>"
    )
    return "".join(parts)


def _pie(rows: list[dict]) -> str:
    total = sum(row["customer_count"] for row in rows)
    description = "; ".join(
        f'{row["segment_type"]}: {row["customer_count"]} customers' for row in rows
    )
    colors = ("--accent", "--ink", "--muted", "--border")
    parts = [
        '<div class="pie-layout"><svg class="segmentation-pie" viewBox="0 0 200 200" '
        'role="img" aria-labelledby="pie-title pie-description">',
        '<title id="pie-title">Customer segmentation pie chart</title>',
        f'<desc id="pie-description">{escape(description)}'
        + ("; No valid customers" if total == 0 else "")
        + "</desc>",
        '<circle class="pie-track" cx="100" cy="100" r="70" fill="none" stroke-width="45"/>',
        '<g transform="rotate(-90 100 100)">',
    ]
    offset = Decimal(0)
    legend = []
    for index, row in enumerate(rows):
        percentage = (
            Decimal(row["customer_count"]) / Decimal(total) * 100 if total else Decimal(0)
        )
        color = colors[index % len(colors)]
        parts.append(
            f'<circle class="pie-segment" data-segment="{escape(row["segment_type"], quote=True)}" '
            'cx="100" cy="100" r="70" fill="none" stroke-width="45" pathLength="100" '
            f'style="stroke:var({color})" stroke-dasharray="{percentage:.8f} {100-percentage:.8f}" '
            f'stroke-dashoffset="{-offset:.8f}"/>'
        )
        offset += percentage
        legend.append(
            '<li><span class="legend-swatch" aria-hidden="true" '
            f'style="background:var({color})"></span>'
            f'{escape(row["segment_type"])}: {row["customer_count"]} ({percentage:.1f}%)</li>'
        )
    parts.extend(
        (
            '</g><text class="pie-total" x="100" y="97" text-anchor="middle">'
            f'{total}</text><text class="chart-text" x="100" y="116" text-anchor="middle">'
            'customers</text></svg><ul class="pie-legend" aria-label="Segment counts">',
            "".join(legend),
            "</ul></div>",
        )
    )
    if total == 0:
        parts.append("<p>No valid customers; all four segment counts are zero.</p>")
    return "".join(parts)


def _table(rows: list[dict], label: str, value: str) -> str:
    result = [
        '<details><summary>Accessible data table (all matching rows)</summary>',
        '<table><caption>Chart data</caption><thead><tr>',
        f'<th scope="col">{escape(label.replace("_", " ").title())}</th>',
        f'<th scope="col">{escape(value.replace("_", " ").title())}</th>',
        "</tr></thead><tbody>",
    ]
    for row in rows:
        result.append(
            f'<tr><th scope="row">{escape(str(row[label]))}</th>'
            f'<td>{escape(str(row[value]))}</td></tr>'
        )
    result.append("</tbody></table></details>")
    return "".join(result)


def _section(
    identifier: str,
    title: str,
    subtitle: str,
    rows: list[dict],
    label: str,
    value: str,
    *,
    monetary: bool = True,
    chart_type: str = "bar",
    limit: int = 20,
) -> str:
    chart = (
        _histogram(rows) if chart_type == "histogram"
        else _pie(rows) if chart_type == "pie"
        else _chart(rows, label, value, monetary=monetary, limit=limit)
    )
    return (
        f'<section data-chart-type="{chart_type}" aria-labelledby="{identifier}-title">'
        f'<h2 id="{identifier}-title">{escape(title)}</h2>'
        f"<p>{escape(subtitle)}</p>"
        f'<div id="{identifier}">'
        + chart
        + _table(rows, label, value)
        + "</div></section>"
    )


_STYLE = """
:root { --ink:#182b3a; --muted:#405668; --paper:#f3f6f8; --card:#fff;
        --accent:#176b87; --track:#dbe8ef; --border:#afc2cf; }
* { box-sizing:border-box; } body { margin:0; background:var(--paper);
  color:var(--ink); font:16px/1.5 system-ui,sans-serif; }
main { max-width:1300px; margin:auto; padding:1.5rem; }
h1,h2 { line-height:1.2; } h2 { font-size:1.25rem; }
p { color:var(--muted); } .filters { display:flex; gap:1rem; flex-wrap:wrap;
  padding:1rem 0; } label { display:flex; flex-direction:column; font-weight:600; }
select,button { padding:.6rem; color:var(--ink); background:var(--card);
  border:1px solid var(--border); border-radius:4px; font:inherit; max-width:100%; }
button { align-self:end; cursor:pointer; } :focus-visible {
  outline:3px solid var(--accent); outline-offset:2px; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,480px),1fr));
  gap:1rem; } section,.summary { background:var(--card); padding:1rem;
  border:1px solid var(--border); border-radius:8px; }
.summary { margin-bottom:1rem; } .bar-row { display:grid;
  grid-template-columns:minmax(90px,1fr) 2fr minmax(60px,auto);
  gap:.5rem; align-items:center; padding:.3rem 0; }
.bar-label { overflow-wrap:anywhere; font-size:.85rem; }
.bar-track { background:var(--track); height:16px; }
.bar { background:var(--accent); display:block; height:100%; }
.bar-value { text-align:right; font-variant-numeric:tabular-nums; font-size:.85rem; }
.histogram { display:block; width:100%; height:auto; }
.histogram-bin { fill:var(--accent); stroke:var(--card); stroke-width:1; }
.axis { stroke:var(--ink); stroke-width:1; }
.chart-text { fill:var(--ink); font:12px system-ui,sans-serif; }
.pie-layout { display:flex; align-items:center; flex-wrap:wrap; gap:1rem; }
.segmentation-pie { width:220px; max-width:100%; height:auto; }
.pie-track { stroke:var(--track); } .pie-total { fill:var(--ink); font-size:24px; }
.pie-legend { padding:0; list-style:none; } .pie-legend li { margin:.4rem 0; }
.legend-swatch { display:inline-block; width:14px; height:14px; margin-right:.5rem;
  border:1px solid var(--ink); }
details { margin-top:1rem; overflow:auto; } summary { cursor:pointer; }
table { border-collapse:collapse; width:100%; } th,td {
  text-align:left; padding:.4rem; border-bottom:1px solid var(--border); }
.sr-only { position:absolute; width:1px; height:1px; padding:0; overflow:hidden;
  clip:rect(0,0,0,0); white-space:nowrap; border:0; }
"""

_SCRIPT = """
(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('dashboard-data').textContent);
  const category = document.getElementById('category-filter');
  const product = document.getElementById('product-filter');
  const grain = document.getElementById('grain-filter');
  const el = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  };
  // Use integer cents for filtered totals; Number is used only for bar widths.
  const cents = value => BigInt(String(value).replace('.', ''));
  const decimal = value => `${value / 100n}.${String(value % 100n).padStart(2, '0')}`;
  const money = value => {
    const [whole, part = '00'] = String(value).split('.');
    return whole.replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',') + '.' + part.padEnd(2, '0');
  };
  function options(node, values, allLabel) {
    node.replaceChildren();
    const all = el('option', allLabel); all.value = ''; node.append(all);
    for (const [value, label] of values) {
      const item = el('option', label); item.value = String(value); node.append(item);
    }
  }
  function draw(id, rows, label, value, monetary = true, limit = 20) {
    const root = document.getElementById(id);
    root.replaceChildren();
    const display = rows.slice(0, limit);
    const maximum = Math.max(0, ...display.map(row => Number(row[value])));
    const bars = el('div', undefined, 'bars');
    bars.dataset.visibleLimit = String(limit);
    bars.setAttribute('role', 'img');
    bars.setAttribute('aria-label', display.map(row => `${row[label]}: ${row[value]}`).join('; ') || 'No matching data');
    if (!display.length) bars.append(el('p', 'No matching data.'));
    for (const row of display) {
      const barRow = el('div', undefined, 'bar-row');
      const track = el('span', undefined, 'bar-track');
      const bar = el('span', undefined, 'bar');
      bar.style.width = `${maximum ? Number(row[value]) / maximum * 100 : 0}%`;
      track.append(bar);
      barRow.append(el('span', String(row[label]), 'bar-label'), track,
        el('span', monetary ? money(row[value]) : String(row[value]), 'bar-value'));
      bars.append(barRow);
    }
    const details = el('details');
    details.append(el('summary', 'Accessible data table (all matching rows)'));
    const table = el('table'); table.append(el('caption', 'Chart data'));
    const head = el('thead'), heading = el('tr');
    for (const field of [label, value]) {
      const cell = el('th', field.replaceAll('_', ' ')); cell.scope = 'col'; heading.append(cell);
    }
    head.append(heading); table.append(head);
    const body = el('tbody');
    for (const row of rows) {
      const tr = el('tr'), th = el('th', String(row[label])); th.scope = 'row';
      tr.append(th, el('td', String(row[value]))); body.append(tr);
    }
    table.append(body); details.append(table); root.append(bars, details);
  }
  function resetProducts() {
    const rows = data.products.filter(row => !category.value || row.category === category.value);
    options(product, rows.map(row => [row.product_id, `${row.product_name} (#${row.product_id})`]), 'All products');
  }
  function updateProducts() {
    const rows = data.products.filter(row =>
      (!category.value || row.category === category.value) &&
      (!product.value || String(row.product_id) === product.value));
    const totals = new Map();
    for (const row of rows) {
      const previous = totals.get(row.category) || 0n;
      totals.set(row.category, previous + cents(row.total_revenue));
    }
    const categories = [...totals].map(([category, total]) =>
      ({category, total_revenue:decimal(total)})).sort((a,b) =>
      cents(a.total_revenue) === cents(b.total_revenue) ? a.category.localeCompare(b.category) :
      cents(a.total_revenue) > cents(b.total_revenue) ? -1 : 1);
    draw('products-chart', rows, 'product_name', 'total_revenue', true, 10);
    draw('categories-chart', categories, 'category', 'total_revenue');
    const revenue = rows.reduce((sum, row) => sum + cents(row.total_revenue), 0n);
    const orders = rows.reduce((sum, row) => sum + BigInt(row.total_orders), 0n);
    document.getElementById('selection-summary').textContent =
      `${rows.length} matching products · ${orders} eligible orders · Revenue ${money(decimal(revenue))}`;
  }
  function updateTrends() {
    const rows = data.trends.filter(row => row.period_type === grain.value);
    draw('trends-chart', rows.slice(-20), 'period_start', 'total_revenue');
    document.getElementById('trend-note').textContent =
      `${grain.value === 'weekly' ? 'Monday-start weeks' : 'Days'}: latest 20 periods with eligible sales. Entire snapshot; unaffected by product/category filters.`;
  }
  options(category, [...new Set(data.products.map(row => row.category))].sort().map(value => [value, value]), 'All categories');
  resetProducts();
  category.addEventListener('change', () => { resetProducts(); updateProducts(); });
  product.addEventListener('change', updateProducts);
  grain.addEventListener('change', updateTrends);
  document.getElementById('reset-filters').addEventListener('click', () => {
    category.value = ''; resetProducts(); grain.value = 'daily'; updateProducts(); updateTrends();
  });
  updateProducts(); updateTrends();
})();
"""


def render_dashboard(
    gold: Mapping[str, DataFrame], output: Path, *, run_id: str
) -> dict:
    """Write a populated, offline .html file and return a JSON-safe manifest.

    The file contains top-10 product bars, a binned customer-revenue histogram,
    a customer segmentation pie, category bars and daily/weekly trends.
    Filters affect product/category charts and their summary; customer histogram,
    trend and segment charts are explicitly labelled as unfiltered.
    Decimal money is serialized as strings. The runner supplies a snapshot run ID.
    """
    output = Path(output)
    if output.suffix.lower() != ".html":
        raise ValueError("output must be an .html file path")
    datasets = {
        name: [row.asDict(recursive=True) for row in frame.collect()]
        for name, frame in dashboard_datasets(gold).items()
    }
    if not datasets["segments"]:
        datasets["segments"] = [
            {
                "segment_type": name, "segment_order": index, "customer_count": 0,
                "total_orders": 0, "total_revenue": Decimal("0.00"),
                "avg_revenue": Decimal("0.00"), "avg_order_value": Decimal("0.00"),
            }
            for index, name in enumerate(("High-Value", "Repeat", "One-Time", "Inactive"), 1)
        ]
    products = datasets["products"]
    revenue = sum((row["total_revenue"] for row in products), Decimal("0.00"))
    orders = sum(row["total_orders"] for row in products)
    trends = [row for row in datasets["trends"] if row["period_type"] == "daily"][-20:]
    sections = (
        _section(
            "products-chart", "Top 10 products by revenue",
            "Product/category filters apply. Top 10 matching products by revenue; table includes all matches.",
            products, "product_name", "total_revenue", limit=10,
        )
        + _section(
            "histogram-chart", "Customer revenue distribution",
            "Entire snapshot; product/category filters do not apply. Bins include their lower bound "
            "and exclude their upper bound; 2000+ is overflow. Zero-revenue customers are included.",
            datasets["customer_revenue_distribution"], "revenue_bin", "customer_count",
            monetary=False, chart_type="histogram",
        )
        + _section(
            "categories-chart", "Revenue by category",
            "Product/category filters apply; totals are recomputed from selected products.",
            datasets["categories"], "category", "total_revenue",
        )
        + _section(
            "trends-chart", "Revenue over time",
            "Latest 20 days with eligible sales. Entire snapshot; product/category filters do not apply.",
            trends, "period_start", "total_revenue",
        )
        + _section(
            "segments-chart", "Customer segmentation",
            "Entire snapshot; product/category filters do not apply. Segments partition valid customers.",
            datasets["segments"], "segment_type", "customer_count",
            monetary=False, chart_type="pie",
        )
    )
    html = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        "script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; "
        'base-uri \'none\'; form-action \'none\'">'
        "<title>Medallion sales dashboard</title><style>" + _STYLE + "</style></head>"
        "<body><main><h1>Quality-aware sales dashboard</h1>"
        f"<p>Snapshot run: <strong>{escape(str(run_id))}</strong></p>"
        "<p>Revenue uses Completed orders with PASS order, customer and product. "
        "Amounts are source currency units; no currency conversion is assumed.</p>"
        '<div class="filters" role="group" aria-label="Dashboard filters">'
        '<label for="category-filter">Category<select id="category-filter">'
        '<option value="">All categories</option></select></label>'
        '<label for="product-filter">Product<select id="product-filter">'
        '<option value="">All products</option></select></label>'
        '<label for="grain-filter">Trend grain<select id="grain-filter">'
        '<option value="daily">Daily</option><option value="weekly">Weekly (Monday start)</option>'
        '</select></label><button id="reset-filters" type="button">Reset filters</button></div>'
        '<p id="filter-scope">Category and product filter only the product/category charts '
        "and summary. Histogram and segmentation cover all valid customers. "
        "Trend grain affects only the trend chart.</p>"
        '<div class="summary" id="selection-summary" role="status" aria-live="polite">'
        f"{len(products)} matching products · {orders} eligible orders · Revenue {_money(revenue)}"
        '</div><p id="trend-note">Days: latest 20 periods with eligible sales. Entire snapshot.</p>'
        '<noscript><p>Charts and data tables are populated. Enable JavaScript for interactive filters.</p>'
        '</noscript><div class="grid">' + sections + "</div>"
        '<p>No raw customer names, emails, or order records are embedded.</p></main>'
        '<script id="dashboard-data" type="application/json">' + _safe_json(datasets)
        + "</script><script>" + _SCRIPT + "</script></body></html>"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return {
        "path": str(output.resolve()),
        "run_id": str(run_id),
        "chart_count": 5,
        "dataset_rows": {name: len(rows) for name, rows in datasets.items()},
        "total_revenue": format(revenue, ".2f"),
        "total_orders": orders,
        "offline": True,
    }

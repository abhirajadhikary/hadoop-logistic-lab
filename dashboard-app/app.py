"""
app.py
------
Gradio dashboard for the Gold Logistics data set. Pulls shipment_snapshot,
delivery_performance and route_optimization from backend.py (FastAPI) and
renders a single-page Power BI style report: KPI card visuals, a slicer
row that cross-filters every chart and table, and a report canvas with
bordered visual tiles. Colors are Streamlit's own brand tokens (the red
primary #FF4B4B plus its documented gray scale) rather than Gradio's
default palette.
"""

import os
import datetime
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gradio as gr

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# Color palette - Streamlit's own brand tokens:
#   primary red  #FF4B4B
#   gray-200     #F0F2F6  (light backgrounds)
#   gray-600     #A3A8B4  (muted text)
#   gray-900     #262730  (dark text)
# Red is reserved for the things that should draw the eye (brand accent,
# delayed shipments, value at risk); gray carries everything else.
# ---------------------------------------------------------------------------
RED = "#FF4B4B"
RED_DARK = "#D9363E"
RED_LIGHT = "#FF8A8A"
GRAY_50 = "#F3F2F1"     # report canvas background (Power BI's light gray canvas)
GRAY_100 = "#F0F2F6"    # streamlit gray-200
GRAY_300 = "#E1E1E1"    # card borders
GRAY_600 = "#A3A8B4"    # streamlit gray-600, muted text
GRAY_900 = "#262730"    # streamlit gray-900, dark text

CHART_COLORWAY = [RED, GRAY_600, RED_DARK, RED_LIGHT, "#5B5F66"]
FONT_STACK = "'Segoe UI', 'Segoe UI Web', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif"


def style_fig(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_STACK, size=12, color=TEXT_PRIMARY),
        title_font=dict(family=FONT_STACK, size=14, color=TEXT_PRIMARY),
        margin=dict(l=10, r=10, t=40, b=10),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.18, font=dict(color=TEXT_MUTED)),
        colorway=CHART_COLORWAY,
    )
    fig.update_xaxes(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER, color=TEXT_MUTED)
    fig.update_yaxes(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER, color=TEXT_MUTED)
    return fig


def empty_fig(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=13, color=TEXT_MUTED))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return style_fig(fig, height=320)


# ---------------------------------------------------------------------------
# Data fetch + shaping
# ---------------------------------------------------------------------------
def fetch_all():
    resp = requests.get(f"{BACKEND_URL}/all-data", timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    shipments = pd.DataFrame(payload.get("shipments", []))
    performance = pd.DataFrame(payload.get("performance", []))
    routes = pd.DataFrame(payload.get("routes", []))

    if not shipments.empty and "last_updated_at" in shipments:
        shipments["last_updated_at"] = pd.to_datetime(shipments["last_updated_at"], errors="coerce")

    if not performance.empty:
        for col in ("delivered_time", "picked_up_time", "shipping_date"):
            if col in performance:
                performance[col] = pd.to_datetime(performance[col], errors="coerce")
        if "is_delayed" in performance:
            performance["is_delayed"] = performance["is_delayed"].astype(bool)

    return shipments, performance, routes


def unique_sorted(*series_list) -> list:
    values = set()
    for s in series_list:
        if s is not None and not s.empty:
            values.update(s.dropna().unique().tolist())
    return sorted(str(v) for v in values)


# ---------------------------------------------------------------------------
# Slicer filtering
# ---------------------------------------------------------------------------
def apply_filters(df: pd.DataFrame, origin_sel: str, dest_sel: str, delayed_sel: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    filtered = df
    if origin_sel and origin_sel != "All" and "origin" in filtered.columns:
        filtered = filtered[filtered["origin"] == origin_sel]
    if dest_sel and dest_sel != "All" and "destination" in filtered.columns:
        filtered = filtered[filtered["destination"] == dest_sel]
    if delayed_sel and delayed_sel != "All" and "is_delayed" in filtered.columns:
        want = delayed_sel == "Delayed"
        filtered = filtered[filtered["is_delayed"] == want]
    return filtered


def filter_df(df: pd.DataFrame, query: str) -> pd.DataFrame:
    if df is None or df.empty or not query or not query.strip():
        return df
    query = query.strip()
    mask = df.apply(lambda col: col.astype(str).str.contains(query, case=False, na=False))
    return df[mask.any(axis=1)]


# ---------------------------------------------------------------------------
# KPI card visuals
# ---------------------------------------------------------------------------
def kpi_card(label: str, value: str) -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """


def build_kpi_html(shipments: pd.DataFrame, performance: pd.DataFrame, routes: pd.DataFrame) -> str:
    total_shipments = len(shipments) if not shipments.empty else 0

    in_transit = 0
    if not shipments.empty and "current_status" in shipments:
        in_transit = int((~shipments["current_status"].isin(["Delivered", "Cancelled"])).sum())

    if not performance.empty and "is_delayed" in performance and len(performance) > 0:
        delayed_count = int(performance["is_delayed"].sum())
        on_time_pct = 100 * (1 - delayed_count / len(performance))
    else:
        delayed_count = 0
        on_time_pct = 0.0

    total_value_at_risk = routes["total_value_at_risk"].sum() if "total_value_at_risk" in routes and not routes.empty else 0

    cards = [
        kpi_card("Total Shipments", f"{total_shipments:,}"),
        kpi_card("In Transit", f"{in_transit:,}"),
        kpi_card("On-Time Rate", f"{on_time_pct:.1f}%"),
        kpi_card("Delayed Shipments", f"{delayed_count:,}"),
        kpi_card("Value at Risk", f"${total_value_at_risk:,.0f}"),
    ]
    timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %H:%M UTC")
    meta = f'<div class="meta-bar">Showing {total_shipments:,} shipments &middot; Report rendered {timestamp}</div>'
    return meta + f'<div class="kpi-grid">{"".join(cards)}</div>'


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def fig_status_distribution(shipments: pd.DataFrame) -> go.Figure:
    if shipments.empty or "current_status" not in shipments:
        return empty_fig("No shipment status data")
    counts = shipments["current_status"].value_counts().reset_index()
    counts.columns = ["status", "count"]
    fig = px.pie(counts, names="status", values="count", hole=0.55, title="Shipment Status Mix")
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return style_fig(fig)


def fig_delay_split(performance: pd.DataFrame) -> go.Figure:
    if performance.empty or "is_delayed" not in performance:
        return empty_fig("No delivery performance data")
    counts = performance["is_delayed"].map({True: "Delayed", False: "On Time"}).value_counts().reset_index()
    counts.columns = ["outcome", "count"]
    fig = px.pie(counts, names="outcome", values="count", hole=0.55, title="On-Time vs Delayed",
                 color="outcome", color_discrete_map={"On Time": GRAY_600, "Delayed": RED})
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return style_fig(fig)


def fig_top_locations(df: pd.DataFrame, col: str, title: str) -> go.Figure:
    if df.empty or col not in df:
        return empty_fig(f"No {col} data")
    counts = df[col].value_counts().head(10).sort_values()
    fig = px.bar(counts, x=counts.values, y=counts.index, orientation="h", title=title,
                  labels={"x": "Shipments", "y": ""})
    fig.update_traces(marker_color=RED)
    return style_fig(fig)


def fig_duration_histogram(performance: pd.DataFrame) -> go.Figure:
    if performance.empty or "delivery_duration_days" not in performance:
        return empty_fig("No delivery duration data")
    fig = px.histogram(performance, x="delivery_duration_days", nbins=20,
                        title="Delivery Duration Distribution",
                        labels={"delivery_duration_days": "Days to Deliver"})
    fig.update_traces(marker_color=RED)
    return style_fig(fig)


def fig_value_at_risk_by_location(routes: pd.DataFrame) -> go.Figure:
    if routes.empty or "total_value_at_risk" not in routes or "location" not in routes:
        return empty_fig("No route risk data")
    agg = routes.groupby("location")["total_value_at_risk"].sum().nlargest(10).sort_values()
    fig = px.bar(agg, x=agg.values, y=agg.index, orientation="h", title="Top 10 Value at Risk by Location",
                  labels={"x": "Value at Risk ($)", "y": ""})
    fig.update_traces(marker_color=RED_DARK)
    return style_fig(fig)


def fig_shipment_trend(performance: pd.DataFrame) -> go.Figure:
    if performance.empty or "shipping_date" not in performance:
        return empty_fig("No shipping date data")
    daily = performance.dropna(subset=["shipping_date"]).groupby("shipping_date").size().reset_index(name="count")
    daily = daily.sort_values("shipping_date")
    if daily.empty:
        return empty_fig("No shipping date data")
    fig = px.area(daily, x="shipping_date", y="count", title="Shipment Volume Over Time", markers=True,
                   labels={"shipping_date": "Date", "count": "Shipments"})
    fig.update_traces(
        line=dict(color=RED, width=2.5),
        fillgradient=dict(
            type="vertical",
            colorscale=[[0, "rgba(255,75,75,0.45)"], [1, "rgba(255,75,75,0.0)"]],
        ),
    )
    return style_fig(fig, height=300)


def fig_top_routes(routes: pd.DataFrame) -> go.Figure:
    if routes.empty or not {"origin", "destination", "total_shipments"}.issubset(routes.columns):
        return empty_fig("No route data")
    agg = (routes.groupby(["origin", "destination"])["total_shipments"]
           .sum().reset_index())
    agg["route"] = agg["origin"] + " \u2192 " + agg["destination"]
    agg = agg.nlargest(10, "total_shipments").sort_values("total_shipments")
    fig = px.bar(agg, x="total_shipments", y="route", orientation="h", title="Top 10 Routes by Shipment Volume",
                  labels={"total_shipments": "Shipments", "route": ""})
    fig.update_traces(marker_color=RED)
    return style_fig(fig, height=300)


# ---------------------------------------------------------------------------
# Render pipeline - shared by the initial load and every slicer change.
# Returns (kpi_html, 8 figures, filtered shipments/performance/routes) = 12 items.
# ---------------------------------------------------------------------------
def render(shipments, performance, routes, origin_sel="All", dest_sel="All", delayed_sel="All"):
    f_ship = apply_filters(shipments, origin_sel, dest_sel, "All")
    f_perf = apply_filters(performance, origin_sel, dest_sel, delayed_sel)
    f_routes = apply_filters(routes, origin_sel, dest_sel, "All")

    kpi_html = build_kpi_html(f_ship, f_perf, f_routes)
    charts = (
        fig_status_distribution(f_ship),
        fig_delay_split(f_perf),
        fig_top_locations(f_perf, "origin", "Top 10 Origins by Shipments"),
        fig_top_locations(f_perf, "destination", "Top 10 Destinations by Shipments"),
        fig_duration_histogram(f_perf),
        fig_value_at_risk_by_location(f_routes),
        fig_shipment_trend(f_perf),
        fig_top_routes(f_routes),
    )
    return (kpi_html, *charts, f_ship, f_perf, f_routes)


def load_dashboard():
    """Fetch fresh data, populate slicer choices, and render the unfiltered view."""
    try:
        shipments, performance, routes = fetch_all()
    except Exception as exc:
        gr.Warning(f"Could not reach backend at {BACKEND_URL}: {exc}")
        empty = pd.DataFrame()
        blank = empty_fig("Backend unavailable")
        error_kpi = '<div class="kpi-grid"><div class="kpi-card"><div class="kpi-value">\u2014</div>' \
                    '<div class="kpi-label">Backend Unreachable</div></div></div>'
        blanks = (blank,) * 8
        return (error_kpi, *blanks, empty, empty, empty,   # kpi + 8 plots + 3 tables
                empty, empty, empty,                        # raw states
                empty, empty, empty,                        # visible states
                gr.update(choices=["All"], value="All"),
                gr.update(choices=["All"], value="All"),
                gr.update(value="All"))

    origin_choices = ["All"] + unique_sorted(
        shipments["origin"] if "origin" in shipments else pd.Series(dtype=str),
        performance["origin"] if "origin" in performance else pd.Series(dtype=str),
    )
    dest_choices = ["All"] + unique_sorted(
        shipments["destination"] if "destination" in shipments else pd.Series(dtype=str),
        performance["destination"] if "destination" in performance else pd.Series(dtype=str),
    )

    visuals = render(shipments, performance, routes)  # 12 items
    visible_ship, visible_perf, visible_routes = visuals[-3], visuals[-2], visuals[-1]

    return (
        *visuals,                                  # kpi + 8 plots + 3 tables (12)
        shipments, performance, routes,             # raw states (3)
        visible_ship, visible_perf, visible_routes,  # visible/search-base states (3)
        gr.update(choices=origin_choices, value="All"),
        gr.update(choices=dest_choices, value="All"),
        gr.update(value="All"),
    )


def on_filter_change(raw_shipments, raw_performance, raw_routes, origin_sel, dest_sel, delayed_sel):
    """Re-render every visual against the already-fetched data using the slicer values."""
    visuals = render(raw_shipments, raw_performance, raw_routes, origin_sel, dest_sel, delayed_sel)
    visible_ship, visible_perf, visible_routes = visuals[-3], visuals[-2], visuals[-1]
    return (*visuals, visible_ship, visible_perf, visible_routes)  # 12 + 3 = 15


# ---------------------------------------------------------------------------
# Styling - dark canvas, simple rounded-rectangle tiles. Streamlit's brand
# red is still the single accent color; everything else is dark neutrals.
# ---------------------------------------------------------------------------
BG_PAGE = "#0E1117"      # page background
BG_SURFACE = "#161B22"   # card / tile surface
BORDER = "#2A2F3A"       # subtle card border
TEXT_PRIMARY = "#F5F6F8"
TEXT_MUTED = "#8B93A1"

RADIUS = "14px"

CSS = f"""
.gradio-container, body {{
    background: {BG_PAGE} !important;
    font-family: {FONT_STACK} !important;
    color: {TEXT_PRIMARY} !important;
}}

/* ---------- header ---------- */
.dash-title {{
    font-size: 24px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    margin: 0;
}}
.dash-subtitle {{
    font-size: 13px;
    color: {TEXT_MUTED};
    margin-top: 2px;
}}
.dash-accent {{
    width: 46px;
    height: 4px;
    background: {RED};
    border-radius: 2px;
    margin-top: 10px;
}}

/* ---------- meta bar ---------- */
.meta-bar {{
    font-size: 12px;
    color: {TEXT_MUTED};
    margin: 4px 0 10px 2px;
}}

/* ---------- KPI card visuals ---------- */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin-bottom: 16px;
}}
.kpi-card {{
    background: {BG_SURFACE};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    padding: 16px 18px;
}}
.kpi-value {{
    font-size: 26px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    line-height: 1.15;
}}
.kpi-label {{
    font-size: 11px;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    color: {TEXT_MUTED};
    margin-top: 4px;
    font-weight: 600;
}}
@media (max-width: 1100px) {{
    .kpi-grid {{ grid-template-columns: repeat(3, 1fr); }}
}}
@media (max-width: 640px) {{
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}

/* ---------- report canvas visual tiles ---------- */
.chart-card {{
    background: {BG_SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS} !important;
    padding: 8px !important;
}}

/* ---------- filter / slicer panel ---------- */
.filter-panel {{
    background: {BG_SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS} !important;
    padding: 12px 14px 4px 14px !important;
    margin-bottom: 14px !important;
}}
.filters-label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: {TEXT_MUTED};
    margin: 0 0 6px 0;
}}

/* ---------- section labels ---------- */
.section-label {{
    font-size: 13px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    margin: 16px 0 6px 2px;
    padding-left: 8px;
    border-left: 3px solid {RED};
}}

/* ---------- misc gradio surfaces, kept simple & rounded ---------- */
.gr-button, button {{
    border-radius: {RADIUS} !important;
}}
input, select, textarea, .gr-dropdown, .gr-textbox {{
    border-radius: {RADIUS} !important;
}}
table {{
    border-radius: {RADIUS} !important;
}}
"""

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
with gr.Blocks(css=CSS, title="Logistics Dashboard", theme=gr.themes.Default(primary_hue="red", neutral_hue="gray")) as demo:

    with gr.Row():
        with gr.Column(scale=4):
            gr.HTML("""
            <div class="dash-title">Logistics Dashboard</div>
            <div class="dash-subtitle">Gold Logistics &middot; shipment, delivery, and route overview</div>
            <div class="dash-accent"></div>
            """)
        with gr.Column(scale=1, min_width=140):
            refresh_btn = gr.Button("Refresh Data", variant="primary")

    with gr.Group(elem_classes="filter-panel"):
        gr.HTML('<div class="filters-label">Filters</div>')
        with gr.Row():
            origin_dd = gr.Dropdown(choices=["All"], value="All", label="Origin")
            dest_dd = gr.Dropdown(choices=["All"], value="All", label="Destination")
            delayed_dd = gr.Dropdown(choices=["All", "Delayed", "On Time"], value="All", label="Delivery Status")

    kpi_html = gr.HTML()

    raw_shipments_state = gr.State(pd.DataFrame())
    raw_performance_state = gr.State(pd.DataFrame())
    raw_routes_state = gr.State(pd.DataFrame())
    visible_shipments_state = gr.State(pd.DataFrame())
    visible_performance_state = gr.State(pd.DataFrame())
    visible_routes_state = gr.State(pd.DataFrame())

    gr.HTML('<div class="section-label">Delivery Overview</div>')
    with gr.Row():
        with gr.Group(elem_classes="chart-card"):
            plot_status = gr.Plot()
        with gr.Group(elem_classes="chart-card"):
            plot_delay = gr.Plot()

    with gr.Row():
        with gr.Group(elem_classes="chart-card"):
            plot_origin = gr.Plot()
        with gr.Group(elem_classes="chart-card"):
            plot_destination = gr.Plot()

    with gr.Row():
        with gr.Group(elem_classes="chart-card"):
            plot_duration = gr.Plot()
        with gr.Group(elem_classes="chart-card"):
            plot_risk = gr.Plot()

    gr.HTML('<div class="section-label">Trends &amp; Routes</div>')
    with gr.Row():
        with gr.Group(elem_classes="chart-card"):
            plot_trend = gr.Plot()
        with gr.Group(elem_classes="chart-card"):
            plot_routes = gr.Plot()

    gr.HTML('<div class="section-label">Raw Data</div>')
    with gr.Tabs():
        with gr.TabItem("Shipments"):
            search_shipments = gr.Textbox(placeholder="Search shipments...", show_label=False)
            table_shipments = gr.Dataframe(wrap=True)
        with gr.TabItem("Delivery Performance"):
            search_performance = gr.Textbox(placeholder="Search performance...", show_label=False)
            table_performance = gr.Dataframe(wrap=True)
        with gr.TabItem("Route Optimization"):
            search_routes = gr.Textbox(placeholder="Search routes...", show_label=False)
            table_routes = gr.Dataframe(wrap=True)

    load_outputs = [
        kpi_html,
        plot_status, plot_delay, plot_origin, plot_destination,
        plot_duration, plot_risk, plot_trend, plot_routes,
        table_shipments, table_performance, table_routes,
        raw_shipments_state, raw_performance_state, raw_routes_state,
        visible_shipments_state, visible_performance_state, visible_routes_state,
        origin_dd, dest_dd, delayed_dd,
    ]
    refresh_btn.click(fn=load_dashboard, outputs=load_outputs)
    demo.load(fn=load_dashboard, outputs=load_outputs)

    filter_outputs = [
        kpi_html,
        plot_status, plot_delay, plot_origin, plot_destination,
        plot_duration, plot_risk, plot_trend, plot_routes,
        table_shipments, table_performance, table_routes,
        visible_shipments_state, visible_performance_state, visible_routes_state,
    ]
    filter_inputs = [raw_shipments_state, raw_performance_state, raw_routes_state, origin_dd, dest_dd, delayed_dd]
    origin_dd.change(fn=on_filter_change, inputs=filter_inputs, outputs=filter_outputs)
    dest_dd.change(fn=on_filter_change, inputs=filter_inputs, outputs=filter_outputs)
    delayed_dd.change(fn=on_filter_change, inputs=filter_inputs, outputs=filter_outputs)

    search_shipments.change(fn=filter_df, inputs=[visible_shipments_state, search_shipments], outputs=table_shipments)
    search_performance.change(fn=filter_df, inputs=[visible_performance_state, search_performance], outputs=table_performance)
    search_routes.change(fn=filter_df, inputs=[visible_routes_state, search_routes], outputs=table_routes)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
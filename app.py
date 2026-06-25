from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.explorer import PROFILES, build_universe, factor_breakdown, filter_universe, price_history, score_universe
from src.ui import apply_theme, close_surface, fmt_billions, fmt_bps, fmt_money, fmt_pct, render_surface_header


st.set_page_config(
    page_title="Market Explorer Demo",
    page_icon=":mag:",
    layout="wide",
)
apply_theme()


@st.cache_data
def load_snapshot(profile: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    snapshot = build_universe()
    scored = score_universe(snapshot.universe, profile=profile)
    return scored, snapshot.region_summary, snapshot.sector_summary


def themed_chart(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor="#647282",
            titleColor="#647282",
            gridColor="rgba(19, 33, 47, 0.08)",
            domainColor="rgba(19, 33, 47, 0.12)",
            tickColor="rgba(19, 33, 47, 0.12)",
        )
        .configure_legend(labelColor="#13212f", titleColor="#647282")
    )


profile = st.selectbox("Scoring Profile", list(PROFILES.keys()), index=0)
universe, region_summary, sector_summary = load_snapshot(profile)

st.markdown(
    (
        "<div class='hero'>"
        "<div class='hero-kicker'>Portfolio Project 04</div>"
        "<div class='hero-title'>Market Explorer Demo</div>"
        "<div class='hero-copy'>"
        "A stock universe explorer with filter, score, ranking, and detail workflows. "
        "The goal is to show product thinking around screeners: not just a table, but a way to narrow a universe, "
        "surface candidates, and explain why a name ranks where it does."
        "</div>"
        "<div class='hero-pills'>"
        "<span class='pill'>Universe explorer</span>"
        "<span class='pill'>Synthetic market data</span>"
        "<span class='pill'>Factor scoring</span>"
        "<span class='pill'>Ranking logic</span>"
        "<span class='pill'>Detail panel</span>"
        "</div>"
        "</div>"
    ),
    unsafe_allow_html=True,
)

filter_cols = st.columns([0.95, 1.05, 1.0, 0.8, 0.8, 0.8], gap="small")
with filter_cols[0]:
    region_filter = st.multiselect("Region", sorted(universe["region"].unique()), default=sorted(universe["region"].unique()))
with filter_cols[1]:
    sector_filter = st.multiselect("Sector", sorted(universe["sector"].unique()), default=sorted(universe["sector"].unique()))
with filter_cols[2]:
    bucket_filter = st.multiselect(
        "Market Cap Bucket",
        ["Mega Cap", "Large Cap", "Mid Cap", "Small Cap"],
        default=["Mega Cap", "Large Cap", "Mid Cap"],
    )
with filter_cols[3]:
    min_adv = st.slider("Min ADV ($M)", min_value=0, max_value=150, value=20, step=5)
with filter_cols[4]:
    max_spread = st.slider("Max Spread (bps)", min_value=5, max_value=40, value=24, step=1)
with filter_cols[5]:
    min_score = st.slider("Min Score", min_value=0, max_value=100, value=45, step=5)

filtered = filter_universe(
    universe,
    regions=region_filter,
    sectors=sector_filter,
    buckets=bucket_filter,
    min_adv=float(min_adv),
    max_spread=float(max_spread),
    min_score=float(min_score),
)
if filtered.empty:
    filtered = universe.head(0).copy()

top_symbol = filtered.iloc[0]["symbol"] if not filtered.empty else universe.iloc[0]["symbol"]
selected_symbol = st.selectbox("Focus Symbol", filtered["symbol"].tolist() if not filtered.empty else universe["symbol"].tolist(), index=0)
selected_row = (filtered if not filtered.empty else universe).loc[lambda frame: frame["symbol"] == selected_symbol].iloc[0]
detail_history = price_history(selected_symbol)
detail_breakdown = factor_breakdown(selected_row)

metric_cols = st.columns(5)
metric_cols[0].metric("Visible Names", f"{len(filtered):,}")
metric_cols[1].metric("Top Candidate", top_symbol)
metric_cols[2].metric("Median Score", f"{filtered['radar_score'].median():.1f}" if not filtered.empty else "n/a")
metric_cols[3].metric("Avg Spread", f"{filtered['spread_bps'].mean():.1f} bps" if not filtered.empty else "n/a")
metric_cols[4].metric("Avg ADV", fmt_money(float(filtered["adv_usd_m"].mean())) if not filtered.empty else "n/a")

top_left, top_right = st.columns([1.18, 0.82], gap="large")

with top_left:
    render_surface_header(
        "Universe Map",
        "Liquidity versus one-month momentum. Size is market cap, color is composite radar score.",
        label="Explorer",
    )
    scatter = (
        alt.Chart(filtered)
        .mark_circle(opacity=0.85, stroke="#ffffff", strokeWidth=0.8)
        .encode(
            x=alt.X("adv_usd_m:Q", title="ADV ($M)"),
            y=alt.Y("momentum_1m_pct:Q", title="1M Momentum %"),
            size=alt.Size("market_cap_b:Q", title="Market Cap ($B)", scale=alt.Scale(range=[120, 1500])),
            color=alt.Color(
                "radar_score:Q",
                title="Radar Score",
                scale=alt.Scale(domain=[35, 85], range=["#d7c6ad", "#0f766e"]),
            ),
            tooltip=[
                alt.Tooltip("symbol:N", title="Symbol"),
                alt.Tooltip("company:N", title="Company"),
                alt.Tooltip("region:N", title="Region"),
                alt.Tooltip("sector:N", title="Sector"),
                alt.Tooltip("radar_score:Q", title="Score", format=".1f"),
                alt.Tooltip("adv_usd_m:Q", title="ADV", format=".1f"),
                alt.Tooltip("spread_bps:Q", title="Spread", format=".1f"),
                alt.Tooltip("signal_tag:N", title="Signal"),
            ],
        )
        .properties(height=340)
    )
    st.altair_chart(themed_chart(scatter), use_container_width=True)

    heatmap = (
        alt.Chart(filtered)
        .mark_rect(cornerRadius=8)
        .encode(
            x=alt.X("sector:N", title=None, sort=sorted(filtered["sector"].unique())),
            y=alt.Y("region:N", title=None, sort=["US", "Europe", "Asia"]),
            color=alt.Color("mean(radar_score):Q", title="Avg Score", scale=alt.Scale(range=["#f1e6d1", "#244c7d"])),
            tooltip=[
                alt.Tooltip("region:N", title="Region"),
                alt.Tooltip("sector:N", title="Sector"),
                alt.Tooltip("mean(radar_score):Q", title="Avg Score", format=".1f"),
            ],
        )
        .properties(height=190)
    )
    st.altair_chart(themed_chart(heatmap), use_container_width=True)
    close_surface()

with top_right:
    render_surface_header(
        "Candidate Detail",
        "Use the detail pane to explain the rank, not just display it.",
        label="Detail",
    )
    st.markdown(
        (
            "<div class='detail-grid'>"
            f"<div class='metric-card'><div class='metric-label'>Symbol</div><div class='metric-value'>{selected_row['symbol']}</div></div>"
            f"<div class='metric-card'><div class='metric-label'>Signal</div><div class='metric-value'>{selected_row['signal_tag']}</div></div>"
            f"<div class='metric-card'><div class='metric-label'>Radar Rank</div><div class='metric-value'>#{int(selected_row['rank'])}</div></div>"
            f"<div class='metric-card'><div class='metric-label'>Composite Score</div><div class='metric-value'>{float(selected_row['radar_score']):.1f}</div></div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    detail_cols = st.columns(2)
    detail_cols[0].metric("Market Cap", fmt_billions(float(selected_row["market_cap_b"])))
    detail_cols[1].metric("ADV", fmt_money(float(selected_row["adv_usd_m"])))
    detail_cols[0].metric("Spread", fmt_bps(float(selected_row["spread_bps"])))
    detail_cols[1].metric("1M Momentum", fmt_pct(float(selected_row["momentum_1m_pct"])))
    detail_cols[0].metric("Volatility", f"{float(selected_row['vol_20d_pct']):.1f}%")
    detail_cols[1].metric("Value Gap", fmt_pct(float(selected_row["relative_value_pct"])))

    breakdown = (
        alt.Chart(detail_breakdown)
        .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
        .encode(
            y=alt.Y("pillar:N", title=None, sort=["Liquidity", "Momentum", "Quality", "Value"]),
            x=alt.X("score:Q", title="Factor score"),
            color=alt.Color(
                "pillar:N",
                scale=alt.Scale(
                    domain=["Liquidity", "Momentum", "Quality", "Value"],
                    range=["#0f766e", "#c26d34", "#244c7d", "#92734b"],
                ),
                legend=None,
            ),
            tooltip=[alt.Tooltip("pillar:N", title="Pillar"), alt.Tooltip("score:Q", title="Score", format=".1f")],
        )
        .properties(height=160)
    )
    st.altair_chart(themed_chart(breakdown), use_container_width=True)
    st.markdown(
        f"<div class='note'>{selected_row['company']} screens well because it combines {selected_row['score_note']}. "
        "This is synthetic data, but the product logic mirrors a real screener workflow: filter, score, rank, then explain.</div>",
        unsafe_allow_html=True,
    )
    close_surface()

bottom_left, bottom_right = st.columns([1.1, 0.9], gap="large")

with bottom_left:
    render_surface_header(
        "Price And Activity",
        "Synthetic detail series for the selected name. The chart is here to make the explorer feel like a product, not just a static ranking table.",
        label="History",
    )
    price_line = (
        alt.Chart(detail_history)
        .mark_line(color="#244c7d", strokeWidth=2.4, interpolate="monotone")
        .encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("close:Q", title="Close", scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("close:Q", title="Close", format=".2f"),
                alt.Tooltip("return_pct:Q", title="Return", format=".2f"),
                alt.Tooltip("drawdown_pct:Q", title="Drawdown", format=".2f"),
            ],
        )
        .properties(height=240)
    )
    volume_bar = (
        alt.Chart(detail_history)
        .mark_bar(color="#0f766e", opacity=0.45)
        .encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("volume_index:Q", title="Volume Index"),
            tooltip=[alt.Tooltip("date:T", title="Date"), alt.Tooltip("volume_index:Q", title="Volume", format=".1f")],
        )
        .properties(height=100)
    )
    st.altair_chart(themed_chart(alt.vconcat(price_line, volume_bar).resolve_scale(x="shared")), use_container_width=True)
    close_surface()

with bottom_right:
    render_surface_header(
        "Top Ranked Names",
        "The ranked board is what you would actually export, review, or monitor.",
        label="Board",
    )
    board = filtered.loc[
        :,
        [
            "rank",
            "symbol",
            "region",
            "sector",
            "radar_score",
            "signal_tag",
            "adv_usd_m",
            "spread_bps",
            "momentum_1m_pct",
            "relative_value_pct",
        ],
    ].head(15)
    st.dataframe(
        board.style.format(
            {
                "radar_score": "{:.1f}",
                "adv_usd_m": "{:.1f}",
                "spread_bps": "{:.1f}",
                "momentum_1m_pct": "{:+.1f}%",
                "relative_value_pct": "{:+.1f}%",
            }
        ),
        width="stretch",
        hide_index=True,
        height=388,
    )
    close_surface()

render_surface_header(
    "Universe Table",
    "Dense explorer view with ranking, score pillars, liquidity, volatility, and valuation context.",
    label="Universe",
)
st.dataframe(
    filtered.loc[
        :,
        [
            "rank",
            "symbol",
            "company",
            "region",
            "sector",
            "market_cap_bucket",
            "radar_score",
            "liquidity_score",
            "momentum_score",
            "quality_score",
            "value_score",
            "adv_usd_m",
            "spread_bps",
            "vol_20d_pct",
            "score_note",
        ],
    ].style.format(
        {
            "radar_score": "{:.1f}",
            "liquidity_score": "{:.1f}",
            "momentum_score": "{:.1f}",
            "quality_score": "{:.1f}",
            "value_score": "{:.1f}",
            "adv_usd_m": "{:.1f}",
            "spread_bps": "{:.1f}",
            "vol_20d_pct": "{:.1f}%",
        }
    ),
    width="stretch",
    hide_index=True,
    height=420,
)
close_surface()

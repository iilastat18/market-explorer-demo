from __future__ import annotations

import streamlit as st


APP_CSS = """
<style>
    :root {
        --bg: #f5f1e8;
        --bg-soft: #ede7da;
        --panel: rgba(255, 252, 247, 0.92);
        --ink: #13212f;
        --muted: #647282;
        --line: rgba(19, 33, 47, 0.10);
        --line-strong: rgba(19, 33, 47, 0.18);
        --accent: #0f766e;
        --accent-2: #244c7d;
        --good: #1d8f6b;
        --warn: #bb6b1c;
        --bad: #b34a4a;
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(36, 76, 125, 0.08), transparent 24%),
            radial-gradient(circle at top right, rgba(15, 118, 110, 0.08), transparent 20%),
            linear-gradient(180deg, var(--bg) 0%, #f7f4ed 100%);
        color: var(--ink);
    }
    #MainMenu,
    header[data-testid="stHeader"],
    [data-testid="stSidebarNav"] {
        display: none;
    }
    [data-testid="stAppViewContainer"] {
        background: transparent;
    }
    .block-container {
        max-width: 1460px;
        padding-top: 0.85rem;
        padding-bottom: 2rem;
    }
    .hero {
        border: 1px solid var(--line-strong);
        border-radius: 22px;
        background: linear-gradient(135deg, rgba(255,252,247,0.96), rgba(245, 241, 232, 0.92));
        box-shadow: 0 18px 42px rgba(23, 35, 50, 0.08);
        padding: 1.2rem 1.25rem;
        margin-bottom: 0.9rem;
    }
    .hero-kicker {
        color: var(--accent-2);
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-size: 0.72rem;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }
    .hero-title {
        color: var(--ink);
        font-size: 2.2rem;
        line-height: 1.0;
        font-weight: 820;
        margin-bottom: 0.35rem;
    }
    .hero-copy {
        color: var(--muted);
        font-size: 0.92rem;
        line-height: 1.6;
        max-width: 66rem;
    }
    .hero-pills {
        margin-top: 0.75rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.42rem;
    }
    .pill {
        display: inline-block;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.66);
        color: var(--ink);
        font-size: 0.74rem;
        font-weight: 750;
        padding: 0.25rem 0.56rem;
    }
    .surface {
        border: 1px solid var(--line);
        border-radius: 18px;
        background: rgba(255, 252, 247, 0.88);
        box-shadow: 0 12px 28px rgba(23, 35, 50, 0.06);
        padding: 0.9rem 0.95rem 0.95rem;
        margin-bottom: 0.85rem;
        backdrop-filter: blur(8px);
    }
    .surface-label {
        display: inline-block;
        border-radius: 999px;
        background: rgba(15, 118, 110, 0.10);
        color: var(--accent);
        padding: 0.18rem 0.45rem;
        font-size: 0.68rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }
    .panel-title {
        color: var(--ink);
        font-size: 1rem;
        font-weight: 760;
        margin-bottom: 0.16rem;
    }
    .panel-copy {
        color: var(--muted);
        font-size: 0.84rem;
        margin-bottom: 0.55rem;
        line-height: 1.55;
    }
    .metric-band,
    .detail-grid {
        display: grid;
        gap: 0.55rem;
        margin-bottom: 0.65rem;
    }
    .metric-band {
        grid-template-columns: repeat(4, minmax(0, 1fr));
    }
    .detail-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .metric-card {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.56);
        padding: 0.62rem 0.7rem;
    }
    .metric-label {
        color: var(--muted);
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.14rem;
    }
    .metric-value {
        color: var(--ink);
        font-size: 0.98rem;
        font-weight: 800;
    }
    .note {
        border: 1px dashed var(--line-strong);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.46);
        padding: 0.62rem 0.7rem;
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.55;
    }
    div[data-testid="stMetric"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.70);
        padding: 0.62rem 0.7rem;
    }
    div[data-testid="stMetricLabel"] *, .stCaption, .stMarkdown p, .stMarkdown li {
        color: var(--muted);
    }
    div[data-testid="stMetricValue"] * {
        color: var(--ink);
    }
    div[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid var(--line);
    }
    .stButton > button {
        border-radius: 12px;
        border: 1px solid var(--line);
        background: linear-gradient(180deg, #fffdfa 0%, #f2ebe0 100%);
        color: var(--ink);
        min-height: 2.35rem;
        font-weight: 760;
    }
    .stButton > button:hover {
        border-color: rgba(15, 118, 110, 0.24);
        color: var(--accent);
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    .stNumberInput > div > div {
        background: rgba(255, 255, 255, 0.72);
        border-color: var(--line);
        color: var(--ink);
    }
    @media (max-width: 980px) {
        .metric-band,
        .detail-grid {
            grid-template-columns: 1fr;
        }
        .hero-title {
            font-size: 1.85rem;
        }
    }
</style>
"""


def apply_theme() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_surface_header(title: str, copy: str, label: str | None = None) -> None:
    st.markdown("<div class='surface'>", unsafe_allow_html=True)
    if label:
        st.markdown(f"<div class='surface-label'>{label}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel-copy'>{copy}</div>", unsafe_allow_html=True)


def close_surface() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def fmt_money(value: float) -> str:
    return f"${value:,.1f}M"


def fmt_billions(value: float) -> str:
    return f"${value:,.1f}B"


def fmt_pct(value: float) -> str:
    return f"{value:+.1f}%"


def fmt_bps(value: float) -> str:
    return f"{value:.1f} bps"

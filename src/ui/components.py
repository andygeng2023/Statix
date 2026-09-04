from __future__ import annotations

import html
from urllib.parse import quote as urlquote

import numpy as np
import pandas as pd
import streamlit as st

from src.config import TEXT


def t(key, lang):
    return TEXT.get(lang, TEXT["en"]).get(key, TEXT["en"].get(key, key))


def money(value, symbol="$", decimals=2):
    if value is None:
        return "—"
    try:
        return f"{symbol}{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def number(value, decimals=2):
    if value is None:
        return "—"
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def pct(value, decimals=2, signed=True):
    if value is None:
        return "—"
    try:
        prefix = "+" if signed and float(value) > 0 else ""
        return f"{prefix}{float(value):,.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"


def score(value, decimals=2):
    if value is None:
        return "—"
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"


def _sparkline_svg(df: pd.DataFrame | None, width=640, height=120) -> str:
    if df is None or df.empty or "close" not in df.columns:
        return ""

    values = pd.to_numeric(df["close"], errors="coerce").dropna().tail(80).to_numpy(dtype=float)
    if len(values) < 2:
        return ""

    finite = np.isfinite(values)
    values = values[finite]
    if len(values) < 2:
        return ""

    lo = float(values.min())
    hi = float(values.max())
    span = hi - lo or 1.0

    points = []
    for i, value in enumerate(values):
        x = 4 + (width - 8) * i / (len(values) - 1)
        y = height - 8 - (height - 16) * (value - lo) / span
        points.append(f"{x:.1f},{y:.1f}")

    return (
        f'<svg class="statix-spark" viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none" aria-hidden="true">'
        f'<polyline points="{" ".join(points)}" fill="none" '
        f'stroke="currentColor" stroke-width="2.4" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
        f"</svg>"
    )


def clickable_card(
    ticker: str,
    name: str | None,
    price: float | None,
    change_pct: float | None,
    df: pd.DataFrame | None = None,
    signal: str | None = None,
    confidence: float | None = None,
    reliability: float | None = None,
    expected_return: float | None = None,
    page: str = "stocks",
):
    """Render a complete clickable card using a normal URL query.

    Keeping the whole card as one <a> means the user does not need a
    separate button. app.py reads page/ticker from st.query_params.
    """
    symbol = str(ticker).upper()
    href = f"?page={urlquote(page)}&ticker={urlquote(symbol)}"

    safe_symbol = html.escape(symbol)
    safe_name = html.escape(name or "")
    spark = _sparkline_svg(df)

    stats = [
        f'<span><b>{money(price)}</b></span>',
        f'<span>{pct(change_pct)}</span>',
    ]

    prediction = ""
    if signal:
        pieces = [f"<b>{html.escape(str(signal))}</b>"]
        if confidence is not None:
            pieces.append(f"Confidence {score(confidence)}")
        if reliability is not None:
            pieces.append(f"Reliability {score(reliability)}")
        if expected_return is not None:
            pieces.append(f"Expected {pct(expected_return * 100)}")
        prediction = '<div class="statix-card-prediction">' + " · ".join(pieces) + "</div>"

    st.markdown(
        f'''
        <a class="statix-card-link" href="{href}">
            <article class="statix-card">
                <div class="statix-card-head">
                    <div>
                        <div class="statix-ticker">{safe_symbol}</div>
                        <div class="statix-name">{safe_name}</div>
                    </div>
                    <div class="statix-arrow">↗</div>
                </div>
                <div class="statix-card-stats">{"".join(stats)}</div>
                {f'<div class="statix-chart">{spark}</div>' if spark else ''}
                {prediction}
            </article>
        </a>
        ''',
        unsafe_allow_html=True,
    )


def inject_theme_css():
    st.markdown(
        """
        <style>
        /* =========================================================
           Statix system-aware navy theme
           ========================================================= */
        :root {
            --statix-bg: #f3f7ff;
            --statix-surface: rgba(255,255,255,.42);
            --statix-border: rgba(20,43,82,.14);
            --statix-text: #102040;
            --statix-muted: #5d6d89;
            --statix-accent: #4159a8;
            --statix-accent-soft: #7187d2;
            --statix-hover: rgba(55,77,145,.08);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --statix-bg: #081426;
                --statix-surface: rgba(13,31,56,.28);
                --statix-border: rgba(157,180,222,.16);
                --statix-text: #e7eefc;
                --statix-muted: #91a3c2;
                --statix-accent: #7f96e8;
                --statix-accent-soft: #9caef0;
                --statix-hover: rgba(126,149,225,.08);
            }
        }

        .stApp {
            background: var(--statix-bg);
            color: var(--statix-text);
        }

        .block-container {
            max-width: 1440px;
            padding-top: 2.25rem;
            padding-bottom: 4rem;
        }

        .brand {
            font-size: 1.7rem;
            font-weight: 850;
            letter-spacing: -.05em;
        }

        .muted { color: var(--statix-muted); }

        /* Professional, transparent cards. */
        .statix-card-link {
            display: block;
            text-decoration: none !important;
            color: inherit !important;
            margin-bottom: 1rem;
        }

        .statix-card {
            background: transparent;
            border: 1px solid var(--statix-border);
            border-radius: 12px;
            padding: 22px 24px;
            min-height: 255px;
            box-sizing: border-box;
            transition: border-color .16s ease, background .16s ease,
                        transform .16s ease, box-shadow .16s ease;
        }

        .statix-card:hover {
            border-color: var(--statix-accent);
            background: var(--statix-hover);
            transform: translateY(-2px);
            box-shadow: 0 12px 30px rgba(14,35,70,.10);
        }

        .statix-card-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
        }

        .statix-ticker {
            font-size: 1.25rem;
            font-weight: 760;
            letter-spacing: -.02em;
        }

        .statix-name {
            margin-top: 3px;
            color: var(--statix-muted);
            font-size: .9rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 280px;
        }

        .statix-arrow {
            color: var(--statix-accent);
            font-size: 1.2rem;
            font-weight: 700;
        }

        .statix-card-stats {
            display: flex;
            gap: 18px;
            align-items: baseline;
            margin-top: 20px;
            font-size: .98rem;
        }

        .statix-card-stats b {
            font-size: 1.35rem;
        }

        .statix-chart {
            height: 105px;
            margin-top: 16px;
            color: var(--statix-accent);
            opacity: .92;
        }

        .statix-spark {
            width: 100%;
            height: 100%;
        }

        .statix-card-prediction {
            color: var(--statix-muted);
            font-size: .82rem;
            margin-top: 12px;
            line-height: 1.45;
        }

        /* Sliding-tab appearance, implemented with buttons so navigation
           can switch pages programmatically. */
        .statix-nav-spacer {
            height: 1px;
            background: var(--statix-border);
            margin-top: -1px;
            margin-bottom: 24px;
        }

        div[data-testid="stHorizontalBlock"] div.stButton > button {
            background: transparent !important;
            border: 0 !important;
            border-bottom: 3px solid transparent !important;
            border-radius: 0 !important;
            color: var(--statix-muted) !important;
            font-weight: 650 !important;
            min-height: 45px !important;
            box-shadow: none !important;
        }

        div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
            color: var(--statix-accent-soft) !important;
            border-bottom-color: var(--statix-accent-soft) !important;
        }

        .statix-active-nav {
            height: 3px;
            margin-top: -3px;
            background: var(--statix-accent);
            border-radius: 2px;
        }

        [data-testid="stMetricValue"] {
            font-variant-numeric: tabular-nums;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

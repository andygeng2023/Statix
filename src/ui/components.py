from __future__ import annotations

import html
import json

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
        n = float(value)
        prefix = "+" if signed and n > 0 else ""
        return f"{prefix}{n:,.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"


def score(value, decimals=2):
    if value is None:
        return "—"
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"


def _sparkline_svg(df: pd.DataFrame | None, width=700, height=150) -> str:
    if df is None or df.empty:
        return ""

    # Accept common column names.
    column = None
    for candidate in ("close", "Close", "adj_close", "Adj Close"):
        if candidate in df.columns:
            column = candidate
            break

    if column is None:
        return ""

    values = (
        pd.to_numeric(df[column], errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .tail(80)
        .to_numpy(dtype=float)
    )

    if len(values) < 2:
        return ""

    lo = float(np.min(values))
    hi = float(np.max(values))
    span = hi - lo

    if not np.isfinite(span) or span <= 0:
        span = 1.0

    points = []

    for i, value in enumerate(values):
        x = 5 + (width - 10) * i / (len(values) - 1)
        y = height - 10 - (height - 20) * (value - lo) / span
        points.append(f"{x:.1f},{y:.1f}")

    return f"""
    <svg class="statix-spark"
         viewBox="0 0 {width} {height}"
         preserveAspectRatio="none"
         aria-hidden="true">
        <polyline
            points="{' '.join(points)}"
            fill="none"
            stroke="currentColor"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"/>
    </svg>
    """


def _navigate_script(page: str, ticker: str) -> str:
    payload = json.dumps(
        {
            "page": page,
            "ticker": str(ticker).upper(),
        }
    )

    return f"""
    <script>
    (() => {{
        const target = {payload};
        const params = new URLSearchParams();
        params.set("page", target.page);
        if (target.ticker) {{
            params.set("ticker", target.ticker);
        }}

        const url = window.parent.location.pathname + "?" + params.toString();

        window.parent.location.assign(url);
    }})();
    </script>
    """


def card_html(
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
) -> str:

    symbol = str(ticker).upper()

    safe_symbol = html.escape(symbol)
    safe_name = html.escape(name or symbol)

    spark = _sparkline_svg(df)

    prediction = ""

    if signal:
        pieces = [
            f"<strong>{html.escape(str(signal))}</strong>"
        ]

        if confidence is not None:
            pieces.append(f"Confidence {score(confidence)}")

        if reliability is not None:
            pieces.append(f"Reliability {score(reliability)}")

        if expected_return is not None:
            pieces.append(
                f"Expected {pct(float(expected_return) * 100)}"
            )

        prediction = (
            '<div class="statix-card-prediction">'
            + " · ".join(pieces)
            + "</div>"
        )

    script = _navigate_script(page, symbol)

    return f"""
    <div
        class="statix-card-link"
        role="button"
        tabindex="0"
        onclick="{html.escape(script, quote=True)}"
    >
        <div class="statix-card">
            <div class="statix-card-head">
                <div class="statix-card-title">
                    <div class="statix-ticker">{safe_symbol}</div>
                    <div class="statix-name">{safe_name}</div>
                </div>

                <div class="statix-arrow">↗</div>
            </div>

            <div class="statix-card-stats">
                <span>
                    <strong>{money(price)}</strong>
                </span>
                <span>{pct(change_pct)}</span>
            </div>

            <div class="statix-chart">
                {spark}
            </div>

            {prediction}
        </div>
    </div>
    """


def card_row(items: list[dict]):
    if not items:
        return

    cards = "".join(card_html(**item) for item in items)

    st.html(
        f"""
        <div class="statix-card-row">
            {cards}
        </div>
        """,
        unsafe_allow_javascript=True,
    )


def bottom_nav_html(page: str, labels: dict[str, str]) -> str:
    buttons = []

    for key, label in labels.items():
        active = "active" if page == key else ""

        buttons.append(
            f"""
            <button
                class="statix-bottom-nav-item {active}"
                onclick="window.parent.location.assign(
                    window.parent.location.pathname + '?page={key}'
                )"
            >
                {html.escape(label)}
            </button>
            """
        )

    return f"""
    <nav class="statix-bottom-nav">
        {''.join(buttons)}
    </nav>
    """


def inject_theme_css():
    st.markdown(
        """
        <style>

        :root {
            --statix-bg: #f3f7ff;
            --statix-border: rgba(20,43,82,.14);
            --statix-text: #102040;
            --statix-muted: #5d6d89;
            --statix-accent: #4159a8;
            --statix-hover: rgba(65,89,168,.08);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --statix-bg: #081426;
                --statix-border: rgba(157,180,222,.16);
                --statix-text: #e7eefc;
                --statix-muted: #91a3c2;
                --statix-accent: #8da4f2;
                --statix-hover: rgba(126,149,225,.10);
            }
        }

        .stApp {
            background: var(--statix-bg);
            color: var(--statix-text);
        }

        .block-container {
            max-width: 1500px;
            padding-top: 2rem;
            padding-bottom: 7rem;
        }

        .statix-card-row {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 20px !important;

            width: 100% !important;
            max-width: 100% !important;

            overflow-x: auto !important;
            overflow-y: hidden !important;

            padding: 6px 4px 18px !important;
            margin-bottom: 28px !important;

            scrollbar-width: thin;
            -webkit-overflow-scrolling: touch;
        }

        .statix-card-link {
            display: block !important;

            flex: 0 0 390px !important;
            width: 390px !important;
            min-width: 390px !important;

            cursor: pointer !important;
            color: inherit !important;
            text-decoration: none !important;
        }

        .statix-card {
            width: 100%;
            min-height: 270px;

            box-sizing: border-box;

            padding: 24px 26px;

            background: transparent;

            border: 1px solid var(--statix-border);
            border-radius: 10px;

            transition:
                border-color .15s ease,
                background .15s ease,
                transform .15s ease,
                box-shadow .15s ease;
        }

        .statix-card-link:hover .statix-card {
            border-color: var(--statix-accent);
            background: var(--statix-hover);
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(10,30,65,.10);
        }

        .statix-card-head {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px;
        }

        .statix-card-title {
            min-width: 0;
        }

        .statix-ticker {
            font-size: 1.35rem;
            font-weight: 780;
            letter-spacing: -.02em;
        }

        .statix-name {
            margin-top: 4px;
            color: var(--statix-muted);
            font-size: .9rem;

            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .statix-arrow {
            color: var(--statix-muted);
            font-size: 1.25rem;
        }

        .statix-card-stats {
            display: flex;
            justify-content: space-between;
            align-items: baseline;

            margin-top: 22px;

            font-size: 1rem;
            font-variant-numeric: tabular-nums;
        }

        .statix-card-stats strong {
            font-size: 1.45rem;
        }

        .statix-chart {
            display: block;

            width: 100%;
            height: 115px;

            margin-top: 18px;

            color: var(--statix-accent);
        }

        .statix-spark {
            display: block;

            width: 100%;
            height: 100%;
        }

        .statix-card-prediction {
            margin-top: 12px;

            color: var(--statix-muted);

            font-size: .82rem;
            line-height: 1.45;
        }

        .statix-bottom-nav {
            position: fixed;

            left: 0;
            right: 0;
            bottom: 0;

            z-index: 999999;

            display: grid;
            grid-template-columns: repeat(4, 1fr);

            background: var(--statix-bg);

            border-top: 1px solid var(--statix-border);

            padding:
                8px
                max(12px, env(safe-area-inset-right))
                calc(8px + env(safe-area-inset-bottom))
                max(12px, env(safe-area-inset-left));

            backdrop-filter: blur(18px);
        }

        .statix-bottom-nav-item {
            border: 0 !important;
            border-radius: 0 !important;

            background: transparent !important;

            color: var(--statix-muted) !important;

            padding: 13px 6px !important;

            font: inherit !important;
            font-weight: 700 !important;

            cursor: pointer !important;
        }

        .statix-bottom-nav-item:hover,
        .statix-bottom-nav-item.active {
            color: var(--statix-text) !important;
        }

        @media (max-width: 700px) {

            .statix-card-link {
                flex-basis: 340px !important;
                width: 340px !important;
                min-width: 340px !important;
            }

            .statix-card {
                min-height: 245px;
            }

            .statix-chart {
                height: 100px;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )
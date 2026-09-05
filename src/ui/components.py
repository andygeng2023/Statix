from __future__ import annotations

import html
import json
from urllib.parse import quote

import numpy as np
import pandas as pd
import streamlit as st

from src.config import TEXT


def t(key: str, lang: str) -> str:
    return TEXT.get(lang, TEXT["en"]).get(
        key,
        TEXT["en"].get(key, key),
    )


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

        if not np.isfinite(n):
            return "—"

        prefix = "+" if signed and n > 0 else ""
        return f"{prefix}{n:,.{decimals}f}%"

    except (TypeError, ValueError):
        return "—"


def score(value, decimals=2):
    if value is None:
        return "—"

    try:
        n = float(value)

        if not np.isfinite(n):
            return "—"

        return f"{n * 100:.{decimals}f}%"

    except (TypeError, ValueError):
        return "—"


def _sparkline_svg(
    df: pd.DataFrame | None,
    expected_return: float | None = None,
    width: int = 640,
    height: int = 110,
) -> str:
    """
    Creates a bounded SVG sparkline.

    The important part here is that the SVG has a fixed viewBox and the
    containing element clips overflow, so the graph cannot escape the card.
    """

    if df is None or df.empty or "close" not in df.columns:
        return ""

    values = (
        pd.to_numeric(
            df["close"],
            errors="coerce",
        )
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
        y = height - 7 - (
            (height - 14) * (value - lo) / span
        )

        x = max(0, min(width, x))
        y = max(0, min(height, y))

        points.append(f"{x:.1f},{y:.1f}")

    forecast = ""

    if expected_return is not None:
        try:
            expected = float(expected_return)

            if np.isfinite(expected):
                forecast_value = values[-1] * (1 + expected)

                forecast_x = width - 5
                forecast_y = height - 7 - (
                    (height - 14)
                    * (forecast_value - lo)
                    / span
                )

                forecast_y = max(
                    7,
                    min(height - 7, forecast_y),
                )

                last_x, last_y = points[-1].split(",")

                forecast = (
                    f'<line '
                    f'x1="{last_x}" '
                    f'y1="{last_y}" '
                    f'x2="{forecast_x:.1f}" '
                    f'y2="{forecast_y:.1f}" '
                    f'class="statix-forecast-line" />'
                )

        except (TypeError, ValueError):
            pass

    point_string = " ".join(points)

    return f"""
        <svg
            class="statix-spark"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 {width} {height}"
            preserveAspectRatio="none"
            aria-hidden="true"
        >
            <polyline
                points="{point_string}"
                class="statix-history-line"
            />
            {forecast}
        </svg>
    """


def _safe_js_url(ticker: str) -> str:
    ticker = str(ticker).upper().strip()

    url = f"?page=stocks&ticker={quote(ticker)}"

    return json.dumps(url)


def _card_html(item: dict) -> str:
    ticker = str(
        item.get("ticker", "")
    ).upper()

    name = html.escape(
        str(item.get("name") or ticker)
    )

    price = money(item.get("price"))
    change = pct(item.get("change_pct"))

    signal = item.get("signal")

    expected = item.get(
        "expected_return"
    )

    spark = _sparkline_svg(
        item.get("df"),
        expected,
    )

    prediction_html = ""

    if signal:
        prediction_html = f"""
            <div class="statix-card-prediction">
                <span class="statix-signal">
                    {html.escape(str(signal))}
                </span>
                <span>
                    Confidence {score(item.get("confidence"))}
                </span>
                <span>
                    Reliability {score(item.get("reliability"))}
                </span>
            </div>
        """

    chart_html = ""

    if spark:
        chart_html = f"""
            <div class="statix-chart">
                {spark}
            </div>
        """

    js_url = _safe_js_url(ticker)

    return f"""
        <div
            class="statix-card-link"
            role="button"
            tabindex="0"
            onclick='window.top.location.href={js_url}'
            onkeydown='if(event.key==="Enter" || event.key===" ") {{
                event.preventDefault();
                window.top.location.href={js_url};
            }}'
        >
            <div class="statix-card">

                <div class="statix-card-head">

                    <div class="statix-card-title">
                        <div class="statix-ticker">
                            {html.escape(ticker)}
                        </div>

                        <div class="statix-name">
                            {name}
                        </div>
                    </div>

                    <div class="statix-card-chevron">
                        ›
                    </div>

                </div>

                <div class="statix-card-stats">

                    <span class="statix-price">
                        {price}
                    </span>

                    <span class="statix-change">
                        {change}
                    </span>

                </div>

                {chart_html}

                {prediction_html}

            </div>
        </div>
    """


def card_row(
    items: list[dict],
    key_prefix: str = "card",
):
    if not items:
        return

    cards = "".join(
        _card_html(item)
        for item in items
    )

    st.html(
        f"""
        <div class="statix-card-scroll">
            {cards}
        </div>
        """,
    )


def bottom_navigation(
    page: str,
    labels: dict[str, str],
):
    """
    Render a genuinely fixed app navigation bar.

    It is deliberately not a fixed Streamlit container. That prevents
    Streamlit's layout container from accidentally pinning unrelated
    content to the bottom of the page.
    """

    nav_items = []

    for key, label in labels.items():

        active_class = (
            " statix-bottom-active"
            if page == key
            else ""
        )

        url = f"?page={quote(key)}"

        nav_items.append(
            f"""
            <button
                class="statix-bottom-item{active_class}"
                onclick="window.top.location.href={json.dumps(url)}"
                aria-label="{html.escape(label)}"
            >
                <span class="statix-bottom-label">
                    {html.escape(label)}
                </span>
            </button>
            """
        )

    st.html(
        f"""
        <div class="statix-bottom-nav">
            <div class="statix-bottom-inner">
                {"".join(nav_items)}
            </div>
        </div>
        """,
    )


def inject_theme_css():
    st.markdown(
        """
        <style>

        :root {
            --statix-bg: #f4f7fc;
            --statix-surface: rgba(255,255,255,.42);
            --statix-border: rgba(24,45,82,.14);
            --statix-border-strong: rgba(24,45,82,.22);
            --statix-text: #102040;
            --statix-muted: #64738d;
            --statix-accent: #4159a8;
            --statix-accent-soft: #7187d2;
            --statix-hover: rgba(65,89,168,.055);
            --statix-positive: #267a55;
            --statix-negative: #b34b4b;
            --statix-nav-bg: rgba(244,247,252,.90);
        }

        @media (prefers-color-scheme: dark) {

            :root {
                --statix-bg: #071426;
                --statix-surface: rgba(14,31,56,.30);
                --statix-border: rgba(164,184,220,.14);
                --statix-border-strong: rgba(164,184,220,.23);
                --statix-text: #e8eefb;
                --statix-muted: #91a3c1;
                --statix-accent: #8298e9;
                --statix-accent-soft: #a0b0ed;
                --statix-hover: rgba(130,152,233,.075);
                --statix-positive: #67bb8e;
                --statix-negative: #e28383;
                --statix-nav-bg: rgba(7,20,38,.90);
            }

        }

        html,
        body {
            background: var(--statix-bg) !important;
        }

        .stApp {
            background: var(--statix-bg);
            color: var(--statix-text);
        }

        .block-container {
            max-width: 1500px;
            padding-top: 2.2rem;
            padding-bottom: 6.5rem;
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none;
        }

        /*
         * Global typography
         */

        h1 {
            letter-spacing: -.035em !important;
            font-weight: 700 !important;
        }

        h2,
        h3 {
            letter-spacing: -.025em !important;
            font-weight: 620 !important;
        }

        [data-testid="stCaptionContainer"] {
            color: var(--statix-muted);
        }

        [data-testid="stMetricValue"] {
            font-variant-numeric: tabular-nums;
        }

        /*
         * Streamlit controls
         */

        div[data-testid="stButton"] > button {
            min-height: 42px;
            border-radius: 7px;
            font-weight: 600;
            box-shadow: none;
            transition:
                border-color .15s ease,
                background .15s ease,
                transform .15s ease;
        }

        div[data-testid="stButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: none;
        }

        /*
         * Card scrolling area
         */

        .statix-card-scroll {
            display: flex;
            flex-direction: row;
            flex-wrap: nowrap;
            align-items: stretch;
            gap: 14px;

            width: 100%;
            max-width: 100%;

            overflow-x: auto;
            overflow-y: hidden;

            box-sizing: border-box;

            padding:
                3px
                4px
                16px
                3px;

            scrollbar-width: thin;
            overscroll-behavior-x: contain;
            scroll-snap-type: x proximity;
        }

        .statix-card-scroll::-webkit-scrollbar {
            height: 6px;
        }

        .statix-card-scroll::-webkit-scrollbar-thumb {
            background: var(--statix-border-strong);
            border-radius: 10px;
        }

        /*
         * Clickable card
         */

        .statix-card-link {
            display: block;

            flex: 0 0 270px;
            width: 270px;
            min-width: 270px;

            color: inherit;
            text-decoration: none;

            cursor: pointer;

            scroll-snap-align: start;

            box-sizing: border-box;
        }

        .statix-card {
            width: 100%;
            height: 218px;
            min-height: 218px;

            box-sizing: border-box;

            padding: 18px 19px;

            background: var(--statix-surface);

            border: 1px solid var(--statix-border-strong);

            border-radius: 10px;

            overflow: hidden;

            display: flex;
            flex-direction: column;

            transition:
                border-color .16s ease,
                background .16s ease,
                transform .16s ease,
                box-shadow .16s ease;

            contain: layout paint;
        }

        .statix-card-link:hover .statix-card,
        .statix-card-link:focus-visible .statix-card {
            border-color: var(--statix-accent);
            background: var(--statix-hover);
            transform: translateY(-2px);
            box-shadow:
                0 8px 24px rgba(16,32,64,.10);
        }

        .statix-card-link:focus-visible {
            outline: none;
        }

        .statix-card-link:focus-visible .statix-card {
            outline: 2px solid var(--statix-accent);
            outline-offset: 2px;
        }

        .statix-card-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;

            min-width: 0;
        }

        .statix-card-title {
            min-width: 0;
            overflow: hidden;
        }

        .statix-ticker {
            color: var(--statix-text);

            font-size: 1.08rem;
            line-height: 1.2;

            font-weight: 720;

            letter-spacing: -.018em;
        }

        .statix-name {
            margin-top: 4px;

            color: var(--statix-muted);

            font-size: .80rem;
            line-height: 1.25;

            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .statix-card-chevron {
            flex: 0 0 auto;

            color: var(--statix-muted);

            font-size: 1.45rem;
            line-height: 1;

            margin-top: -2px;
        }

        .statix-card-stats {
            display: flex;
            align-items: baseline;
            justify-content: space-between;

            gap: 10px;

            margin-top: 15px;

            font-variant-numeric: tabular-nums;
        }

        .statix-price {
            color: var(--statix-text);

            font-size: 1.24rem;
            line-height: 1;

            font-weight: 650;

            letter-spacing: -.02em;
        }

        .statix-change {
            color: var(--statix-text);

            font-size: .88rem;
            font-weight: 560;
        }

        /*
         * Graph
         */

        .statix-chart {
            width: 100%;
            height: 78px;

            min-height: 78px;
            max-height: 78px;

            margin-top: 14px;

            overflow: hidden;

            box-sizing: border-box;

            color: var(--statix-accent);

            opacity: .90;

            flex: 0 0 78px;
        }

        .statix-spark {
            display: block;

            width: 100%;
            max-width: 100%;

            height: 100%;
            max-height: 100%;

            overflow: hidden;
        }

        .statix-history-line {
            fill: none;

            stroke: currentColor;
            stroke-width: 2.2;

            stroke-linecap: round;
            stroke-linejoin: round;

            vector-effect: non-scaling-stroke;
        }

        .statix-forecast-line {
            fill: none;

            stroke: var(--statix-accent-soft);
            stroke-width: 2;

            stroke-dasharray: 6 5;

            stroke-linecap: round;

            vector-effect: non-scaling-stroke;
        }

        /*
         * Prediction metadata
         */

        .statix-card-prediction {
            display: flex;
            flex-wrap: wrap;

            gap: 4px 10px;

            margin-top: 10px;

            color: var(--statix-muted);

            font-size: .73rem;
            line-height: 1.3;

            font-variant-numeric: tabular-nums;

            overflow: hidden;
        }

        .statix-signal {
            color: var(--statix-text);
            font-weight: 650;
        }

        /*
         * Section spacing
         */

        .statix-section-description {
            margin-top: -8px;
            margin-bottom: 10px;
        }

        /*
         * Bottom application navigation
         *
         * Only this element is fixed.
         */

        .statix-bottom-nav {
            position: fixed;

            z-index: 99999;

            left: 0;
            right: 0;
            bottom: 0;

            width: 100%;

            box-sizing: border-box;

            padding:
                8px
                max(12px, calc((100vw - 1500px) / 2));

            background: var(--statix-nav-bg);

            border-top: 1px solid var(--statix-border);

            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
        }

        .statix-bottom-inner {
            display: flex;

            width: 100%;
            max-width: 1500px;

            margin: 0 auto;

            gap: 4px;
        }

        .statix-bottom-item {
            position: relative;

            flex: 1 1 0;

            min-width: 0;

            height: 48px;

            border: 0;
            border-radius: 7px;

            background: transparent;

            color: var(--statix-muted);

            cursor: pointer;

            font: inherit;

            transition:
                background .15s ease,
                color .15s ease;
        }

        .statix-bottom-item:hover {
            background: var(--statix-hover);
            color: var(--statix-text);
        }

        .statix-bottom-active {
            color: var(--statix-text);
            font-weight: 650;
        }

        .statix-bottom-active::before {
            content: "";

            position: absolute;

            top: 0;
            left: 28%;
            right: 28%;

            height: 2px;

            border-radius: 2px;

            background: var(--statix-accent);
        }

        .statix-bottom-label {
            display: block;

            text-align: center;

            font-size: .80rem;
            line-height: 48px;

            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /*
         * Inputs
         */

        input,
        textarea,
        [data-baseweb="select"] > div {
            border-radius: 7px !important;
        }

        /*
         * Mobile
         */

        @media (max-width: 700px) {

            .block-container {
                padding-top: 1.25rem;
                padding-left: 1rem;
                padding-right: 1rem;
                padding-bottom: 6.5rem;
            }

            .statix-card-link {
                flex-basis: 260px;
                width: 260px;
                min-width: 260px;
            }

            .statix-card {
                height: 210px;
                min-height: 210px;
            }

            .statix-chart {
                height: 72px;
                min-height: 72px;
                max-height: 72px;
                flex-basis: 72px;
            }

            .statix-bottom-nav {
                padding-left: 8px;
                padding-right: 8px;
            }

            .statix-bottom-label {
                font-size: .74rem;
            }

        }

        </style>
        """,
        unsafe_allow_html=True,
    )
from __future__ import annotations

import html

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


def _sparkline_svg(df: pd.DataFrame | None, width=640, height=120) -> str:
    if df is None or df.empty or "close" not in df.columns:
        return ""

    values = (
        pd.to_numeric(df["close"], errors="coerce")
        .dropna()
        .tail(80)
        .to_numpy(dtype=float)
    )

    values = values[np.isfinite(values)]

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
) -> str:

    symbol = str(ticker).upper()

    safe_symbol = html.escape(symbol, quote=True)
    safe_name = html.escape(name or symbol, quote=True)

    spark = _sparkline_svg(df)

    prediction = ""

    if signal:
        pieces = [f"<b>{html.escape(str(signal))}</b>"]

        if confidence is not None:
            pieces.append(f"Confidence {score(confidence)}")

        if reliability is not None:
            pieces.append(f"Reliability {score(reliability)}")

        if expected_return is not None:
            pieces.append(
                f"Expected {pct(expected_return * 100)}"
            )

        prediction = (
            '<div class="statix-card-prediction">'
            + " · ".join(pieces)
            + "</div>"
        )

    return f"""
    <div class="statix-card">
        <div class="statix-card-head">
            <div>
                <div class="statix-ticker">{safe_symbol}</div>
                <div class="statix-name">{safe_name}</div>
            </div>
            <div class="statix-arrow">↗</div>
        </div>

        <div class="statix-card-stats">
            <span><b>{money(price)}</b></span>
            <span>{pct(change_pct)}</span>
        </div>

        {f'<div class="statix-chart">{spark}</div>' if spark else ""}

        {prediction}
    </div>
    """


def card_row(items: list[dict], key_prefix: str = "card"):
    if not items:
        return

    # Horizontal scrolling container.
    st.markdown('<div class="statix-scroll-row">', unsafe_allow_html=True)

    for index, item in enumerate(items):
        ticker = str(item["ticker"]).upper()

        left, right = st.columns([9, 1], gap="small")

        with left:
            st.html(
                card_html(
                    ticker=ticker,
                    name=item.get("name"),
                    price=item.get("price"),
                    change_pct=item.get("change_pct"),
                    df=item.get("df"),
                    signal=item.get("signal"),
                    confidence=item.get("confidence"),
                    reliability=item.get("reliability"),
                    expected_return=item.get("expected_return"),
                )
            )

        with right:
            if st.button(
                "↗",
                key=f"{key_prefix}_{ticker}_{index}",
                help=f"Open {ticker}",
                use_container_width=True,
            ):
                st.session_state["page"] = "stocks"
                st.session_state["selected_ticker"] = ticker
                st.query_params.clear()
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def bottom_navigation(page: str, labels: dict[str, str]):
    st.markdown(
        '<div class="statix-bottom-spacer"></div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(4, gap="small")

    for col, key in zip(cols, labels):
        with col:
            active = page == key

            if st.button(
                labels[key],
                key=f"bottom_nav_{key}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state["page"] = key
                st.session_state.pop("selected_ticker", None)
                st.query_params.clear()
                st.rerun()


def inject_theme_css():
    st.markdown(
        """
        <style>

        :root {
            --statix-bg:#f3f7ff;
            --statix-border:rgba(20,43,82,.14);
            --statix-text:#102040;
            --statix-muted:#5d6d89;
            --statix-accent:#4159a8;
            --statix-hover:rgba(55,77,145,.08);
        }

        @media (prefers-color-scheme:dark) {
            :root {
                --statix-bg:#081426;
                --statix-border:rgba(157,180,222,.16);
                --statix-text:#e7eefc;
                --statix-muted:#91a3c2;
                --statix-accent:#7f96e8;
                --statix-hover:rgba(126,149,225,.08);
            }
        }

        .stApp {
            background:var(--statix-bg);
            color:var(--statix-text);
        }

        .block-container {
            max-width:1500px;
            padding-top:2rem;
            padding-bottom:2rem;
        }

        /* Horizontal card scrolling */

        .statix-scroll-row {
            display:flex;
            overflow-x:auto;
            overflow-y:hidden;
            gap:18px;
            width:100%;
            padding:4px 4px 18px;
            margin-bottom:22px;
            scrollbar-width:thin;
        }

        .statix-scroll-row::-webkit-scrollbar {
            height:7px;
        }

        /* Individual card */

        .statix-card {
            width:100%;
            min-height:250px;
            box-sizing:border-box;
            padding:22px 24px;
            background:transparent;
            border:1px solid var(--statix-border);
            border-radius:10px;
            transition:
                border-color .15s ease,
                background .15s ease,
                transform .15s ease;
        }

        .statix-card:hover {
            border-color:var(--statix-accent);
            background:var(--statix-hover);
            transform:translateY(-2px);
        }

        .statix-card-head {
            display:flex;
            justify-content:space-between;
            gap:16px;
        }

        .statix-ticker {
            font-size:1.3rem;
            font-weight:760;
            letter-spacing:-.02em;
        }

        .statix-name {
            margin-top:3px;
            color:var(--statix-muted);
            font-size:.88rem;
            white-space:nowrap;
            overflow:hidden;
            text-overflow:ellipsis;
        }

        .statix-arrow {
            color:var(--statix-muted);
            font-size:1.15rem;
        }

        .statix-card-stats {
            display:flex;
            justify-content:space-between;
            align-items:baseline;
            margin-top:22px;
            font-size:.98rem;
            font-variant-numeric:tabular-nums;
        }

        .statix-card-stats b {
            font-size:1.4rem;
        }

        .statix-chart {
            height:105px;
            margin-top:17px;
            color:var(--statix-accent);
            opacity:.92;
        }

        .statix-spark {
            width:100%;
            height:100%;
        }

        .statix-card-prediction {
            color:var(--statix-muted);
            font-size:.82rem;
            margin-top:12px;
            line-height:1.45;
        }

        /*
        The Streamlit button beside each card is the actual
        navigation control. Make it visually minimal.
        */

        div[data-testid="stButton"] button {
            border-radius:8px;
        }

        /* Bottom navigation */

        .statix-bottom-spacer {
            height:80px;
        }

        [data-testid="stHorizontalBlock"] {
            align-items:stretch;
        }

        [data-testid="stMetricValue"] {
            font-variant-numeric:tabular-nums;
        }

        @media (max-width:700px) {

            .statix-card {
                min-height:225px;
                padding:19px 20px;
            }

            .statix-card-stats b {
                font-size:1.25rem;
            }

        }

        </style>
        """,
        unsafe_allow_html=True,
    )
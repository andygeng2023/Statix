from __future__ import annotations

import html
from urllib.parse import quote

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


def _sparkline_svg(
    df: pd.DataFrame | None,
    expected_return: float | None = None,
    width=640,
    height=120,
) -> str:
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

    forecast = ""
    if expected_return is not None and len(values) >= 2:
        forecast_value = values[-1] * (1 + float(expected_return))
        forecast_x = width - 4
        forecast_y = height - 8 - (height - 16) * (forecast_value - lo) / span
        forecast_y = max(8, min(height - 8, forecast_y))
        forecast = (
            f'<line x1="{points[-1].split(",")[0]}" '
            f'y1="{points[-1].split(",")[1]}" x2="{forecast_x:.1f}" '
            f'y2="{forecast_y:.1f}" stroke="#d97706" stroke-width="2.4" '
            f'stroke-dasharray="7 6" stroke-linecap="round" />'
        )

    return (
        f'<svg class="statix-spark" xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" preserveAspectRatio="none" '
        f'aria-hidden="true" style="display:block;width:100%;height:100%;">'
        f'<polyline points="{" ".join(points)}" fill="none" '
        f'stroke="currentColor" stroke-width="2.4" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
        f"{forecast}"
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
    stock_url = f"?page=stocks&amp;ticker={quote(symbol)}"

    spark = _sparkline_svg(df, expected_return=expected_return)

    prediction = ""

    if signal:
        pieces = [f"<b>{html.escape(str(signal))}</b>"]

        if confidence is not None:
            pieces.append(f"Confidence {score(confidence)}")

        if reliability is not None:
            pieces.append(f"Reliability {score(reliability)}")

        if expected_return is not None:
            pieces.append(
                f"5D outlook {pct(expected_return * 100)}"
            )

        prediction = (
            '<div class="statix-card-prediction">'
            + " · ".join(pieces)
            + "</div>"
        )

    return f"""
    <style>
        .statix-card-link {{ display:block; width:232px; min-width:232px; color:inherit; text-decoration:none; }}
        .statix-card {{ box-sizing:border-box; width:232px; min-height:235px; padding:16px 18px; border:1px solid rgba(20,43,82,.22); border-radius:10px; color:#102040; background:#f3f7ff; }}
        .statix-card-head {{ display:flex; justify-content:space-between; gap:16px; }}
        .statix-ticker {{ font-size:1.15rem; font-weight:760; }}
        .statix-name {{ margin-top:3px; color:#5d6d89; font-size:.88rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
        .statix-card-stats {{ display:flex; justify-content:space-between; align-items:baseline; margin-top:16px; font-size:.98rem; }}
        .statix-card-stats b {{ font-size:1.2rem; }}
        .statix-chart {{ display:block; width:100%; height:92px; margin-top:12px; color:#4159a8; }}
        .statix-card-prediction {{ color:#5d6d89; font-size:.82rem; margin-top:12px; line-height:1.45; }}
    </style>
    <a class="statix-card-link" href="{stock_url}" target="_top">
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

        {f'<div class="statix-chart" style="height:92px;">{spark}</div>' if spark else ""}

        {prediction}
    </div>
    </a>
    """


def card_row(items: list[dict], key_prefix: str = "card"):
    if not items:
        return

    st.markdown(
        f"<style>.st-key-card-row-{key_prefix} {{ overflow-x:auto; overflow-y:hidden; flex-wrap:nowrap !important; scrollbar-width:thin; }} "
        f".st-key-card-row-{key_prefix} > div {{ flex:0 0 248px !important; width:248px !important; min-width:248px !important; }}</style>",
        unsafe_allow_html=True,
    )
    with st.container(horizontal=True, gap="small", key=f"card-row-{key_prefix}"):
        for item in items:
            ticker = str(item["ticker"]).upper()
            st.components.v1.html(
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
                ),
                width=248,
                height=260,
                scrolling=False,
            )


def bottom_navigation(page: str, labels: dict[str, str]):
    st.markdown(
        '<div class="statix-bottom-spacer"></div>',
        unsafe_allow_html=True,
    )

    with st.container(key="statix-bottom-nav"):
        cols = st.columns(len(labels), gap="small")
        for col, key in zip(cols, labels):
            with col:
                if st.button(
                    labels[key],
                    key=f"bottom_nav_{key}",
                    use_container_width=True,
                    type="primary" if page == key else "secondary",
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

        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display:none;
        }

        div[data-testid="stButton"] > button {
            min-height:42px;
            border-radius:8px;
            border-color:rgba(65,89,168,.35);
            color:var(--statix-text);
            font-weight:650;
        }

        div[data-testid="stButton"] > button[kind="primary"] {
            background:var(--statix-accent);
            border-color:var(--statix-accent);
            color:#ffffff;
        }

        div[data-testid="stButton"] > button:hover {
            border-color:var(--statix-accent);
            box-shadow:0 4px 12px rgba(65,89,168,.2);
        }

        .block-container {
            max-width:1500px;
            padding-top:2rem;
            padding-bottom:2rem;
        }

        /* Individual card */

        .statix-card-link {
            display:block;
            flex:0 0 232px;
            width:232px;
            min-width:232px;
            color:inherit;
            text-decoration:none;
        }

        .statix-card {
            width:100%;
            min-height:235px;
            box-sizing:border-box;
            padding:16px 18px;
            background:transparent;
            border:1px solid rgba(20,43,82,.22);
            border-radius:10px;
            transition:
                border-color .15s ease,
                background .15s ease,
                transform .15s ease,
                box-shadow .15s ease;
        }

        .statix-card:hover {
            border-color:var(--statix-accent);
            background:var(--statix-hover);
            transform:translateY(-2px);
            box-shadow:0 8px 20px rgba(16,32,64,.14);
        }

        .statix-card-head {
            display:flex;
            justify-content:space-between;
            gap:16px;
        }

        .statix-ticker {
            font-size:1.15rem;
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
            margin-top:16px;
            font-size:.98rem;
            font-variant-numeric:tabular-nums;
        }

        .statix-card-stats b {
            font-size:1.2rem;
        }

        .statix-chart {
            height:92px;
            margin-top:12px;
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

        /* Bottom navigation */

        .statix-bottom-spacer {
            height:80px;
        }

        .st-key-statix-bottom-nav {
            position:fixed;
            z-index:1000;
            left:0;
            right:0;
            bottom:0;
            display:flex;
            gap:8px;
            padding:12px max(16px, calc((100vw - 1500px) / 2));
            background:color-mix(in srgb, var(--statix-bg) 94%, transparent);
            border-top:1px solid var(--statix-border);
            backdrop-filter:blur(12px);
        }

        .statix-bottom-tab {
            flex:1;
            padding:10px 8px;
            border:1px solid transparent;
            border-radius:8px;
            color:var(--statix-muted);
            text-align:center;
            text-decoration:none;
            font-size:.9rem;
        }

        .statix-bottom-tab:hover,
        .statix-bottom-tab-active {
            border-color:var(--statix-border);
            background:var(--statix-hover);
            color:var(--statix-text);
        }

        [data-testid="stHorizontalBlock"]:has(.statix-card-link) {
            flex-wrap:nowrap !important;
            overflow-x:auto;
            overflow-y:hidden;
            padding:4px 4px 14px;
            scrollbar-width:thin;
        }

        [data-testid="stHorizontalBlock"]:has(.statix-card-link) > div {
            flex:0 0 232px !important;
            width:232px !important;
            min-width:232px !important;
        }

        [data-testid="stHorizontalBlock"] {
            align-items:stretch;
        }

        [data-testid="stMetricValue"] {
            font-variant-numeric:tabular-nums;
        }

        @media (max-width:700px) {

            .statix-card-link {
                flex-basis:212px;
                width:212px;
                min-width:212px;
            }

            .statix-card {
                min-height:200px;
                padding:14px 16px;
            }

            .statix-card-stats b {
                font-size:1.2rem;
            }

        }

        </style>
        """,
        unsafe_allow_html=True,
    )
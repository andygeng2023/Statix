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
    values = pd.to_numeric(df["close"], errors="coerce").dropna().tail(80).to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 2:
        return ""
    lo, hi = float(values.min()), float(values.max())
    span = hi - lo or 1.0
    points = []
    for i, value in enumerate(values):
        x = 4 + (width - 8) * i / (len(values) - 1)
        y = height - 8 - (height - 16) * (value - lo) / span
        points.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg class="statix-spark" viewBox="0 0 {width} {height}" preserveAspectRatio="none" aria-hidden="true">'
        f'<polyline points="{" ".join(points)}" fill="none" stroke="currentColor" stroke-width="2.4" '
        f'stroke-linecap="round" stroke-linejoin="round" /></svg>'
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
    page: str = "stocks",
) -> str:
    symbol = str(ticker).upper()
    href = f"?page={urlquote(page)}&ticker={urlquote(symbol)}"
    safe_symbol = html.escape(symbol)
    safe_name = html.escape(name or "")
    spark = _sparkline_svg(df)

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

    return f'''
    <a class="statix-card-link" href="{href}">
      <div class="statix-card">
        <div class="statix-card-head">
          <div><div class="statix-ticker">{safe_symbol}</div><div class="statix-name">{safe_name}</div></div>
          <div class="statix-arrow">↗</div>
        </div>
        <div class="statix-card-stats"><span><b>{money(price)}</b></span><span>{pct(change_pct)}</span></div>
        {f'<div class="statix-chart">{spark}</div>' if spark else ''}
        {prediction}
      </div>
    </a>
    '''


def card_row(items: list[dict]):
    if not items:
        return
    cards = "".join(card_html(**item) for item in items)
    st.markdown(f'<div class="statix-card-row">{cards}</div>', unsafe_allow_html=True)


def inject_theme_css():
    st.markdown(
        """
        <style>
        :root {
            --statix-bg:#f3f7ff; --statix-border:rgba(20,43,82,.14);
            --statix-text:#102040; --statix-muted:#5d6d89; --statix-accent:#4159a8;
            --statix-accent-soft:#7187d2; --statix-hover:rgba(55,77,145,.08);
        }
        @media (prefers-color-scheme:dark) {
            :root {
                --statix-bg:#081426; --statix-border:rgba(157,180,222,.16);
                --statix-text:#e7eefc; --statix-muted:#91a3c2; --statix-accent:#7f96e8;
                --statix-accent-soft:#9caef0; --statix-hover:rgba(126,149,225,.08);
            }
        }
        .stApp { background:var(--statix-bg); color:var(--statix-text); }
        .block-container { max-width:1440px; padding-top:2rem; padding-bottom:6.5rem; }
        .brand { font-size:1.7rem; font-weight:850; letter-spacing:-.05em; }
        .muted { color:var(--statix-muted); }

        .statix-card-row {
            display:flex; gap:16px; overflow-x:auto; overflow-y:hidden;
            padding:4px 2px 14px; margin:0 0 20px;
            scroll-snap-type:x proximity; scrollbar-width:thin;
        }
        .statix-card-link {
            flex:0 0 360px; width:360px; display:block; color:inherit !important;
            text-decoration:none !important; scroll-snap-align:start;
        }
        .statix-card {
            min-height:245px; box-sizing:border-box; padding:22px 24px;
            background:transparent; border:1px solid var(--statix-border); border-radius:10px;
            transition:border-color .16s ease,background .16s ease,transform .16s ease,box-shadow .16s ease;
        }
        .statix-card:hover { border-color:var(--statix-accent); background:var(--statix-hover); transform:translateY(-2px); box-shadow:0 12px 30px rgba(14,35,70,.10); }
        .statix-card-head { display:flex; justify-content:space-between; gap:16px; }
        .statix-ticker { font-size:1.28rem; font-weight:760; letter-spacing:-.02em; }
        .statix-name { margin-top:3px; color:var(--statix-muted); font-size:.88rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .statix-arrow { color:var(--statix-muted); font-size:1.2rem; }
        .statix-card-stats { display:flex; justify-content:space-between; align-items:baseline; margin-top:22px; font-size:.98rem; font-variant-numeric:tabular-nums; }
        .statix-card-stats b { font-size:1.38rem; }
        .statix-chart { height:102px; margin-top:16px; color:var(--statix-accent); opacity:.92; }
        .statix-spark { width:100%; height:100%; }
        .statix-card-prediction { color:var(--statix-muted); font-size:.82rem; margin-top:12px; line-height:1.45; }

        /* Fixed app navigation: same-page links, evenly distributed like mobile app tabs. */
        .statix-bottom-nav {
            position:fixed; z-index:999999; left:0; right:0; bottom:0;
            display:grid; grid-template-columns:repeat(4,1fr); gap:0;
            padding:8px max(12px, env(safe-area-inset-left)) calc(8px + env(safe-area-inset-bottom));
            background:color-mix(in srgb, var(--statix-bg) 94%, transparent);
            border-top:1px solid var(--statix-border); backdrop-filter:blur(16px);
        }
        .statix-bottom-nav a { text-align:center; padding:11px 6px; color:var(--statix-muted); text-decoration:none !important; font-weight:680; font-size:.9rem; border-radius:8px; }
        .statix-bottom-nav a:hover, .statix-bottom-nav a.active { color:var(--statix-text); background:var(--statix-hover); }
        [data-testid="stMetricValue"] { font-variant-numeric:tabular-nums; }
        @media (max-width:700px) { .statix-card-link{flex-basis:315px;width:315px;} .statix-card{min-height:225px;} }
        </style>
        """,
        unsafe_allow_html=True,
    )

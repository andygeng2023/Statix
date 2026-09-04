from __future__ import annotations

import base64
import html
import io

import numpy as np
import pandas as pd
import streamlit as st

from src.config import TEXT


# ============================================================
# Translation helper
# ============================================================

def t(key: str, lang: str) -> str:
    return TEXT.get(
        lang,
        TEXT["en"],
    ).get(
        key,
        TEXT["en"].get(key, key),
    )


# ============================================================
# Number formatting
# ============================================================

def money(
    value,
    symbol="$",
    decimals=2,
):
    if value is None:
        return "—"

    try:
        return f"{symbol}{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def number(
    value,
    decimals=2,
):
    if value is None:
        return "—"

    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def pct(
    value,
    decimals=2,
    signed=True,
):
    if value is None:
        return "—"

    try:
        n = float(value)

        prefix = (
            "+"
            if signed and n > 0
            else ""
        )

        return f"{prefix}{n:,.{decimals}f}%"

    except (TypeError, ValueError):
        return "—"


def score(
    value,
    decimals=2,
):
    if value is None:
        return "—"

    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"


# ============================================================
# Sparkline
# ============================================================

def _sparkline_svg(
    df: pd.DataFrame | None,
    width: int = 640,
    height: int = 120,
) -> str:

    if (
        df is None
        or df.empty
        or "close" not in df.columns
    ):
        return ""

    values = (
        pd.to_numeric(
            df["close"],
            errors="coerce",
        )
        .dropna()
        .tail(80)
        .to_numpy(dtype=float)
    )

    values = values[np.isfinite(values)]

    if len(values) < 2:
        return ""

    low = float(values.min())
    high = float(values.max())

    span = high - low

    if span == 0:
        span = 1.0

    points = []

    for i, value in enumerate(values):

        x = (
            4
            + (width - 8)
            * i
            / (len(values) - 1)
        )

        y = (
            height
            - 8
            - (height - 16)
            * (value - low)
            / span
        )

        points.append(
            f"{x:.1f},{y:.1f}"
        )

    return (
        f'<svg '
        f'class="statix-spark" '
        f'viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none" '
        f'aria-hidden="true">'
        f'<polyline '
        f'points="{" ".join(points)}" '
        f'fill="none" '
        f'stroke="currentColor" '
        f'stroke-width="2.5" '
        f'stroke-linecap="round" '
        f'stroke-linejoin="round" />'
        f'</svg>'
    )


# ============================================================
# Convert SVG into a small data URI image.
#
# Streamlit buttons support Markdown images in their labels.
# This lets the actual native button contain a graph.
# ============================================================

def _sparkline_markdown(
    df: pd.DataFrame | None,
) -> str:

    svg = _sparkline_svg(df)

    if not svg:
        return ""

    encoded = base64.b64encode(
        svg.encode("utf-8")
    ).decode("ascii")

    return (
        f"![chart]"
        f"(data:image/svg+xml;base64,{encoded})"
    )


# ============================================================
# Navigate inside Streamlit
# ============================================================

def open_stock(ticker: str):
    st.session_state["selected_ticker"] = (
        str(ticker).upper()
    )

    st.session_state["page"] = "stocks"


# ============================================================
# Native clickable stock card
# ============================================================

def stock_card(
    ticker: str,
    name: str | None,
    price: float | None,
    change_pct: float | None,
    df: pd.DataFrame | None = None,
    signal: str | None = None,
    confidence: float | None = None,
    reliability: float | None = None,
    expected_return: float | None = None,
    key: str | None = None,
):

    symbol = str(ticker).upper()

    display_name = (
        name
        or symbol
    )

    spark = _sparkline_markdown(df)

    # --------------------------------------------------------
    # The button label uses Markdown.
    #
    # No <a>
    # No JavaScript
    # No window.parent
    # No query-string navigation
    # --------------------------------------------------------

    lines = [
        f"**{symbol}**",
        f"*{display_name}*",
        "",
        f"**{money(price)}**   {pct(change_pct)}",
    ]

    if signal:

        prediction_parts = [
            f"**{signal}**"
        ]

        if confidence is not None:
            prediction_parts.append(
                f"Confidence {score(confidence)}"
            )

        if reliability is not None:
            prediction_parts.append(
                f"Reliability {score(reliability)}"
            )

        if expected_return is not None:
            prediction_parts.append(
                f"Expected {pct(expected_return * 100)}"
            )

        lines.extend(
            [
                "",
                " · ".join(prediction_parts),
            ]
        )

    if spark:
        lines.extend(
            [
                "",
                spark,
            ]
        )

    label = "\n\n".join(lines)

    clicked = st.button(
        label,
        key=key or f"stock_card_{symbol}",
        width=380,
        type="secondary",
        help=f"Open {symbol}",
    )

    if clicked:
        open_stock(symbol)
        st.rerun()


# ============================================================
# Horizontally scrolling row
# ============================================================

def card_row(
    items: list[dict],
    row_key: str = "row",
):

    if not items:
        return

    # Streamlit 1.62 supports:
    #
    # horizontal=True
    # wrap=False
    #
    # which produces a single horizontally scrolling row.
    with st.container(
        horizontal=True,
        wrap=False,
        horizontal_alignment="left",
        vertical_alignment="top",
        gap="medium",
        key=f"scroll_{row_key}",
    ):

        for index, item in enumerate(items):

            ticker = str(
                item["ticker"]
            ).upper()

            stock_card(
                ticker=ticker,
                name=item.get("name"),
                price=item.get("price"),
                change_pct=item.get("change_pct"),
                df=item.get("df"),
                signal=item.get("signal"),
                confidence=item.get("confidence"),
                reliability=item.get("reliability"),
                expected_return=item.get("expected_return"),
                key=f"{row_key}_{index}_{ticker}",
            )


# ============================================================
# Bottom navigation
# ============================================================

def bottom_nav(page: str):

    with st.container(key="bottom_nav"):

        st.markdown(
            '<div class="statix-bottom-spacer"></div>',
            unsafe_allow_html=True,
        )

        labels = {
            "home": "Home",
            "stocks": "Stocks",
            "discover": "Discover",
            "settings": "Settings",
        }

        cols = st.columns(
            4,
            gap="small",
        )

        for col, (key, label) in zip(
            cols,
            labels.items(),
        ):

            active = (
                page == key
            )

            with col:

                if st.button(
                    label,
                    key=f"bottom_nav_{key}",
                    width="stretch",
                    type="primary" if active else "secondary",
                ):

                    st.session_state["page"] = key

                    if key != "stocks":
                        st.session_state[
                            "selected_ticker"
                        ] = None

                    st.rerun()


# ============================================================
# Theme
# ============================================================

def inject_theme_css():

    st.markdown(
        """
<style>

/* =========================================================
   Statix colour system
   ========================================================= */

:root {
    --statix-bg: #f2f6ff;
    --statix-text: #102040;
    --statix-muted: #64738e;
    --statix-border: rgba(30, 55, 100, .16);
    --statix-accent: #5269b5;
    --statix-hover: rgba(82, 105, 181, .08);
    --statix-bottom: rgba(242, 246, 255, .92);
}

@media (prefers-color-scheme: dark) {

    :root {
        --statix-bg: #071426;
        --statix-text: #e9effc;
        --statix-muted: #91a2c0;
        --statix-border: rgba(155, 181, 225, .17);
        --statix-accent: #8198e9;
        --statix-hover: rgba(129, 152, 233, .08);
        --statix-bottom: rgba(7, 20, 38, .94);
    }
}


/* =========================================================
   Application
   ========================================================= */

.stApp {
    background: var(--statix-bg);
    color: var(--statix-text);
}

.block-container {
    max-width: 1480px;
    padding-top: 1.8rem;
    padding-bottom: 7rem;
}


/* =========================================================
   Sidebar / branding
   ========================================================= */

.brand {
    font-size: 1.75rem;
    font-weight: 850;
    letter-spacing: -.05em;
}

.muted {
    color: var(--statix-muted);
}


/* =========================================================
   Horizontal card rows
   ========================================================= */

.statix-card-row {
    width: 100%;
    margin-bottom: 1.2rem;
}


/* =========================================================
   Native Streamlit stock buttons
   ========================================================= */

div[class*="st-key-"][class*="stock_card_"] {
    flex: 0 0 380px;
    min-width: 380px;
    width: 380px;
}


/*
   The actual Streamlit button becomes the card.
*/

div[class*="st-key-"][class*="stock_card_"] button {
    width: 380px !important;
    min-width: 380px !important;

    min-height: 255px !important;

    padding: 22px 24px !important;

    border-radius: 10px !important;

    border: 1px solid var(--statix-border) !important;

    background: transparent !important;

    color: var(--statix-text) !important;

    text-align: left !important;

    box-shadow: none !important;

    transition:
        border-color .16s ease,
        background .16s ease,
        transform .16s ease,
        box-shadow .16s ease !important;
}


/*
   Make the card feel like a card rather than a button.
*/

div[class*="st-key-"][class*="stock_card_"] button:hover {
    border-color: var(--statix-accent) !important;

    background: var(--statix-hover) !important;

    transform: translateY(-2px);

    box-shadow:
        0 12px 28px rgba(10, 30, 65, .12) !important;
}


/*
   Remove Streamlit's normal button focus appearance.
*/

div[class*="st-key-"][class*="stock_card_"] button:focus {
    border-color: var(--statix-accent) !important;

    box-shadow:
        0 0 0 2px
        color-mix(
            in srgb,
            var(--statix-accent) 25%,
            transparent
        ) !important;
}


/* =========================================================
   Card typography
   ========================================================= */

div[class*="st-key-"][class*="stock_card_"] button p {
    color: var(--statix-text) !important;
    margin: 0 !important;
    line-height: 1.45 !important;
}

div[class*="st-key-"][class*="stock_card_"] button strong {
    font-size: 1.25rem;
    font-weight: 780;
}

div[class*="st-key-"][class*="stock_card_"] button em {
    color: var(--statix-muted);
    font-style: normal;
    font-size: .86rem;
}


/*
   Markdown image / sparkline.
*/

div[class*="st-key-"][class*="stock_card_"] button img {
    width: 100% !important;
    max-width: 100% !important;
    height: 78px !important;
    max-height: 78px !important;
    object-fit: fill !important;
    display: block !important;
    margin-top: 7px !important;
}


/* =========================================================
   Bottom navigation
   ========================================================= */

.statix-bottom-spacer {
    height: 4.5rem;
}


/*
   Keep the four native buttons evenly distributed.
*/

div[data-testid="stHorizontalBlock"] {
    gap: .7rem;
}


/*
   Bottom nav is visually fixed using sticky positioning.
   It remains part of the same Streamlit page/session.
*/

div[data-testid="stHorizontalBlock"]:has(
    button[kind="primary"]
) {
}


/*
    Scope the fixed position to the navigation container so card rows
    remain in the normal page flow.
*/

div[class*="st-key-bottom_nav"] div[data-testid="stHorizontalBlock"] {
    position: fixed;

    left: 0;
    right: 0;
    bottom: 0;

    z-index: 999;

    padding:
        10px
        max(20px, calc((100vw - 1480px) / 2));

    background: var(--statix-bottom);

    border-top:
        1px solid
        var(--statix-border);

    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
}


/* =========================================================
   Normal Streamlit buttons
   ========================================================= */

button[kind="secondary"] {
    border-radius: 8px;
}


/* =========================================================
   Metrics
   ========================================================= */

[data-testid="stMetricValue"] {
    font-variant-numeric: tabular-nums;
}


/* =========================================================
   Mobile
   ========================================================= */

@media (max-width: 700px) {

    div[class*="st-key-"][class*="stock_card_"] {
        flex-basis: 330px;
        min-width: 330px;
        width: 330px;
    }

    div[class*="st-key-"][class*="stock_card_"] button {
        width: 330px !important;
        min-width: 330px !important;
    }

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}

</style>
""",
        unsafe_allow_html=True,
    )
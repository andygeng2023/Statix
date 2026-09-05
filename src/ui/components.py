from __future__ import annotations

import html

import numpy as np
import pandas as pd
import streamlit as st

from src.config import TEXT


def t(key, lang):
    return TEXT.get(
        lang,
        TEXT["en"],
    ).get(
        key,
        TEXT["en"].get(
            key,
            key,
        ),
    )


def money(
    value,
    symbol="$",
    decimals=2,
):
    if value is None:
        return "—"

    try:
        number_value = float(value)

        if not np.isfinite(
            number_value
        ):
            return "—"

        return (
            f"{symbol}"
            f"{number_value:,.{decimals}f}"
        )

    except (
        TypeError,
        ValueError,
    ):
        return "—"


def number(
    value,
    decimals=2,
):
    if value is None:
        return "—"

    try:
        number_value = float(value)

        if not np.isfinite(
            number_value
        ):
            return "—"

        return (
            f"{number_value:,.{decimals}f}"
        )

    except (
        TypeError,
        ValueError,
    ):
        return "—"


def pct(
    value,
    decimals=2,
    signed=True,
):
    if value is None:
        return "—"

    try:
        number_value = float(value)

        if not np.isfinite(
            number_value
        ):
            return "—"

        prefix = (
            "+"
            if signed
            and number_value > 0
            else ""
        )

        return (
            f"{prefix}"
            f"{number_value:,.{decimals}f}%"
        )

    except (
        TypeError,
        ValueError,
    ):
        return "—"


def score(
    value,
    decimals=2,
):
    if value is None:
        return "—"

    try:
        number_value = float(value)

        if not np.isfinite(number_value):
            return "—"

        return f"{number_value * 100:.{decimals}f}%"

    except (
        TypeError,
        ValueError,
    ):
        return "—"


def _sparkline_svg(
    df: pd.DataFrame | None,
    expected_return: float | None = None,
    width=640,
    height=120,
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
        .to_numpy(
            dtype=float
        )
    )

    values = values[
        np.isfinite(values)
    ]

    if len(values) < 2:
        return ""

    low = float(values.min())
    high = float(values.max())

    span = high - low

    if span == 0:
        span = 1.0

    points = []

    for index, value in enumerate(
        values
    ):

        x = (
            4
            + (width - 8)
            * index
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

    forecast = ""

    if (
        expected_return is not None
        and len(values) >= 2
    ):

        try:

            expected = float(
                expected_return
            )

            if np.isfinite(
                expected
            ):

                forecast_value = (
                    values[-1]
                    * (1 + expected)
                )

                forecast_x = width - 4

                forecast_y = (
                    height
                    - 8
                    - (height - 16)
                    * (
                        forecast_value
                        - low
                    )
                    / span
                )

                forecast_y = max(
                    8,
                    min(
                        height - 8,
                        forecast_y,
                    ),
                )

                last_x, last_y = (
                    points[-1].split(",")
                )

                forecast = (
                    '<line '
                    f'x1="{last_x}" '
                    f'y1="{last_y}" '
                    f'x2="{forecast_x:.1f}" '
                    f'y2="{forecast_y:.1f}" '
                    'stroke="var(--statix-forecast)" '
                    'stroke-width="2.2" '
                    'stroke-dasharray="6 6" '
                    'stroke-linecap="round" />'
                )

        except (
            TypeError,
            ValueError,
        ):
            pass

    points_string = " ".join(
        points
    )

    return (
        '<svg '
        'class="statix-spark" '
        'xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        'preserveAspectRatio="none" '
        'aria-hidden="true">'
        '<polyline '
        f'points="{points_string}" '
        'fill="none" '
        'stroke="currentColor" '
        'stroke-width="2.2" '
        'stroke-linecap="round" '
        'stroke-linejoin="round" />'
        f"{forecast}"
        "</svg>"
    )


def _card_html(
    item: dict,
) -> str:

    ticker = str(
        item.get(
            "ticker",
            "",
        )
    ).upper()

    name = html.escape(
        str(
            item.get(
                "name"
            )
            or ticker
        ),
        quote=True,
    )

    spark = _sparkline_svg(
        item.get("df"),
        item.get(
            "expected_return"
        ),
    )

    signal = item.get(
        "signal"
    )

    prediction_html = ""

    if signal:

        prediction_html = (
            '<div class="statix-card-prediction">'
            '<span class="statix-signal">'
            f"{html.escape(str(signal))}"
            "</span>"
            '<span class="statix-prediction-meta">'
            f"Confidence "
            f"{score(item.get('confidence'))}"
            " · "
            f"Reliability "
            f"{score(item.get('reliability'))}"
            "</span>"
            "</div>"
        )

    chart_html = ""

    if spark:

        chart_html = (
            '<div class="statix-chart">'
            f"{spark}"
            "</div>"
        )

    else:

        chart_html = (
            '<div class="statix-chart '
            'statix-chart-empty"></div>'
        )

    return (
        '<div '
        'class="statix-card-link" '
        f'data-ticker="{html.escape(ticker, quote=True)}" '
        'role="button" '
        'tabindex="0">'
        '<div class="statix-card">'

        '<div class="statix-card-head">'

        '<div class="statix-card-identity">'

        '<div class="statix-ticker">'
        f"{html.escape(ticker)}"
        "</div>"

        '<div class="statix-name">'
        f"{name}"
        "</div>"

        "</div>"

        '<div class="statix-arrow">›</div>'

        "</div>"

        '<div class="statix-card-stats">'

        '<span class="statix-price">'
        f"{money(item.get('price'))}"
        "</span>"

        '<span class="statix-change">'
        f"{pct(item.get('change_pct'))}"
        "</span>"

        "</div>"

        f"{chart_html}"

        f"{prediction_html}"

        "</div>"
        "</div>"
    )


def card_row(
    items: list[dict],
    key_prefix: str = "card",
):

    if not items:
        return

    safe_key = (
        str(key_prefix)
        .replace("_", "-")
        .replace(" ", "-")
    )

    with st.container(
        horizontal=True,
        horizontal_alignment="left",
        gap="small",
        key=f"card-row-{safe_key}",
    ):

        for item in items:

            st.markdown(
                _card_html(item),
                unsafe_allow_html=True,
            )


def bottom_navigation(
    page: str,
    labels: dict[str, str],
):

    with st.container(
        key="statix-bottom-nav"
    ):

        cols = st.columns(
            len(labels),
            gap="small",
        )

        for col, key in zip(
            cols,
            labels,
        ):

            with col:

                if st.button(
                    labels[key],
                    key=(
                        f"bottom_nav_{key}"
                    ),
                    use_container_width=True,
                    type=(
                        "primary"
                        if page == key
                        else "secondary"
                    ),
                ):

                    st.session_state[
                        "page"
                    ] = key

                    st.session_state.pop(
                        "selected_ticker",
                        None,
                    )

                    st.query_params.clear()

                    st.rerun()


def inject_theme_css():

    st.markdown(
        """
        <style>

        :root {
            --statix-bg:#f3f7ff;
            --statix-surface:rgba(255,255,255,.34);
            --statix-surface-hover:rgba(255,255,255,.60);
            --statix-border:rgba(20,43,82,.14);
            --statix-border-strong:rgba(20,43,82,.22);
            --statix-text:#102040;
            --statix-muted:#63728c;
            --statix-accent:#4159a8;
            --statix-hover:rgba(65,89,168,.065);
            --statix-forecast:#b97916;
            --statix-nav-bg:rgba(243,247,255,.92);
        }

        @media (prefers-color-scheme:dark) {

            :root {
                --statix-bg:#081426;
                --statix-surface:rgba(13,31,56,.28);
                --statix-surface-hover:rgba(20,42,72,.48);
                --statix-border:rgba(157,180,222,.16);
                --statix-border-strong:rgba(157,180,222,.24);
                --statix-text:#e7eefc;
                --statix-muted:#91a3c2;
                --statix-accent:#8b9ee9;
                --statix-hover:rgba(126,149,225,.08);
                --statix-forecast:#d6a14b;
                --statix-nav-bg:rgba(8,20,38,.93);
            }
        }

        /* -----------------------------------------
           PAGE
        ----------------------------------------- */

        .stApp {
            background:var(--statix-bg);
            color:var(--statix-text);
        }

        .block-container {
            max-width:1500px;

            padding-top:2rem;

            /*
             * IMPORTANT:
             * This reserves space at the ACTUAL bottom
             * of every page, rather than inserting a spacer
             * before the page content.
             */
            padding-bottom:125px !important;
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display:none;
        }

        /* -----------------------------------------
           BUTTONS
        ----------------------------------------- */

        div[data-testid="stButton"] > button {
            min-height:42px;
            border-radius:8px;
            border-color:var(--statix-border-strong);
            color:var(--statix-text);
            font-weight:600;
            transition:
                background .15s ease,
                border-color .15s ease,
                transform .15s ease;
        }

        div[data-testid="stButton"] > button:hover {
            border-color:var(--statix-accent);
            transform:translateY(-1px);
        }

        div[data-testid="stButton"] > button[kind="primary"] {
            background:var(--statix-accent);
            border-color:var(--statix-accent);
            color:#fff;
        }

        /* -----------------------------------------
           HORIZONTAL CARD ROWS
        ----------------------------------------- */

        [data-testid="stHorizontalBlock"]:has(.statix-card-link) {

            width:100%;
            max-width:100%;
            min-width:0;

            flex-wrap:nowrap !important;

            overflow-x:auto !important;
            overflow-y:hidden !important;

            align-items:stretch !important;

            padding:
                5px
                5px
                16px;

            margin-bottom:4px;

            scrollbar-width:thin;

            scrollbar-color:
                var(--statix-border-strong)
                transparent;
        }

        [data-testid="stHorizontalBlock"]:has(.statix-card-link)
        > div {

            flex:0 0 285px !important;

            width:285px !important;
            min-width:285px !important;
            max-width:285px !important;

            min-height:0 !important;

            box-sizing:border-box;
        }

        [data-testid="stHorizontalBlock"]:has(.statix-card-link)
        > div > div {

            width:100%;
            max-width:100%;
            min-width:0;
        }

        /* -----------------------------------------
           CARD
        ----------------------------------------- */

        .statix-card-link {

            display:block;

            width:100%;
            max-width:100%;
            min-width:0;

            color:inherit;
            text-decoration:none;

            cursor:pointer;

            outline:none;

            box-sizing:border-box;
        }

        .statix-card {

            display:block;

            width:100%;
            max-width:100%;
            min-width:0;

            box-sizing:border-box;

            min-height:220px;

            padding:18px 19px;

            background:var(--statix-surface);

            border:
                1px solid
                var(--statix-border);

            border-radius:10px;

            /*
             * Critical overflow protection.
             */
            overflow:hidden;

            contain:layout paint;

            transition:
                border-color .15s ease,
                background .15s ease,
                transform .15s ease,
                box-shadow .15s ease;
        }

        .statix-card:hover {

            border-color:
                var(--statix-accent);

            background:
                var(--statix-surface-hover);

            transform:
                translateY(-2px);

            box-shadow:
                0 8px 22px
                rgba(16,32,64,.10);
        }

        .statix-card-link:focus-visible
        .statix-card {

            border-color:
                var(--statix-accent);

            box-shadow:
                0 0 0 2px
                rgba(65,89,168,.18);
        }

        /* -----------------------------------------
           CARD HEADER
        ----------------------------------------- */

        .statix-card-head {

            display:flex;

            width:100%;
            max-width:100%;
            min-width:0;

            justify-content:
                space-between;

            align-items:flex-start;

            gap:12px;
        }

        .statix-card-identity {

            min-width:0;
            max-width:
                calc(100% - 28px);
        }

        .statix-ticker {

            font-size:1.08rem;

            line-height:1.2;

            font-weight:720;

            letter-spacing:-.02em;
        }

        .statix-name {

            margin-top:4px;

            color:
                var(--statix-muted);

            font-size:.84rem;

            line-height:1.25;

            white-space:nowrap;

            overflow:hidden;

            text-overflow:ellipsis;

            max-width:100%;
        }

        .statix-arrow {

            flex:0 0 auto;

            color:
                var(--statix-muted);

            font-size:1.45rem;

            line-height:1;

            transition:
                color .15s ease,
                transform .15s ease;
        }

        .statix-card-link:hover
        .statix-arrow {

            color:
                var(--statix-accent);

            transform:
                translateX(2px);
        }

        /* -----------------------------------------
           PRICE
        ----------------------------------------- */

        .statix-card-stats {

            display:flex;

            width:100%;
            max-width:100%;
            min-width:0;

            justify-content:
                space-between;

            align-items:
                baseline;

            gap:10px;

            margin-top:17px;

            font-size:.92rem;

            font-variant-numeric:
                tabular-nums;
        }

        .statix-price {

            min-width:0;

            font-size:1.25rem;

            line-height:1.15;

            font-weight:680;

            letter-spacing:-.02em;

            white-space:nowrap;

            overflow:hidden;

            text-overflow:ellipsis;
        }

        .statix-change {

            flex:0 0 auto;

            color:
                var(--statix-muted);

            white-space:nowrap;

            font-weight:550;
        }

        /* -----------------------------------------
           GRAPH
        ----------------------------------------- */

        .statix-chart {

            display:block;

            position:relative;

            width:100%;
            max-width:100%;
            min-width:0;

            height:88px;

            margin-top:14px;

            box-sizing:border-box;

            overflow:hidden;

            color:
                var(--statix-accent);

            opacity:.92;
        }

        .statix-chart-empty {

            height:88px;
        }

        .statix-spark {

            display:block;

            position:absolute;

            left:0;
            top:0;

            width:100% !important;
            max-width:100% !important;
            min-width:0 !important;

            height:100% !important;
            max-height:100% !important;

            box-sizing:border-box;

            overflow:hidden;

            contain:paint;
        }

        /* -----------------------------------------
           PREDICTION
        ----------------------------------------- */

        .statix-card-prediction {

            display:flex;

            width:100%;
            max-width:100%;
            min-width:0;

            flex-wrap:wrap;

            gap:4px 8px;

            margin-top:12px;

            font-size:.78rem;

            line-height:1.35;

            overflow:hidden;
        }

        .statix-signal {

            color:
                var(--statix-text);

            font-weight:650;
        }

        .statix-prediction-meta {

            color:
                var(--statix-muted);
        }

        /* -----------------------------------------
           BOTTOM NAV
        ----------------------------------------- */

        .st-key-statix-bottom-nav {

            position:fixed;

            z-index:1000;

            left:0;
            right:0;
            bottom:0;

            width:100%;

            box-sizing:border-box;

            padding:
                9px
                max(
                    14px,
                    calc(
                        (100vw - 1500px) / 2
                    )
                );

            background:
                var(--statix-nav-bg);

            border-top:
                1px solid
                var(--statix-border);

            backdrop-filter:
                blur(16px);

            -webkit-backdrop-filter:
                blur(16px);
        }

        .st-key-statix-bottom-nav
        [data-testid="stHorizontalBlock"] {

            width:100%;
        }

        .st-key-statix-bottom-nav
        div[data-testid="stButton"] > button {

            min-height:44px;

            border:
                1px solid
                transparent;

            border-radius:7px;

            background:transparent;

            box-shadow:none;

            color:
                var(--statix-muted);

            font-size:.88rem;

            font-weight:600;
        }

        .st-key-statix-bottom-nav
        div[data-testid="stButton"] > button:hover {

            background:
                var(--statix-hover);

            color:
                var(--statix-text);

            border-color:
                transparent;

            transform:none;

            box-shadow:none;
        }

        .st-key-statix-bottom-nav
        div[data-testid="stButton"] > button[kind="primary"] {

            background:
                var(--statix-hover);

            border-color:
                var(--statix-border);

            color:
                var(--statix-accent);

            box-shadow:none;
        }

        /* -----------------------------------------
           GENERAL
        ----------------------------------------- */

        [data-testid="stMetricValue"] {

            font-variant-numeric:
                tabular-nums;

            letter-spacing:-.02em;
        }

        hr {
            border-color:
                var(--statix-border) !important;
        }

        /* -----------------------------------------
           MOBILE
        ----------------------------------------- */

        @media (max-width:700px) {

            .block-container {

                padding-top:1.35rem;

                padding-left:1rem;
                padding-right:1rem;

                /*
                 * Slightly more room on mobile because
                 * the navigation remains visible.
                 */
                padding-bottom:135px !important;
            }

            [data-testid="stHorizontalBlock"]:has(.statix-card-link)
            > div {

                flex-basis:265px !important;

                width:265px !important;
                min-width:265px !important;
                max-width:265px !important;
            }

            .statix-card {

                min-height:205px;

                padding:
                    16px
                    17px;
            }

            .statix-chart {

                height:78px;
            }

            .st-key-statix-bottom-nav {

                padding:
                    8px
                    8px;
            }

            .st-key-statix-bottom-nav
            div[data-testid="stButton"] > button {

                min-height:44px;

                padding-left:4px;
                padding-right:4px;

                font-size:.78rem;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )
from __future__ import annotations

import streamlit as st

from src.models.scanner_service import scan
from src.storage.database import get_settings
from src.ui.components import (
    card_row,
    money,
    pct,
    score,
    t,
)
from src.data.market import (
    history,
    quote,
)
from src.data.search import (
    security_name,
)


settings = get_settings()

lang = st.session_state.get(
    "language_preference",
    settings.get(
        "language",
        "en",
    ),
)


st.markdown(
    f"# {t('discover', lang)}"
)

st.caption(
    t(
        "scanner_caption",
        lang,
    )
)


# =========================================================
# SCANNER CONTROL
# =========================================================

limit = st.select_slider(
    t(
        "universe_size",
        lang,
    ),
    options=[
        100,
        250,
        500,
    ],
    value=500,
)


if st.button(
    t("queue", lang),
    type="primary",
    use_container_width=False,
):

    progress = st.progress(
        0,
        text="Preparing scanner...",
    )

    def update_progress(current, total, message):
        progress.progress(
            min(1.0, current / max(1, total)),
            text=message,
        )

    with st.spinner(
        "Scanning market data..."
    ):

        try:

            scan_results = scan(
                int(limit),
                progress_callback=update_progress,
            )

            # Explicitly copy the returned list into
            # session state before rerunning.
            st.session_state[
                "latest_scan_rows"
            ] = list(
                scan_results or []
            )

            st.session_state[
                "scan_completed"
            ] = True

            st.session_state[
                "scan_result_count"
            ] = len(
                st.session_state[
                    "latest_scan_rows"
                ]
            )

            progress.progress(1.0, text="Scanner complete")

            st.rerun()

        except Exception as exc:

            st.session_state[
                "scan_completed"
            ] = False

            st.error(
                f"Scanner error: {exc}"
            )


# =========================================================
# READ PERSISTED RESULTS
# =========================================================

rows = st.session_state.get(
    "latest_scan_rows",
    [],
)

scan_completed = st.session_state.get(
    "scan_completed",
    False,
)


# =========================================================
# SCAN STATUS
# =========================================================

if scan_completed:

    result_count = len(rows)

    if result_count:

        st.success(
            f"Scan complete — "
            f"{result_count} result"
            f"{'s' if result_count != 1 else ''} returned."
        )

        # Small summary lets you verify immediately
        # that the scanner returned data.
        summary_cols = st.columns(
            3
        )

        with summary_cols[0]:

            st.metric(
                "Results",
                result_count,
            )

        with summary_cols[1]:

            bullish_count = sum(
                1
                for row in rows
                if str(
                    row.get(
                        "signal",
                        "",
                    )
                ).lower()
                == "bullish"
            )

            st.metric(
                "Bullish",
                bullish_count,
            )

        with summary_cols[2]:

            if rows:

                top_return = max(
                    float(
                        row.get(
                            "expected_return",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                )

                st.metric(
                    "Highest model return",
                    pct(
                        top_return * 100
                    ),
                )

    else:

        st.warning(
            "The scanner completed, "
            "but returned no qualifying results."
        )


# =========================================================
# AREA DATA
# =========================================================

area_symbols = {

    "Top stocks": [
        "NVDA",
        "MSFT",
        "AAPL",
        "AMZN",
        "GOOGL",
        "META",
        "AVGO",
        "TSLA",
    ],

    "Technology": [
        "NVDA",
        "MSFT",
        "AAPL",
        "AVGO",
        "ORCL",
        "AMD",
        "CRM",
        "ADBE",
    ],

    "Healthcare": [
        "LLY",
        "UNH",
        "JNJ",
        "ABBV",
        "MRK",
        "TMO",
        "ISRG",
        "PFE",
    ],

    "Financials": [
        "JPM",
        "V",
        "MA",
        "BAC",
        "WFC",
        "GS",
        "MS",
        "BLK",
    ],

    "Consumer": [
        "AMZN",
        "WMT",
        "COST",
        "HD",
        "MCD",
        "NKE",
        "SBUX",
        "TJX",
    ],

    "ETFs": [
        "SPY",
        "QQQ",
        "DIA",
        "IWM",
        "XLK",
        "XLF",
        "XLE",
        "ARKK",
    ],
}


area_labels = {

    "Top stocks": t(
        "area_top_stocks",
        lang,
    ),

    "Technology": t(
        "area_technology",
        lang,
    ),

    "Healthcare": t(
        "area_healthcare",
        lang,
    ),

    "Financials": t(
        "area_financials",
        lang,
    ),

    "Consumer": t(
        "area_consumer",
        lang,
    ),

    "ETFs": t(
        "area_etfs",
        lang,
    ),
}


# =========================================================
# TOP BY AREA
# =========================================================

st.subheader(
    t(
        "top_by_area",
        lang,
    )
)


selected_area = st.selectbox(
    t(
        "area",
        lang,
    ),
    list(
        area_symbols
    ),
    format_func=lambda value:
        area_labels[value],
    label_visibility="collapsed",
)


area_items = []

for ticker in area_symbols[
    selected_area
]:

    try:

        q = quote(
            ticker
        )

        df = history(
            ticker,
            "3mo",
        )

        area_items.append(
            {
                "ticker": ticker,
                "name": security_name(
                    ticker
                ),
                "price": q.get(
                    "price"
                ),
                "change_pct": q.get(
                    "change_pct"
                ),
                "df": df,
            }
        )

    except Exception:

        # One unavailable symbol should
        # not break the entire Discover page.
        continue


card_row(
    area_items,
    key_prefix="discover_area",
)


# =========================================================
# SCANNER RESULTS
# =========================================================

if rows:

    st.subheader(
        t(
            "latest",
            lang,
        )
    )

    st.caption(
        "Latest model scanner results"
    )

    items = []

    for row in rows[:16]:

        ticker = str(
            row.get(
                "ticker",
                "",
            )
        ).upper()

        if not ticker:
            continue

        try:

            q = quote(
                ticker
            )

        except Exception:

            q = {}

        try:

            df = history(
                ticker,
                "6mo",
            )

        except Exception:

            df = None

        items.append(
            {
                "ticker": ticker,

                "name": security_name(
                    ticker
                ),

                "price": q.get(
                    "price",
                    row.get(
                        "price"
                    ),
                ),

                "change_pct": q.get(
                    "change_pct",
                    row.get(
                        "change_pct"
                    ),
                ),

                "df": df,

                "signal": row.get(
                    "signal"
                ),

                "confidence": row.get(
                    "confidence"
                ),

                "reliability": row.get(
                    "reliability"
                ),

                "expected_return": row.get(
                    "expected_return"
                ),
            }
        )

    if items:

        card_row(
            items,
            key_prefix="discover",
        )

    else:

        st.warning(
            "Scanner results were returned, "
            "but none could be displayed."
        )


    # =====================================================
    # BULLISH SIGNALS
    # =====================================================

    bullish = [
        row
        for row in rows
        if str(
            row.get(
                "signal",
                "",
            )
        ).lower()
        == "bullish"
    ]


    if bullish:

        st.subheader(
            t(
                "bullish_signals",
                lang,
            )
        )

        bullish_items = []

        for row in bullish[:12]:

            ticker = str(
                row.get(
                    "ticker",
                    "",
                )
            ).upper()

            if not ticker:
                continue

            try:

                q = quote(
                    ticker
                )

            except Exception:

                q = {}

            try:

                df = history(
                    ticker,
                    "6mo",
                )

            except Exception:

                df = None

            bullish_items.append(
                {
                    "ticker": ticker,

                    "name": security_name(
                        ticker
                    ),

                    "price": q.get(
                        "price",
                        row.get(
                            "price"
                        ),
                    ),

                    "change_pct": q.get(
                        "change_pct",
                        row.get(
                            "change_pct"
                        ),
                    ),

                    "df": df,

                    "signal": row.get(
                        "signal"
                    ),

                    "confidence": row.get(
                        "confidence"
                    ),

                    "reliability": row.get(
                        "reliability"
                    ),

                    "expected_return": row.get(
                        "expected_return"
                    ),
                }
            )

        if bullish_items:

            card_row(
                bullish_items,
                key_prefix=(
                    "discover_bullish"
                ),
            )

else:

    if not scan_completed:

        st.info(
            t(
                "no_scan",
                lang,
            )
        )
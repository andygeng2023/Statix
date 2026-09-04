from __future__ import annotations

import streamlit as st

from src.data.market import history, quote
from src.data.search import security_name
from src.storage.database import get_settings, get_watchlist
from src.ui.components import card_row, t


settings = get_settings()

lang = st.session_state.get(
    "language_preference",
    settings.get("language", "en"),
)


st.markdown("# Home")
st.caption(
    "Market overview, saved symbols and model signals."
)


# ============================================================
# Data helpers
# ============================================================

def card_data(
    ticker: str,
    period: str,
):
    q = quote(ticker)

    df = history(
        ticker,
        period,
    )

    return q, df


def make_items(
    symbols: list[str],
    period: str,
    row_name: str,
):

    items = []

    for ticker in symbols:

        ticker = str(ticker).upper()

        try:
            q, df = card_data(
                ticker,
                period,
            )

            items.append(
                {
                    "ticker": ticker,
                    "name": security_name(ticker),
                    "price": q.get("price"),
                    "change_pct": q.get("change_pct"),
                    "df": df,
                }
            )

        except Exception:
            # One failed provider should not remove the rest
            # of the horizontal row.
            continue

    return items


# ============================================================
# Prevent duplicate symbols between Home sections
# ============================================================

watchlist = [
    str(x).upper()
    for x in get_watchlist()
]

watch_set = set(watchlist)


# ============================================================
# Market pulse
# ============================================================

pulse_candidates = [
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
    "VTI",
    "VOO",
]

pulse_symbols = [
    ticker
    for ticker in pulse_candidates
    if ticker not in watch_set
]


st.subheader(
    t("market_pulse", lang)
)

pulse_items = make_items(
    pulse_symbols,
    "3mo",
    "pulse",
)

card_row(
    pulse_items,
    row_key="home_pulse",
)


# ============================================================
# Watchlist
# ============================================================

if watchlist:

    st.subheader(
        t("watch_suggestions", lang)
    )

    watch_items = make_items(
        watchlist[:10],
        "6mo",
        "watchlist",
    )

    card_row(
        watch_items,
        row_key="home_watchlist",
    )


# ============================================================
# Featured
# ============================================================

already_shown = (
    set(pulse_symbols)
    | watch_set
)

featured_candidates = [
    "NVDA",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "AAPL",
    "AVGO",
    "TSLA",
]


featured_symbols = [
    ticker
    for ticker in featured_candidates
    if ticker not in already_shown
]


st.subheader(
    t("top_stocks", lang)
)

featured_items = make_items(
    featured_symbols,
    "6mo",
    "featured",
)

card_row(
    featured_items,
    row_key="home_featured",
)
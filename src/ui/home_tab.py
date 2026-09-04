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


def card_data(ticker, period="6mo"):
    q = quote(ticker)
    df = history(ticker, period)

    return q, df


watchlist = [
    str(x).upper()
    for x in get_watchlist()
]

watch_set = set(watchlist)


# ---------------------------------------
# MARKET PULSE
# ---------------------------------------

pulse_symbols = [
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
]

pulse_symbols = [
    ticker
    for ticker in pulse_symbols
    if ticker not in watch_set
]


# ---------------------------------------
# TOP STOCKS
# ---------------------------------------

featured_symbols = [
    "NVDA",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "AVGO",
    "TSLA",
    "AAPL",
]


already_used = set(
    pulse_symbols
) | watch_set


featured_symbols = [
    ticker
    for ticker in featured_symbols
    if ticker not in already_used
]


def make_items(symbols, period):
    items = []

    for ticker in symbols:
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

    return items


# ---------------------------------------
# MARKET PULSE
# ---------------------------------------

st.subheader(
    t("market_pulse", lang)
)

card_row(
    make_items(
        pulse_symbols,
        "3mo",
    ),
    key_prefix="home_pulse",
)


# ---------------------------------------
# WATCHLIST
# ---------------------------------------

if watchlist:

    st.subheader(
        t("watch_suggestions", lang)
    )

    card_row(
        make_items(
            watchlist[:8],
            "6mo",
        ),
        key_prefix="home_watchlist",
    )


# ---------------------------------------
# FEATURED
# ---------------------------------------

st.subheader(
    t("top_stocks", lang)
)

card_row(
    make_items(
        featured_symbols,
        "6mo",
    ),
    key_prefix="home_featured",
)
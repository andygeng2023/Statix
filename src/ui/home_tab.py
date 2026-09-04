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
st.caption("Market overview, saved symbols and model signals.")


@st.cache_data(ttl=300, show_spinner=False)
def load_card_data(ticker: str, period: str):
    q = quote(ticker)

    try:
        df = history(ticker, period)
    except Exception:
        df = None

    return q, df


@st.cache_data(ttl=3600, show_spinner=False)
def cached_security_name(ticker: str):
    return security_name(ticker)


def make_items(symbols: list[str], period: str):
    items = []

    for ticker in symbols:
        ticker = str(ticker).upper()

        try:
            q, df = load_card_data(ticker, period)
        except Exception:
            continue

        if not q:
            continue

        items.append(
            {
                "ticker": ticker,
                "name": cached_security_name(ticker),
                "price": q.get("price"),
                "change_pct": q.get("change_pct"),
                "df": df,
            }
        )

    return items


# ---------------------------------------------------------
# Watchlist
# ---------------------------------------------------------

watchlist = [
    str(x).upper()
    for x in get_watchlist()
]

watch_set = set(watchlist)


# ---------------------------------------------------------
# Market pulse
# ---------------------------------------------------------

pulse_symbols = [
    ticker
    for ticker in [
        "SPY",
        "QQQ",
        "DIA",
        "IWM",
    ]
    if ticker not in watch_set
]


# ---------------------------------------------------------
# Featured
# ---------------------------------------------------------

featured_candidates = [
    "NVDA",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "AVGO",
    "TSLA",
    "AAPL",
]

already_used = set(pulse_symbols) | watch_set

featured = [
    ticker
    for ticker in featured_candidates
    if ticker not in already_used
]


# ---------------------------------------------------------
# Render sections
# ---------------------------------------------------------

st.subheader(t("market_pulse", lang))

pulse_items = make_items(
    pulse_symbols,
    "3mo",
)

card_row(pulse_items)


if watchlist:

    st.subheader(
        t("watch_suggestions", lang)
    )

    watch_items = make_items(
        watchlist[:8],
        "6mo",
    )

    card_row(watch_items)


if featured:

    st.subheader(
        t("top_stocks", lang)
    )

    featured_items = make_items(
        featured,
        "6mo",
    )

    card_row(featured_items)
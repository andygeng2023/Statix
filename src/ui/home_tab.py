from __future__ import annotations

import streamlit as st

from src.data.market import history, quote
from src.data.search import security_name
from src.storage.database import get_settings, get_watchlist
from src.ui.components import clickable_card, money, pct, t


settings = get_settings()
lang = st.session_state.get("language_preference", settings.get("language", "en"))

st.markdown("# Home")
st.caption("Market overview, saved symbols and model signals.")


def card_data(ticker, history_period="6mo"):
    q = quote(ticker)
    df = history(ticker, history_period)
    return q, df


# Keep sections distinct so the same symbol is not repeated across Home.
watchlist = [str(x).upper() for x in get_watchlist()]
watch_symbols = set(watchlist)

pulse_symbols = ["SPY", "QQQ", "DIA", "IWM"]
market_symbols = [x for x in pulse_symbols if x not in watch_symbols]

# ---------------------------------------------------------
# Market pulse
# ---------------------------------------------------------
st.subheader(t("market_pulse", lang))
cols = st.columns(4)

for col, ticker in zip(cols, market_symbols):
    q, df = card_data(ticker, "3mo")
    with col:
        clickable_card(
            ticker=ticker,
            name=security_name(ticker),
            price=q.get("price"),
            change_pct=q.get("change_pct"),
            df=df,
        )

# ---------------------------------------------------------
# Watchlist
# ---------------------------------------------------------
if watchlist:
    st.subheader(t("watch_suggestions", lang))
    cols = st.columns(min(4, len(watchlist)))

    for col, ticker in zip(cols, watchlist[:4]):
        q, df = card_data(ticker, "6mo")
        with col:
            clickable_card(
                ticker=ticker,
                name=security_name(ticker),
                price=q.get("price"),
                change_pct=q.get("change_pct"),
                df=df,
            )

# ---------------------------------------------------------
# Featured stocks
# ---------------------------------------------------------
featured = ["NVDA", "MSFT", "GOOGL", "AMZN"]
featured = [x for x in featured if x not in watch_symbols and x not in set(market_symbols)]

if featured:
    st.subheader(t("top_stocks", lang))
    cols = st.columns(min(4, len(featured)))

    for col, ticker in zip(cols, featured):
        q, df = card_data(ticker, "6mo")
        with col:
            clickable_card(
                ticker=ticker,
                name=security_name(ticker),
                price=q.get("price"),
                change_pct=q.get("change_pct"),
                df=df,
            )

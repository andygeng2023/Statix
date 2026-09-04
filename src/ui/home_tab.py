from __future__ import annotations

import streamlit as st

from src.data.market import history, quote
from src.data.search import security_name
from src.storage.database import get_settings, get_watchlist
from src.ui.components import card_row, t

settings = get_settings()
lang = st.session_state.get("language_preference", settings.get("language", "en"))

st.markdown("# Home")
st.caption("Market overview, saved symbols and model signals.")


def card_data(ticker, history_period="6mo"):
    q = quote(ticker)
    df = history(ticker, history_period)
    return q, df

watchlist = [str(x).upper() for x in get_watchlist()]
watch_set = set(watchlist)
pulse_symbols = [x for x in ["SPY", "QQQ", "DIA", "IWM"] if x not in watch_set]
featured = [x for x in ["NVDA", "MSFT", "GOOGL", "AMZN"] if x not in watch_set and x not in set(pulse_symbols)]


def make_items(symbols, period):
    items = []
    for ticker in symbols:
        q, df = card_data(ticker, period)
        items.append({
            "ticker": ticker,
            "name": security_name(ticker),
            "price": q.get("price"),
            "change_pct": q.get("change_pct"),
            "df": df,
        })
    return items

st.subheader(t("market_pulse", lang))
card_row(make_items(pulse_symbols, "3mo"))

if watchlist:
    st.subheader(t("watch_suggestions", lang))
    card_row(make_items(watchlist[:8], "6mo"))

if featured:
    st.subheader(t("top_stocks", lang))
    card_row(make_items(featured, "6mo"))

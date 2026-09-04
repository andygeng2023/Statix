
import streamlit as st

from src.data.market import quote
from src.storage.database import get_settings, get_watchlist
from src.ui.components import money, pct, t


# ---------------------------------------------------------
# Settings / language
# ---------------------------------------------------------

settings = get_settings()
lang = settings.get("language", "en")


# ---------------------------------------------------------
# Page
# ---------------------------------------------------------

st.markdown("# Home")
st.caption("A compact view of the market and your saved symbols.")


def open_in_stocks(ticker, key_prefix):
    if st.button(
        "Open in Stocks",
        key=f"{key_prefix}_{ticker}",
        use_container_width=True,
    ):
        st.session_state["selected_ticker"] = ticker
        st.session_state["stocks_notice"] = ticker


def show_quote_card(container, ticker, key_prefix):
    q = quote(ticker)

    with container:
        st.metric(
            ticker,
            money(q.get("price")),
            pct(q.get("change_pct")),
        )

        provider = q.get("provider", "—")
        updated_at = q.get("updated_at", "—")

        st.caption(f"{provider} · {updated_at}")

        open_in_stocks(ticker, key_prefix)


# ---------------------------------------------------------
# Short Discover section
# ---------------------------------------------------------

st.subheader(t("discover_short", lang))

cols = st.columns(4)

for c, ticker in zip(
    cols,
    ["AAPL", "MSFT", "NVDA", "AMZN"],
):
    show_quote_card(c, ticker, "home_discover")


# ---------------------------------------------------------
# Live market pulse
# ---------------------------------------------------------

@st.fragment(run_every="15s")
def live_pulse():
    st.subheader(t("market_pulse", lang))

    cols = st.columns(4)

    for c, ticker in zip(
        cols,
        ["SPY", "QQQ", "DIA", "IWM"],
    ):
        show_quote_card(c, ticker, "home_pulse")


live_pulse()


# ---------------------------------------------------------
# Top stocks
# ---------------------------------------------------------

st.subheader(t("top_stocks", lang))

cols = st.columns(4)

for c, ticker in zip(
    cols,
    ["NVDA", "AAPL", "MSFT", "GOOGL"],
):
    show_quote_card(c, ticker, "home_top")


# ---------------------------------------------------------
# Watchlist suggestions
# ---------------------------------------------------------

wl = get_watchlist()[:4]

if wl:
    st.subheader(t("watch_suggestions", lang))

    cols = st.columns(min(4, len(wl)))

    for c, ticker in zip(cols, wl):
        show_quote_card(c, ticker, "home_watch")
import streamlit as st

from src.data.market import quote, history
from src.data.search import resolve_name
from src.storage.database import get_watchlist
from src.models.model import load_model
from src.models.features import create_features
from src.ui.components import stock_card, t

lang = st.session_state.get("language_preference", "en")

st.title(t("home", lang))
st.caption("Fast market overview. Detailed analysis is loaded only when you open a stock.")

def quick_signal(ticker):
    model = load_model()
    if model is None:
        return None
    df = history(ticker, "2y")
    if df.empty or len(df) < 64:
        return None
    market = history("SPY", "2y")
    f, _ = create_features(df, market, target=False)
    if len(f) < 64:
        return None
    return model.predict(f[model.feature_columns].tail(64).to_numpy())

st.subheader(t("discover_short", lang))
cols = st.columns(4)
for c, ticker in zip(cols, ["AAPL", "MSFT", "NVDA", "AMZN"]):
    q = quote(ticker)
    with c:
        st.metric(resolve_name(ticker), q.get("price", "—"), f'{q.get("change_pct", 0):+.2f}%' if q.get("change_pct") is not None else None)
        st.caption(ticker)
        if st.button("Open", key=f"home_open_{ticker}", use_container_width=True):
            st.session_state["selected_ticker"] = ticker
            st.session_state["active_tab"] = "stocks"
            st.rerun()

st.subheader(t("market_pulse", lang))
cols = st.columns(4)
for c, ticker in zip(cols, ["SPY", "QQQ", "DIA", "IWM"]):
    q = quote(ticker)
    with c:
        st.metric(ticker, q.get("price", "—"), f'{q.get("change_pct", 0):+.2f}%' if q.get("change_pct") is not None else None)
        st.caption(q.get("provider", "—"))

wl = get_watchlist()[:4]
if wl:
    st.subheader(t("watch_suggestions", lang))
    cols = st.columns(min(4, len(wl)))
    for c, ticker in zip(cols, wl):
        q = quote(ticker)
        with c:
            st.metric(resolve_name(ticker), q.get("price", "—"), f'{q.get("change_pct", 0):+.2f}%' if q.get("change_pct") is not None else None)
            st.caption(ticker)
            if st.button("Open", key=f"home_watch_{ticker}", use_container_width=True):
                st.session_state["selected_ticker"] = ticker
                st.session_state["active_tab"] = "stocks"
                st.rerun()

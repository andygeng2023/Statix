import streamlit as st
from src.data.market import get_quote
from src.storage.database import get_watchlist,recent
from src.ui.components import header,money,pct
header("Statix","Fast market intelligence and model-based outlooks.")
if st.button("Search a stock",use_container_width=True): st.switch_page("pages/search.py")
st.subheader("Market pulse")
cols=st.columns(3)
for c,t in zip(cols,["SPY","QQQ","DIA"]):
    q=get_quote(t); c.metric(t,money(q.get("price")),pct(q.get("change_pct")))
st.subheader("Popular")
cols=st.columns(4)
for c,t in zip(cols,["AAPL","MSFT","NVDA","AMZN"]):
    q=get_quote(t); c.metric(t,money(q.get("price")),pct(q.get("change_pct")))
    if c.button("Analyze",key="h"+t,use_container_width=True): st.session_state.selected_ticker=t; st.switch_page("pages/stock.py")
wl=get_watchlist()
if wl:
    st.subheader("Watchlist")
    cols=st.columns(min(4,len(wl)))
    for c,t in zip(cols,wl[:4]):
        q=get_quote(t); c.metric(t,money(q.get("price")),pct(q.get("change_pct")))
recent_tickers=recent()
if recent_tickers: st.caption("Recently viewed: "+" · ".join(recent_tickers))

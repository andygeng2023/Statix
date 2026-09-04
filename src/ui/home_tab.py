import streamlit as st
from src.data.market import quote,history
from src.storage.database import get_watchlist
from src.ui.components import money,pct,card,t

st.markdown("# Home")
st.caption("A compact view of the market and your saved symbols.")
# short discover section
st.subheader(t("discover_short",lang))
cols=st.columns(4)
for c,ticker in zip(cols,["AAPL","MSFT","NVDA","AMZN"]):
 q=quote(ticker)
 c.metric(ticker,money(q.get("price")),pct(q.get("change_pct")))
 if c.button(
      "Open in Stocks",
      key=f"home_stock_{ticker}",
      use_container_width=True,
    ):
      st.session_state["selected_ticker"] = ticker
      st.session_state["stocks_notice"] = ticker

@st.fragment(run_every="15s")
def live_pulse():
 st.subheader(t("market_pulse",lang))
 cols=st.columns(4)
 for c,ticker in zip(cols,["SPY","QQQ","DIA","IWM"]):
  q=quote(ticker)
  c.metric(ticker,money(q.get("price")),pct(q.get("change_pct")))
  c.caption(f"{q.get('provider','—')} · {q.get('updated_at','—')}")
  if c.button(
      "Open in Stocks",
      key=f"home_stock_{ticker}",
      use_container_width=True,
    ):
      st.session_state["selected_ticker"] = ticker
      st.session_state["stocks_notice"] = ticker
live_pulse()

st.subheader(t("top_stocks",lang))
cols=st.columns(4)
for c,ticker in zip(cols,["NVDA","AAPL","MSFT","GOOGL"]):
 q=quote(ticker)
 c.metric(ticker,money(q.get("price")),pct(q.get("change_pct")))
 if c.button(
      "Open in Stocks",
      key=f"home_stock_{ticker}",
      use_container_width=True,
    ):
      st.session_state["selected_ticker"] = ticker
      st.session_state["stocks_notice"] = ticker

wl=get_watchlist()[:4]
if wl:
 st.subheader(t("watch_suggestions",lang))
 cols=st.columns(min(4,len(wl)))
 for c,ticker in zip(cols,wl):
  q=quote(ticker)
  c.metric(ticker,money(q.get("price")),pct(q.get("change_pct")))
  if c.button(
      "Open in Stocks",
      key=f"home_stock_{ticker}",
      use_container_width=True,
    ):
      st.session_state["selected_ticker"] = ticker
      st.session_state["stocks_notice"] = ticker

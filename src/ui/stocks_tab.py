import streamlit as st
from src.data.search import search_stocks
from src.data.market import quote,history
from src.storage.database import get_watchlist,is_watched,add_to_watchlist,remove_from_watchlist,record_view
from src.models.model import load_model
from src.models.features import create_features
from src.ui.components import money,pct,card,t

search=st.text_input(t("search",lang),placeholder="Apple, NVDA, 000001…")
if search:
 results=search_stocks(search)
 if not results: st.info(t("no_results",lang))
 for i,r in enumerate(results):
  sym=r["symbol"]; q=quote(sym); a,b,c=st.columns([3,1.5,1.2]); a.markdown(f"**{sym}** · {r.get('name','')}"); a.caption(r.get("exchange", "")); b.metric(t("price",lang),money(q.get("price")),pct(q.get("change_pct")))
  if c.button(t("analyze",lang),key=f"an{i}"): st.session_state["selected_ticker"]=sym; st.rerun()

st.divider(); st.subheader(t("watchlist",lang))
wl=get_watchlist()
if not wl: st.info("Add symbols from search.")
for ticker in wl:
 q=quote(ticker); df=history(ticker,"1y"); a,b,c=st.columns([4,1.3,1])
 with a:
  card(ticker,q,df)
 with b:
  if st.button(t("analyze",lang),key="wa"+ticker): st.session_state["selected_ticker"]=ticker; record_view(ticker); st.rerun()
 with c:
  if st.button(t("remove",lang),key="wr"+ticker): remove_from_watchlist(ticker); st.rerun()

ticker=st.session_state.get("selected_ticker")
if ticker:
 st.divider(); st.subheader(ticker)
 q=quote(ticker); df=history(ticker,"5y")
 if q: st.metric(t("price",lang),money(q.get("price")),pct(q.get("change_pct")))
 if not df.empty: st.line_chart(df["close"],height=260)
 if not is_watched(ticker):
  if st.button(t("watch",lang),key="detailwatch"): add_to_watchlist(ticker); st.rerun()
 else:
  if st.button(t("remove",lang),key="detailremove"): remove_from_watchlist(ticker); st.rerun()
 model=load_model()
 if model is None: st.info(t("no_model",lang))
 elif not df.empty:
  market=history("SPY","5y"); f,cols=create_features(df,market,target=False)
  if len(f)>=64:
   X=f[model.feature_columns].tail(64).to_numpy(); p=model.predict(X); a,b,c,d=st.columns(4); a.metric("Signal",p["direction"]); b.metric(t("confidence",lang),f"{p['confidence']*100:.1f}%"); c.metric(t("reliability",lang),f"{p['reliability']*100:.1f}%"); d.metric(t("expected",lang),f"{p['expected_return']*100:+.2f}%")

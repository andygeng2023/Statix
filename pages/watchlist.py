import streamlit as st
from src.storage.database import get_watchlist,remove_from_watchlist
from src.data.market import get_quote
from src.ui.components import header,money,pct
header("Watchlist","Your saved symbols.")
wl=get_watchlist()
if not wl: st.info("Your watchlist is empty. Add stocks from Search.")
for t in wl:
    q=get_quote(t); a,b,c=st.columns([2,2,1]); a.markdown(f"**{t}**"); b.metric("Price",money(q.get("price")),pct(q.get("change_pct")))
    if c.button("Open",key="o"+t,use_container_width=True): st.session_state.selected_ticker=t; st.switch_page("pages/stock.py")
    if st.button("Remove",key="x"+t): remove_from_watchlist(t); st.rerun()

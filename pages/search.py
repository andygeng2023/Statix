import streamlit as st
from src.data.search import search_stocks
from src.data.market import get_quote
from src.storage.database import is_watched,add_to_watchlist,remove_from_watchlist
from src.ui.components import header,money,pct

header("Search","Find a stock or ETF by company name or symbol.")
q=st.text_input("Search",placeholder="Apple, Microsoft, NVDA…",label_visibility="collapsed")
if q.strip():
    results=search_stocks(q)
    if not results: st.info("No matching securities were found. Try a company name or ticker.")
    for i,r in enumerate(results):
        t=r["symbol"]; c1,c2,c3=st.columns([4,2,1.8])
        with c1:
            st.markdown(f"**{t}** · {r['name']}")
            st.caption(f"{r.get('exchange') or 'Exchange unavailable'} · {r.get('type','')}")
        with c2:
            # Avoid hammering the quote endpoint: only show quotes for the first four.
            if i<4:
                quote=get_quote(t); st.write(money(quote.get("price"))); st.caption(pct(quote.get("change_pct")))
            else: st.caption("Quote available on Stock page")
        with c3:
            if st.button("Analyze",key=f"a{i}",use_container_width=True): st.session_state.selected_ticker=t; st.switch_page("pages/stock.py")
            if is_watched(t):
                if st.button("Remove",key=f"r{i}",use_container_width=True): remove_from_watchlist(t); st.rerun()
            else:
                if st.button("Watch",key=f"w{i}",use_container_width=True): add_to_watchlist(t); st.rerun()

from __future__ import annotations
import requests
import streamlit as st

@st.cache_data(ttl=3600,max_entries=300,show_spinner=False)
def search_stocks(query,limit=12):
    q=str(query).strip()
    if not q:
        return []
    try:
        r=requests.get("https://query1.finance.yahoo.com/v1/finance/search",params={"q":q,"quotesCount":max(limit*2,20),"newsCount":0},timeout=8,headers={"User-Agent":"Statix/1.0"})
        r.raise_for_status(); data=r.json()
    except Exception:
        return []
    out=[]; seen=set()
    for x in data.get("quotes",[]):
        typ=x.get("quoteType","")
        if typ not in {"EQUITY","ETF","MUTUALFUND"}: continue
        symbol=str(x.get("symbol") or "").upper()
        if not symbol or symbol in seen: continue
        seen.add(symbol)
        out.append({"symbol":symbol,"name":x.get("longname") or x.get("shortname") or symbol,"exchange":x.get("exchange","") or "","type":typ})
    return out[:limit]

search_symbols=search_stocks

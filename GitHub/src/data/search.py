from __future__ import annotations
import requests
import streamlit as st

@st.cache_data(ttl=3600, max_entries=200)
def search_stocks(query, limit=12):
    q=str(query).strip()
    if not q: return []
    try:
        r=requests.get("https://query1.finance.yahoo.com/v1/finance/search",params={"q":q,"quotesCount":limit*2,"newsCount":0},timeout=8,headers={"User-Agent":"Statix/1.0"})
        r.raise_for_status(); data=r.json()
    except Exception:
        return []
    out=[]
    for x in data.get("quotes",[]):
        typ=x.get("quoteType","")
        if typ not in {"EQUITY","ETF","MUTUALFUND"}: continue
        s=x.get("symbol")
        if s: out.append({"symbol":s,"name":x.get("longname") or x.get("shortname") or s,"exchange":x.get("exchange","") or "","type":typ})
    return out[:limit]

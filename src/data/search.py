from __future__ import annotations
import difflib
import os
import requests
import streamlit as st

YAHOO_SEARCH = "https://query1.finance.yahoo.com/v1/finance/search"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
ALPACA_ASSETS = "https://api.alpaca.markets/v2/assets"


def _headers():
    email = os.getenv("SEC_USER_AGENT_EMAIL", "statix@example.com")
    return {"User-Agent": f"Statix/1.0 {email}", "Accept-Encoding": "gzip, deflate"}


@st.cache_data(ttl=86400, max_entries=2, show_spinner=False)
def _sec_universe():
    try:
        r = requests.get(SEC_TICKERS, headers=_headers(), timeout=15)
        r.raise_for_status()
        data = r.json()
        out=[]
        for x in data.values():
            sym=str(x.get("ticker") or "").upper().strip()
            name=str(x.get("title") or "").strip()
            cik=str(x.get("cik_str") or "")
            if sym and name:
                out.append({"symbol":sym,"name":name,"exchange":"SEC","type":"EQUITY","cik":cik})
        return out
    except Exception:
        return []


@st.cache_data(ttl=86400, max_entries=2, show_spinner=False)
def _alpaca_assets():
    key=os.getenv("APCA_API_KEY_ID")
    secret=os.getenv("APCA_API_SECRET_KEY")
    try:
        import streamlit as st
        key=st.secrets.get("alpaca_api_key", key)
        secret=st.secrets.get("alpaca_api_secret", secret)
    except Exception:
        pass
    if not key or not secret:
        return []
    try:
        r=requests.get(ALPACA_ASSETS, headers={"APCA-API-KEY-ID":str(key),"APCA-API-SECRET-KEY":str(secret)}, params={"status":"active","asset_class":"us_equity"}, timeout=15)
        r.raise_for_status()
        return [{"symbol":str(x.get("symbol") or "").upper(),"name":x.get("name") or x.get("symbol"),"exchange":x.get("exchange") or "","type":"EQUITY"}
                for x in r.json() if x.get("tradable", True)]
    except Exception:
        return []


def _rank(items, q, limit):
    q=q.lower().strip()
    def score(x):
        s=x["symbol"].lower(); n=x["name"].lower()
        exact = 1.0 if s == q else 0.0
        prefix = 0.65 if s.startswith(q) else 0.0
        name_prefix = 0.35 if n.startswith(q) else 0.0
        ratio=max(difflib.SequenceMatcher(None,q,s).ratio(), difflib.SequenceMatcher(None,q,n[:max(len(q),1)]).ratio())
        return exact+prefix+name_prefix+ratio
    return sorted(items,key=score,reverse=True)[:limit]


@st.cache_data(ttl=1800, max_entries=300, show_spinner=False)
def search_stocks(query, limit=12):
    q=str(query).strip()
    if not q:
        return []
    merged={}
    # Local SEC data is deterministic and avoids Yahoo's intermittent search endpoint failures.
    for x in _alpaca_assets()+_sec_universe():
        if not x.get("symbol"): continue
        sym=x["symbol"].upper()
        if q.lower() in sym.lower() or q.lower() in str(x.get("name","")).lower():
            merged[sym]=x
    if merged:
        return _rank(list(merged.values()),q,limit)
    # Yahoo is the third fallback for names not present in SEC/Alpaca results.
    try:
        r=requests.get(YAHOO_SEARCH, params={"q":q,"quotesCount":max(limit*3,30),"newsCount":0}, timeout=8, headers={"User-Agent":"Statix/1.0"})
        r.raise_for_status()
        out=[]
        for x in r.json().get("quotes",[]):
            if x.get("quoteType") not in {"EQUITY","ETF","MUTUALFUND"}: continue
            sym=str(x.get("symbol") or "").upper()
            if sym and sym not in merged:
                merged[sym]={"symbol":sym,"name":x.get("longname") or x.get("shortname") or sym,"exchange":x.get("exchange") or "","type":x.get("quoteType")}
        out=list(merged.values())
        if out: return _rank(out,q,limit)
    except Exception:
        pass
    return _rank(list(merged.values()),q,limit)

search_symbols=search_stocks

from __future__ import annotations
import difflib, os, requests
import pandas as pd
import streamlit as st
from src.data.providers import validate_symbol
from src.config import SEARCH_TTL
SEC_URL="https://www.sec.gov/files/company_tickers_exchange.json"

def _sec_headers():
    try: email=st.secrets.get("SEC_USER_AGENT_EMAIL","you@example.com")
    except Exception: email=os.getenv("SEC_USER_AGENT_EMAIL","you@example.com")
    return {"User-Agent":f"Statix/2.0 {email}","Accept-Encoding":"gzip, deflate"}

@st.cache_data(ttl=86400,show_spinner=False)
def sec_universe():
    try:
        r=requests.get(SEC_URL,headers=_sec_headers(),timeout=15); r.raise_for_status(); d=r.json(); rows=d.get("data",[])
        return pd.DataFrame([{"symbol":str(x[0]).upper(),"name":str(x[1]),"exchange":str(x[2] or "")} for x in rows if len(x)>=3])
    except Exception:return pd.DataFrame(columns=["symbol","name","exchange"])

def _qd_search(query):
    try:
        import streamlit as st
        from quantdash import QuantDash

        api_key = st.secrets.get("quantdash_api_key", "")

        if not api_key:
            return []

        client = QuantDash(api_key=api_key)

        result = client.quotes.get(
            universes="US_Stock",
            to_dataframe=True,
        )

        if result is None or result.empty:
            return []

        q = query.lower()

        rows = []

        for _, row in result.iterrows():
            values = " ".join(
                str(row.get(column, ""))
                for column in result.columns
            ).lower()

            if q in values:
                symbol = (
                    row.get("symbol")
                    or row.get("ticker")
                    or row.get("代码")
                )

                if symbol:
                    rows.append({
                        "symbol": str(symbol).upper(),
                        "name": str(
                            row.get("name")
                            or row.get("名称")
                            or symbol
                        ),
                        "exchange": str(
                            row.get("exchange", "")
                        ),
                        "type": "EQUITY",
                    })

            if len(rows) >= 20:
                break

        return rows

    except Exception:
        return []

def _yahoo_search(q):
    try:
        r=requests.get("https://query1.finance.yahoo.com/v1/finance/search",params={"q":q,"quotesCount":12,"newsCount":0},timeout=10); r.raise_for_status();
        return [{"symbol":x.get("symbol",""),"name":x.get("longname") or x.get("shortname") or x.get("symbol",""),"exchange":x.get("exchange",""),"type":x.get("quoteType","")} for x in r.json().get("quotes",[]) if x.get("symbol")]
    except Exception:return []

@st.cache_data(ttl=SEARCH_TTL,max_entries=500,show_spinner=False)
def search_stocks(query):
    q=query.strip();
    if not q:return []
    rows=[]; seen=set()
    for x in _qd_search(q)+_yahoo_search(q):
        s=x.get("symbol","").upper()
        if s and s not in seen: seen.add(s); rows.append(x)
    sec=sec_universe()
    if not sec.empty:
        qq=q.lower(); mask=sec.symbol.str.lower().str.contains(qq,na=False)|sec.name.str.lower().str.contains(qq,na=False)
        for _,r in sec[mask].head(15).iterrows():
            s=r.symbol
            if s not in seen: seen.add(s); rows.append({"symbol":s,"name":r.name,"exchange":r.exchange,"type":"EQUITY"})
    if not rows and len(q)<=12:
        syms=sec.symbol.tolist() if not sec.empty else []
        for s in difflib.get_close_matches(q.upper(),syms,n=10,cutoff=.55): rows.append({"symbol":s,"name":s,"exchange":"","type":"EQUITY"})
    # Last-resort exact-symbol validation prevents a provider outage from producing
    # a misleading empty search for a valid ticker such as AAPL or MSFT.
    if not rows and q.replace(".","").replace("-","").isalnum() and validate_symbol(q.upper()):
        rows.append({"symbol":q.upper(),"name":q.upper(),"exchange":"","type":"EQUITY"})
    return rows[:20]

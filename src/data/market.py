from __future__ import annotations
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf
import streamlit as st
from src.config import HISTORY_TTL, QUOTE_TTL

REQUIRED=["open","high","low","close","volume"]


def _clean(df):
    if df is None or df.empty:
        return pd.DataFrame()
    out=df.copy()
    if isinstance(out.columns,pd.MultiIndex):
        # yfinance can return (field, ticker) or (ticker, field).
        if len(out.columns.levels)>=2:
            if set(REQUIRED).intersection({str(x).lower() for x in out.columns.get_level_values(0)}):
                out.columns=[str(c[0]).lower() for c in out.columns]
            else:
                out.columns=[str(c[-1]).lower() for c in out.columns]
    out.columns=[str(c).lower().replace(" ","_") for c in out.columns]
    out=out.rename(columns={"adj_close":"close"})
    for c in REQUIRED:
        if c in out:
            out[c]=pd.to_numeric(out[c],errors="coerce")
    if not all(c in out for c in REQUIRED):
        return pd.DataFrame()
    return out[REQUIRED].dropna(subset=["close"]).sort_index()


@st.cache_data(ttl=HISTORY_TTL,max_entries=250,show_spinner=False)
def get_stock_data(ticker,period="5y",interval="1d"):
    ticker=str(ticker).strip().upper()
    if not ticker:
        return pd.DataFrame()
    try:
        df=yf.download(ticker,period=period,interval=interval,auto_adjust=True,progress=False,threads=False)
        out=_clean(df)
        if out.empty:
            return pd.DataFrame()
        return out
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=QUOTE_TTL,max_entries=750,show_spinner=False)
def get_quote(ticker):
    ticker=str(ticker).strip().upper()
    if not ticker:
        return {"ticker":"","price":None,"change_pct":None,"updated_at":None,"error":"Invalid symbol"}
    try:
        t=yf.Ticker(ticker)
        fi=getattr(t,"fast_info",{}) or {}
        price=fi.get("last_price") or fi.get("regular_market_price")
        prev=fi.get("previous_close")
        if price is None:
            h=_clean(t.history(period="5d",interval="1d",auto_adjust=True))
            if h.empty:
                return {"ticker":ticker,"price":None,"change_pct":None,"updated_at":None,"error":"No market data returned."}
            price=float(h["close"].iloc[-1])
            prev=float(h["close"].iloc[-2]) if len(h)>1 else None
        price=float(price)
        change=((price-float(prev))/float(prev)*100) if prev not in (None,0) else None
        return {"ticker":ticker,"price":price,"change_pct":change,"updated_at":datetime.now(timezone.utc).isoformat(),"error":None}
    except Exception as exc:
        return {"ticker":ticker,"price":None,"change_pct":None,"updated_at":None,"error":str(exc)}


def clear_market_cache():
    get_stock_data.clear(); get_quote.clear()

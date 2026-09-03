from __future__ import annotations
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime, timezone
from src.config import HISTORY_TTL, QUOTE_TTL

REQUIRED=["open","high","low","close","volume"]

def _clean(df):
    if df is None or df.empty: return pd.DataFrame()
    out=df.copy()
    if isinstance(out.columns,pd.MultiIndex):
        out.columns=[str(c[0]).lower() if isinstance(c,tuple) else str(c).lower() for c in out.columns]
    out.columns=[str(c).lower().replace(" ","_") for c in out.columns]
    rename={"adj_close":"close"}
    out=out.rename(columns=rename)
    for c in REQUIRED:
        if c in out: out[c]=pd.to_numeric(out[c],errors="coerce")
    if not all(c in out for c in REQUIRED): return pd.DataFrame()
    return out[REQUIRED].dropna(subset=["close"]).sort_index()

@st.cache_data(ttl=HISTORY_TTL, max_entries=200)
def get_stock_data(ticker, period="5y", interval="1d"):
    ticker=str(ticker).strip().upper()
    try:
        df=yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False, threads=False)
        out=_clean(df)
        if out.empty: raise ValueError(f"No market data for {ticker}")
        return out
    except Exception as e:
        raise ValueError(f"Market data unavailable for {ticker}: {e}") from e

@st.cache_data(ttl=QUOTE_TTL, max_entries=500)
def get_quote(ticker):
    ticker=str(ticker).strip().upper()
    try:
        t=yf.Ticker(ticker)
        fi=getattr(t,"fast_info",{}) or {}
        price=fi.get("last_price") or fi.get("regular_market_price")
        prev=fi.get("previous_close")
        if price is None:
            h=_clean(t.history(period="5d", interval="1d", auto_adjust=True))
            if h.empty: raise ValueError("no quote")
            price=float(h["close"].iloc[-1]); prev=float(h["close"].iloc[-2]) if len(h)>1 else None
        price=float(price); change_pct=((price-float(prev))/float(prev)*100) if prev else None
        return {"ticker":ticker,"price":price,"change_pct":change_pct,"updated_at":datetime.now(timezone.utc).isoformat()}
    except Exception:
        try:
            h=get_stock_data(ticker,period="5d")
            price=float(h["close"].iloc[-1]); prev=float(h["close"].iloc[-2]) if len(h)>1 else None
            return {"ticker":ticker,"price":price,"change_pct":((price-prev)/prev*100 if prev else None),"updated_at":datetime.now(timezone.utc).isoformat()}
        except Exception as e:
            return {"ticker":ticker,"price":None,"change_pct":None,"updated_at":None,"error":str(e)}

def clear_market_cache():
    get_stock_data.clear(); get_quote.clear()

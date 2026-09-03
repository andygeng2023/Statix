from __future__ import annotations
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from src.config import HISTORY_TTL, QUOTE_TTL
from src.data.providers import alpaca_history, alpaca_quote, yahoo_history, yahoo_quote


def _empty(ticker, error):
    return {"ticker": ticker, "price": None, "change_pct": None, "updated_at": None, "provider": None, "error": error}


@st.cache_data(ttl=HISTORY_TTL, max_entries=300, show_spinner=False)
def get_stock_data(ticker, period="5y", interval="1d"):
    ticker = str(ticker).strip().upper()
    if not ticker:
        return pd.DataFrame()
    # Alpaca first; Yahoo remains a broad fallback.
    limit = 1500 if period == "5y" else 400
    df = alpaca_history(ticker, limit=limit)
    if not df.empty:
        return df
    return yahoo_history(ticker, period=period, interval=interval)


@st.cache_data(ttl=QUOTE_TTL, max_entries=1000, show_spinner=False)
def get_quote(ticker):
    ticker = str(ticker).strip().upper()
    if not ticker:
        return _empty("", "Invalid symbol")
    q = alpaca_quote(ticker)
    if q:
        # Calculate day change from the previous completed daily bar.
        h = get_stock_data(ticker, period="5d", interval="1d")
        if len(h) > 1 and q.get("price"):
            prev = float(h["close"].iloc[-1])
            if prev and abs(float(q["price"])-prev) > 1e-9:
                q["change_pct"] = (float(q["price"])-prev) / prev * 100
        return q
    q = yahoo_quote(ticker)
    return q or _empty(ticker, "No market data returned by Alpaca or Yahoo.")


def clear_market_cache():
    get_stock_data.clear()
    get_quote.clear()

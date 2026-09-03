from __future__ import annotations

from datetime import datetime, timezone
import os
import requests
import pandas as pd
import yfinance as yf

ALPACA_DATA_URL = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets")


def _secret(name: str, default=None):
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)


def alpaca_credentials():
    key = _secret("alpaca_api_key") or os.getenv("APCA_API_KEY_ID")
    secret = _secret("alpaca_api_secret") or os.getenv("APCA_API_SECRET_KEY")
    return key, secret


def _alpaca_headers():
    key, secret = alpaca_credentials()
    if not key or not secret:
        return None
    return {"APCA-API-KEY-ID": str(key), "APCA-API-SECRET-KEY": str(secret)}


def alpaca_enabled() -> bool:
    return bool(_alpaca_headers())


def _clean_ohlcv(rows):
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    rename = {"o":"open", "h":"high", "l":"low", "c":"close", "v":"volume"}
    df = df.rename(columns=rename)
    needed = ["open", "high", "low", "close", "volume"]
    if not all(x in df.columns for x in needed):
        return pd.DataFrame()
    df[needed] = df[needed].apply(pd.to_numeric, errors="coerce")
    if "t" in df.columns:
        df.index = pd.to_datetime(df["t"], utc=True, errors="coerce")
    return df[needed].dropna(subset=["close"]).sort_index()


def alpaca_history(ticker: str, limit: int = 1500, feed: str = "iex") -> pd.DataFrame:
    headers = _alpaca_headers()
    if not headers:
        return pd.DataFrame()
    url = f"{ALPACA_DATA_URL.rstrip('/')}/v2/stocks/{ticker.upper()}/bars"
    params = {"timeframe": "1Day", "limit": min(int(limit), 10000), "feed": feed, "adjustment": "all"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=12)
        r.raise_for_status()
        return _clean_ohlcv(r.json().get("bars", []))
    except Exception:
        return pd.DataFrame()


def alpaca_quote(ticker: str) -> dict:
    headers = _alpaca_headers()
    if not headers:
        return {}
    symbol = ticker.upper()
    url = f"{ALPACA_DATA_URL.rstrip('/')}/v2/stocks/{symbol}/quotes/latest"
    try:
        r = requests.get(url, headers=headers, params={"feed": "iex"}, timeout=8)
        r.raise_for_status()
        q = (r.json() or {}).get("quote") or {}
        ask = q.get("ap")
        bid = q.get("bp")
        price = ask or bid
        if price is None:
            return {}
        ts = q.get("t")
        return {"ticker": symbol, "price": float(price), "change_pct": None,
                "updated_at": ts or datetime.now(timezone.utc).isoformat(), "provider": "alpaca", "error": None}
    except Exception:
        return {}


def yahoo_history(ticker: str, period="5y", interval="1d") -> pd.DataFrame:
    try:
        raw = yf.download(ticker.upper(), period=period, interval=interval, auto_adjust=True, progress=False, threads=False)
        if raw is None or raw.empty:
            return pd.DataFrame()
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = [str(c[0] if str(c[0]).lower() in {"open","high","low","close","volume"} else c[-1]).lower() for c in raw.columns]
        raw.columns = [str(c).lower().replace(" ", "_") for c in raw.columns]
        raw = raw.rename(columns={"adj_close": "close"})
        cols = ["open","high","low","close","volume"]
        if not all(c in raw.columns for c in cols):
            return pd.DataFrame()
        raw[cols] = raw[cols].apply(pd.to_numeric, errors="coerce")
        return raw[cols].dropna(subset=["close"]).sort_index()
    except Exception:
        return pd.DataFrame()


def yahoo_quote(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker.upper())
        fi = getattr(t, "fast_info", {}) or {}
        price = fi.get("last_price") or fi.get("regular_market_price")
        prev = fi.get("previous_close")
        if price is None:
            h = yahoo_history(ticker, period="5d", interval="1d")
            if h.empty:
                return {}
            price = float(h["close"].iloc[-1])
            prev = float(h["close"].iloc[-2]) if len(h) > 1 else None
        change = ((float(price)-float(prev))/float(prev)*100) if prev not in (None,0) else None
        return {"ticker": ticker.upper(), "price": float(price), "change_pct": change,
                "updated_at": datetime.now(timezone.utc).isoformat(), "provider": "yahoo", "error": None}
    except Exception:
        return {}

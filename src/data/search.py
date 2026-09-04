from __future__ import annotations

import difflib
import os
import re
import requests
import pandas as pd
import streamlit as st
from src.data.providers import validate_symbol
from src.config import SEARCH_TTL

SEC_URL = "https://www.sec.gov/files/company_tickers_exchange.json"


def _sec_headers():
    try:
        email = st.secrets.get("SEC_USER_AGENT_EMAIL", "you@example.com")
    except Exception:
        email = os.getenv("SEC_USER_AGENT_EMAIL", "you@example.com")
    return {"User-Agent": f"Statix/3.0 {email}", "Accept-Encoding": "gzip, deflate"}


@st.cache_data(ttl=86400, show_spinner=False)
def sec_universe():
    try:
        r = requests.get(SEC_URL, headers=_sec_headers(), timeout=15)
        r.raise_for_status()
        rows = r.json().get("data", [])
        return pd.DataFrame([
            {"symbol": str(x[0]).upper(), "name": str(x[1]), "exchange": str(x[2] or "")}
            for x in rows if len(x) >= 3
        ])
    except Exception:
        return pd.DataFrame(columns=["symbol", "name", "exchange"])


def _yahoo_search(query):
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/search",
            params={"q": query, "quotesCount": 20, "newsCount": 0},
            timeout=8,
        )
        r.raise_for_status()
        out = []
        for x in r.json().get("quotes", []):
            symbol = x.get("symbol")
            if symbol:
                out.append({
                    "symbol": symbol.upper(),
                    "name": x.get("longname") or x.get("shortname") or symbol,
                    "exchange": x.get("exchange", ""),
                    "type": x.get("quoteType", ""),
                })
        return out
    except Exception:
        return []


def _fuzzy_rows(query: str, universe: pd.DataFrame, limit=12):
    if universe.empty:
        return []
    q = re.sub(r"[^a-z0-9]+", "", query.lower())
    if not q:
        return []

    candidates = []
    for row in universe.itertuples(index=False):
        symbol = str(row.symbol)
        name = str(row.name)
        ns = re.sub(r"[^a-z0-9]+", "", symbol.lower())
        nn = re.sub(r"[^a-z0-9]+", "", name.lower())
        score = max(
            difflib.SequenceMatcher(None, q, ns).ratio(),
            difflib.SequenceMatcher(None, q, nn).ratio(),
        )
        if q in ns:
            score += 0.35
        if q in nn:
            score += 0.25
        candidates.append((score, {
            "symbol": symbol,
            "name": name,
            "exchange": str(row.exchange),
            "type": "EQUITY",
        }))
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in candidates[:limit] if x[0] >= 0.45]


@st.cache_data(ttl=SEARCH_TTL, max_entries=500, show_spinner=False)
def search_stocks(query):
    q = query.strip()
    if not q:
        return []

    rows, seen = [], set()

    def add(item):
        s = str(item.get("symbol", "")).upper()
        if s and s not in seen:
            seen.add(s)
            item["symbol"] = s
            rows.append(item)

    for item in _yahoo_search(q):
        add(item)

    sec = sec_universe()
    if not sec.empty:
        ql = q.lower()
        mask = (
            sec.symbol.str.lower().eq(ql)
            | sec.name.str.lower().str.contains(re.escape(q), na=False)
        )
        for _, row in sec[mask].head(20).iterrows():
            add({"symbol": row.symbol, "name": row.name, "exchange": row.exchange, "type": "EQUITY"})

        # Fuzzy matching makes misspellings such as "Aple" or partial
        # company names useful instead of returning an empty result.
        for item in _fuzzy_rows(q, sec, limit=12):
            add(item)

    if not rows and re.fullmatch(r"[A-Za-z0-9.-]{1,20}", q):
        if validate_symbol(q.upper()):
            add({"symbol": q.upper(), "name": q.upper(), "exchange": "", "type": "EQUITY"})

    return rows[:20]


@st.cache_data(ttl=86400, max_entries=2000, show_spinner=False)
def resolve_name(ticker: str) -> str:
    symbol = ticker.strip().upper()
    if not symbol:
        return symbol

    sec = sec_universe()
    if not sec.empty:
        hit = sec[sec.symbol == symbol]
        if not hit.empty:
            return str(hit.iloc[0]["name"])

    # Yahoo's search endpoint is inexpensive and also handles non-US symbols.
    rows = _yahoo_search(symbol)
    for row in rows:
        if row["symbol"].upper() == symbol:
            return row["name"]

    if symbol.split(".")[0].isdigit():
        try:
            import akshare as ak
            data = ak.stock_zh_a_spot_em()
            hit = data[data["代码"].astype(str) == symbol.split(".")[0]]
            if not hit.empty:
                return str(hit.iloc[0]["名称"])
        except Exception:
            pass

    return symbol

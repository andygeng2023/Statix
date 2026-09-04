from __future__ import annotations

import difflib
import os
import re

import pandas as pd
import requests
import streamlit as st

from src.config import SEARCH_TTL
from src.data.providers import validate_symbol

SEC_URL = "https://www.sec.gov/files/company_tickers_exchange.json"


def _sec_headers():
    try:
        email = st.secrets.get("SEC_USER_AGENT_EMAIL", "you@example.com")
    except Exception:
        email = os.getenv("SEC_USER_AGENT_EMAIL", "you@example.com")
    return {
        "User-Agent": f"Statix/2.0 {email}",
        "Accept-Encoding": "gzip, deflate",
    }


@st.cache_data(ttl=86400, show_spinner=False)
def sec_universe():
    try:
        response = requests.get(
            SEC_URL,
            headers=_sec_headers(),
            timeout=15,
        )
        response.raise_for_status()
        rows = response.json().get("data", [])
        return pd.DataFrame(
            [
                {
                    "symbol": str(x[0]).upper(),
                    "name": str(x[1]),
                    "exchange": str(x[2] or ""),
                }
                for x in rows
                if len(x) >= 3
            ]
        )
    except Exception:
        return pd.DataFrame(columns=["symbol", "name", "exchange"])


def _yahoo_search(query):
    try:
        response = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/search",
            params={"q": query, "quotesCount": 20, "newsCount": 0},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
        return [
            {
                "symbol": x.get("symbol", ""),
                "name": x.get("longname") or x.get("shortname") or x.get("symbol", ""),
                "exchange": x.get("exchange", ""),
                "type": x.get("quoteType", ""),
            }
            for x in result.get("quotes", [])
            if x.get("symbol")
        ]
    except Exception:
        return []


def _qd_search(query):
    try:
        from quantdash import QuantDash

        api_key = st.secrets.get("quantdash_api_key", "")
        if not api_key:
            return []

        client = QuantDash(api_key=api_key)
        result = client.quotes.get(universes="US_Stock", to_dataframe=True)
        if result is None or result.empty:
            return []

        q = query.lower().strip()
        rows = []
        for _, row in result.iterrows():
            values = " ".join(str(row.get(c, "")) for c in result.columns).lower()
            if q in values:
                symbol = row.get("symbol") or row.get("ticker") or row.get("代码")
                if symbol:
                    rows.append({
                        "symbol": str(symbol).upper(),
                        "name": str(row.get("name") or row.get("名称") or symbol),
                        "exchange": str(row.get("exchange", "")),
                        "type": "EQUITY",
                    })
            if len(rows) >= 20:
                break
        return rows
    except Exception:
        return []


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


@st.cache_data(ttl=86400, show_spinner=False)
def _security_directory():
    sec = sec_universe()
    if sec.empty:
        return {}
    return {
        row.symbol: {
            "symbol": row.symbol,
            "name": row.name,
            "exchange": row.exchange,
            "type": "EQUITY",
        }
        for row in sec.itertuples()
    }


@st.cache_data(ttl=SEARCH_TTL, max_entries=500, show_spinner=False)
def search_stocks(query):
    q = str(query).strip()
    if not q:
        return []

    rows = []
    seen = set()

    def add(item):
        symbol = str(item.get("symbol", "")).upper().strip()
        if not symbol or symbol in seen:
            return
        seen.add(symbol)
        item = dict(item)
        item["symbol"] = symbol
        rows.append(item)

    for item in _qd_search(q) + _yahoo_search(q):
        add(item)

    directory = _security_directory()
    nq = _normalize_text(q)

    # Exact/substring matches against SEC symbol and company name.
    for item in directory.values():
        ns = _normalize_text(item["symbol"])
        nn = _normalize_text(item["name"])
        if nq in ns or nq in nn:
            add(item)
            if len(rows) >= 20:
                return rows

    # Fuzzy matching makes small typos useful: Aple -> Apple.
    candidates = list(directory.values())
    scored = []
    for item in candidates:
        symbol = _normalize_text(item["symbol"])
        name = _normalize_text(item["name"])
        score_symbol = difflib.SequenceMatcher(None, nq, symbol).ratio()
        score_name = difflib.SequenceMatcher(None, nq, name).ratio()
        score = max(score_symbol, score_name)
        if score >= 0.48:
            scored.append((score, item))

    for _, item in sorted(scored, key=lambda x: x[0], reverse=True)[:20]:
        add(item)

    if not rows and q.replace(".", "").replace("-", "").isalnum() and validate_symbol(q.upper()):
        add({
            "symbol": q.upper(),
            "name": q.upper(),
            "exchange": "",
            "type": "EQUITY",
        })

    return rows[:20]


@st.cache_data(ttl=86400, max_entries=2000, show_spinner=False)
def security_name(ticker: str) -> str:
    symbol = str(ticker).upper().strip()
    directory = _security_directory()
    item = directory.get(symbol)
    if item:
        return item["name"]

    # Numeric/non-US identifiers can often be resolved through Yahoo search.
    results = _yahoo_search(symbol)
    if results:
        return results[0].get("name") or symbol

    return symbol

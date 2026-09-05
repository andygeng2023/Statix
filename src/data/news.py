from __future__ import annotations

import re
from datetime import datetime, timezone

import streamlit as st
import yfinance as yf

POSITIVE = {"beat", "beats", "growth", "upgrade", "strong", "surge", "record", "profit", "bullish", "outperform"}
NEGATIVE = {"miss", "misses", "cut", "downgrade", "weak", "drop", "loss", "bearish", "lawsuit", "risk"}


def _sentiment(text: str) -> str:
    words = set(re.findall(r"[a-z]+", text.lower()))
    score = len(words & POSITIVE) - len(words & NEGATIVE)
    return "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"


@st.cache_data(ttl=900, max_entries=500, show_spinner=False)
def latest_news(ticker: str, limit: int = 8) -> list[dict]:
    try:
        items = yf.Ticker(ticker.upper()).news or []
    except Exception:
        return []
    rows = []
    for item in items[:limit]:
        content = item.get("content", item)
        title = content.get("title") or item.get("title")
        if not title:
            continue
        publisher = content.get("provider", {}).get("displayName") or item.get("publisher") or "News"
        link = content.get("canonicalUrl", {}).get("url") or item.get("link") or ""
        timestamp = content.get("pubDate") or item.get("providerPublishTime")
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")
        rows.append({
            "title": str(title),
            "publisher": str(publisher),
            "url": str(link),
            "date": str(timestamp or ""),
            "sentiment": _sentiment(str(title)),
        })
    return rows

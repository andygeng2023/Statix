from __future__ import annotations
import streamlit as st
from src.data.providers import get_quote,get_history
from src.config import QUOTE_TTL,HISTORY_TTL

@st.cache_data(ttl=1,max_entries=500,show_spinner=False)
def quote(ticker):
	symbol = ticker.upper()
	result = get_quote(symbol)
	recent = None

	required_fields = ("price", "change_pct", "open", "high", "low")
	if not result or any(result.get(field) is None for field in required_fields):
		recent = get_history(symbol, period="5d", limit=10)
		if recent is not None and not recent.empty and "close" in recent:
			close = recent["close"].dropna()
			if not close.empty:
				price = float(close.iloc[-1])
				previous = float(close.iloc[-2]) if len(close) > 1 else None
				latest = recent.iloc[-1]
				result = {
					**result,
					"ticker": symbol,
					"price": result.get("price") or price,
					"open": result.get("open") or float(latest.get("open", price)),
					"high": result.get("high") or float(latest.get("high", price)),
					"low": result.get("low") or float(latest.get("low", price)),
				}
				if result.get("change_pct") is None and previous not in (None, 0):
					result["change_pct"] = (price - previous) / previous * 100

	return result

@st.cache_data(ttl=1,max_entries=500,show_spinner=False)
def history(ticker,period="1y"): return get_history(ticker.upper(),period=period)

def clear_caches(): st.cache_data.clear()

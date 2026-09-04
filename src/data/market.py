from __future__ import annotations
import streamlit as st
from src.data.providers import get_quote,get_history
from src.config import QUOTE_TTL,HISTORY_TTL

@st.cache_data(ttl=QUOTE_TTL,max_entries=500,show_spinner=False)
def quote(ticker): return get_quote(ticker.upper())

@st.cache_data(ttl=HISTORY_TTL,max_entries=500,show_spinner=False)
def history(ticker,period="1y"): return get_history(ticker.upper(),period=period)

def clear_caches(): st.cache_data.clear()

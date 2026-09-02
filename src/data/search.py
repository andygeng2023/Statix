import requests
import streamlit as st


SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"


@st.cache_data(ttl=3600, show_spinner=False)
def search_symbols(query: str):

    query = query.strip()

    if not query:
        return []

    try:
        response = requests.get(
            SEARCH_URL,
            params={
                "q": query,
                "quotesCount": 15,
                "newsCount": 0,
            },
            headers={
                "User-Agent": "Mozilla/5.0",
            },
            timeout=8,
        )

        response.raise_for_status()

        data = response.json()

    except Exception:
        return []

    results = []

    for item in data.get("quotes", []):

        quote_type = item.get("quoteType", "")

        if quote_type not in {
            "EQUITY",
            "ETF",
            "MUTUALFUND",
        }:
            continue

        symbol = item.get("symbol")

        if not symbol:
            continue

        results.append(
            {
                "symbol": symbol,
                "name": (
                    item.get("longname")
                    or item.get("shortname")
                    or symbol
                ),
                "exchange": item.get("exchange", ""),
                "type": quote_type,
            }
        )

    return results
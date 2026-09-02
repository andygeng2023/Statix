import requests
import streamlit as st


@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def search_stocks(query: str):
    query = query.strip()

    if not query:
        return []

    url = (
        "https://query1.finance.yahoo.com/"
        "v1/finance/search"
    )

    params = {
        "q": query,
        "quotesCount": 20,
        "newsCount": 0,
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("quotes", []):
        symbol = item.get("symbol")

        if not symbol:
            continue

        quote_type = item.get(
            "quoteType",
            "",
        )

        # Keep actual tradable/security results.
        if quote_type not in {
            "EQUITY",
            "ETF",
            "MUTUALFUND",
        }:
            continue

        results.append(
            {
                "symbol": symbol,
                "name": (
                    item.get("longname")
                    or item.get("shortname")
                    or symbol
                ),
                "exchange": item.get(
                    "exchange",
                    "",
                ),
                "type": quote_type,
            }
        )

    return results
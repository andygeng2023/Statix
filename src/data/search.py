import requests
import streamlit as st


@st.cache_data(ttl=3600, show_spinner=False)
def search_stocks(query: str):

    query = query.strip()

    if not query:
        return []

    url = (
        "https://query1.finance.yahoo.com/"
        "v1/finance/search"
    )

    try:
        response = requests.get(
            url,
            params={
                "q": query,
                "quotesCount": 20,
                "newsCount": 0,
            },
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10,
        )

        response.raise_for_status()

        payload = response.json()

    except (
        requests.RequestException,
        ValueError,
    ):
        return []

    results = []

    for item in payload.get("quotes", []):

        quote_type = item.get("quoteType")

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
                "exchange": (
                    item.get("exchange")
                    or ""
                ),
                "type": quote_type,
            }
        )

    return results
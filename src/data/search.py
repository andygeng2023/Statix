import requests
import streamlit as st


SEARCH_URL = (
    "https://query1.finance.yahoo.com/"
    "v1/finance/search"
)


@st.cache_data(
    ttl=3600,
    max_entries=2000,
    show_spinner=False,
)
def search_stocks(
    query: str,
    limit: int = 15,
):

    query = query.strip()

    if not query:
        return []

    try:

        response = requests.get(
            SEARCH_URL,
            params={
                "q": query,
                "quotesCount": limit,
                "newsCount": 0,
            },
            timeout=5,
        )

        response.raise_for_status()

        payload = response.json()

        results = []

        for item in payload.get(
            "quotes",
            [],
        ):

            symbol = item.get("symbol")

            if not symbol:
                continue

            name = (
                item.get("longname")
                or item.get("shortname")
                or symbol
            )

            results.append(
                {
                    "symbol": symbol.upper(),
                    "name": name,
                    "type": item.get(
                        "quoteType",
                        "",
                    ),
                    "exchange": item.get(
                        "exchange",
                        "",
                    ),
                }
            )

        return results[:limit]

    except Exception:
        return []


search_symbols = search_stocks
from __future__ import annotations

from typing import Any

import requests
import streamlit as st


SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"


@st.cache_data(ttl=3600, show_spinner=False)
def search_symbols(
    query: str,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """
    Search Yahoo Finance for supported securities.

    Returns normalized dictionaries containing:
        symbol
        name
        exchange
        type
    """

    query = str(query or "").strip()

    if not query:
        return []

    limit = max(1, min(int(limit), 25))

    try:
        response = requests.get(
            SEARCH_URL,
            params={
                "q": query,
                "quotesCount": limit,
                "newsCount": 0,
            },
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            },
            timeout=8,
        )

        response.raise_for_status()
        data = response.json()

    except Exception:
        return []

    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in data.get("quotes", []):
        quote_type = str(
            item.get("quoteType", "")
        ).upper()

        if quote_type not in {
            "EQUITY",
            "ETF",
            "MUTUALFUND",
        }:
            continue

        symbol = str(
            item.get("symbol") or ""
        ).strip().upper()

        if not symbol or symbol in seen:
            continue

        seen.add(symbol)

        name = (
            item.get("longname")
            or item.get("shortname")
            or symbol
        )

        results.append(
            {
                "symbol": symbol,
                "name": str(name),
                "exchange": str(
                    item.get("exchange")
                    or item.get("fullExchangeName")
                    or ""
                ),
                "type": quote_type,
            }
        )

        if len(results) >= limit:
            break

    return results


def search_stocks(
    query: str,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """
    Backwards-compatible public search function.

    Search pages can use either search_stocks() or
    search_symbols().
    """

    return search_symbols(
        query=query,
        limit=limit,
    )


def clear_search_cache() -> None:
    search_symbols.clear()
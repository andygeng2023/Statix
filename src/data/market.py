import streamlit as st

from src.config import (
    HISTORY_CACHE_SECONDS,
    QUOTE_CACHE_SECONDS,
)
from src.data.providers.yahoo import YahooProvider


_PROVIDER = YahooProvider()


@st.cache_data(
    ttl=QUOTE_CACHE_SECONDS,
    max_entries=20_000,
    show_spinner=False,
)
def get_quote(ticker: str) -> dict:
    return _PROVIDER.get_quote(ticker)


@st.cache_data(
    ttl=QUOTE_CACHE_SECONDS,
    max_entries=20_000,
    show_spinner=False,
)
def get_quotes(tickers: tuple[str, ...]) -> dict:
    return _PROVIDER.get_quotes(list(tickers))


@st.cache_data(
    ttl=HISTORY_CACHE_SECONDS,
    max_entries=5_000,
    show_spinner=False,
)
def get_stock_data(
    ticker: str,
    period: str = "5y",
    interval: str = "1d",
):
    return _PROVIDER.get_history(
        ticker,
        period,
        interval,
    )


def clear_market_cache():
    get_quote.clear()
    get_quotes.clear()
    get_stock_data.clear()
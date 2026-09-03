import pandas as pd
import streamlit as st

from src.config import SETTINGS
from .provider import get_provider


@st.cache_data(
    ttl=SETTINGS.quote_cache_seconds,
    max_entries=5000,
    show_spinner=False,
    refresh_mode="background",
)
def get_quote(ticker: str) -> dict:

    return get_provider().get_quote(
        ticker.upper().strip()
    )


@st.cache_data(
    ttl=SETTINGS.quote_cache_seconds,
    max_entries=500,
    show_spinner=False,
    refresh_mode="background",
)
def get_quotes(
    tickers: tuple[str, ...],
) -> dict:

    return get_provider().get_quotes(
        tickers
    )


@st.cache_data(
    ttl=SETTINGS.history_cache_seconds,
    max_entries=1000,
    show_spinner=False,
    refresh_mode="background",
)
def get_stock_data(
    ticker: str,
    period: str = "5y",
    interval: str = "1d",
) -> pd.DataFrame:

    return get_provider().get_history(
        ticker.upper().strip(),
        period,
        interval,
    )


def clear_market_cache():

    get_quote.clear()

    get_quotes.clear()

    get_stock_data.clear()
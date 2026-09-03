import streamlit as st

from src.config import SETTINGS
from .providers.yahoo import YahooProvider


@st.cache_resource(
    show_spinner=False
)
def get_provider():

    if SETTINGS.market_provider == "yahoo":
        return YahooProvider()

    return YahooProvider()
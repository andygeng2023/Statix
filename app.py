import streamlit as st

from src.config import APP_NAME
from src.auth import render_auth_gate

st.set_page_config(
    page_title=APP_NAME,
    page_icon="S",
    layout="wide",
    initial_sidebar_state="collapsed",
)

render_auth_gate()

pg = st.navigation(
    [
        st.Page("pages/home.py", title="Home"),
        st.Page("pages/stocks.py", title="Stocks"),
        st.Page("pages/stock.py", title="Stock"),
        st.Page("pages/scanner.py", title="Scanner"),
        st.Page("pages/watchlist.py", title="Watchlist"),
    ]
)

pg.run()
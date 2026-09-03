import streamlit as st

from src.auth import render_auth_gate
from src.storage.database import init_db


st.set_page_config(
    page_title="Statix",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

if not render_auth_gate():
    st.stop()


pages = {
    "Statix": [
        st.Page("pages/home.py", title="Home"),
        st.Page("pages/search.py", title="Search"),
        st.Page("pages/stock.py", title="Stock"),
        st.Page("pages/prediction.py", title="Prediction"),
        st.Page("pages/scanner.py", title="Scanner"),
        st.Page("pages/watchlist.py", title="Watchlist"),
        st.Page("pages/settings.py", title="Settings"),
    ]
}

pg = st.navigation(pages)

pg.run()
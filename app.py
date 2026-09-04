from __future__ import annotations

import streamlit as st

from src.auth import ensure_authenticated, current_user
from src.config import APP_NAME
from src.storage.database import get_settings
from src.ui.components import inject_theme_css


st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_theme_css()

if not ensure_authenticated():
    st.stop()

settings = get_settings()
lang = st.session_state.get(
    "language_preference",
    settings.get("language", "en"),
)
st.session_state.setdefault(
    "provider_preference",
    settings.get("provider", "auto"),
)

# URL-driven navigation is what makes a whole card clickable while keeping
# the tab-like navigation appearance.
params = st.query_params
url_page = params.get("page")
url_ticker = params.get("ticker")

valid_pages = {"home", "stocks", "discover", "settings"}

if url_page in valid_pages:
    st.session_state["page"] = url_page
elif "page" not in st.session_state:
    st.session_state["page"] = "home"

if url_ticker:
    st.session_state["selected_ticker"] = str(url_ticker).upper()

page = st.session_state.get("page", "home")

with st.sidebar:
    st.markdown('<div class="brand">Statix</div>', unsafe_allow_html=True)
    user = current_user()
    st.caption((user or {}).get("email") or "Local user")
    st.caption(
        "Model outputs are research signals, not guarantees or financial advice."
    )

# Four top-level areas. These are buttons styled like native sliding tabs;
# unlike st.tabs(), they can be changed by a card click.
nav = st.columns(4)
labels = {
    "home": "Home",
    "stocks": "Stocks",
    "discover": "Discover",
    "settings": "Settings",
}

for col, key in zip(nav, labels):
    with col:
        if st.button(
            labels[key],
            key=f"nav_{key}",
            use_container_width=True,
        ):
            st.session_state["page"] = key
            st.query_params.clear()
            st.rerun()

        if page == key:
            st.markdown('<div class="statix-active-nav"></div>', unsafe_allow_html=True)

st.markdown('<div class="statix-nav-spacer"></div>', unsafe_allow_html=True)

if page == "home":
    exec(open("src/ui/home_tab.py").read(), globals())
elif page == "stocks":
    exec(open("src/ui/stocks_tab.py").read(), globals())
elif page == "discover":
    exec(open("src/ui/discover_tab.py").read(), globals())
elif page == "settings":
    exec(open("src/ui/settings_tab.py").read(), globals())

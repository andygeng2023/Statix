from __future__ import annotations

import streamlit as st

from src.auth import ensure_authenticated, current_user
from src.config import APP_NAME
from src.storage.database import get_settings
from src.ui.components import bottom_nav_html, inject_theme_css


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


# ---------------------------------------------------------
# Navigation state
# ---------------------------------------------------------

params = st.query_params

page = params.get("page", "home")
ticker = params.get("ticker")

valid_pages = {
    "home",
    "stocks",
    "discover",
    "settings",
}

if page not in valid_pages:
    page = "home"

st.session_state["page"] = page

if ticker:
    st.session_state["selected_ticker"] = str(ticker).upper()


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div class="brand">Statix</div>',
        unsafe_allow_html=True,
    )

    user = current_user()

    st.caption(
        (user or {}).get("email") or "Local user"
    )

    st.caption(
        "Model outputs are research signals, not guarantees or financial advice."
    )


# ---------------------------------------------------------
# Bottom navigation
# ---------------------------------------------------------

labels = {
    "home": "Home",
    "stocks": "Stocks",
    "discover": "Discover",
    "settings": "Settings",
}

st.html(
    bottom_nav_html(page, labels),
    unsafe_allow_javascript=True,
)


# ---------------------------------------------------------
# Pages
# ---------------------------------------------------------

if page == "home":
    exec(
        open("src/ui/home_tab.py", encoding="utf-8").read(),
        globals(),
    )

elif page == "stocks":
    exec(
        open("src/ui/stocks_tab.py", encoding="utf-8").read(),
        globals(),
    )

elif page == "discover":
    exec(
        open("src/ui/discover_tab.py", encoding="utf-8").read(),
        globals(),
    )

elif page == "settings":
    exec(
        open("src/ui/settings_tab.py", encoding="utf-8").read(),
        globals(),
    )
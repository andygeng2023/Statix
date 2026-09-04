from __future__ import annotations

import streamlit as st

from src.auth import ensure_authenticated, current_user
from src.config import APP_NAME
from src.storage.database import get_settings
from src.ui.components import bottom_nav, inject_theme_css


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

# -------------------------------------------------------------------
# Internal app navigation
#
# IMPORTANT:
# We intentionally do NOT use browser URLs for navigation.
# The whole app remains one Streamlit page/session.
# -------------------------------------------------------------------

st.session_state.setdefault("page", "home")
st.session_state.setdefault("selected_ticker", None)

page = st.session_state["page"]


def go_to(page_name: str):
    st.session_state["page"] = page_name


with st.sidebar:
    st.markdown('<div class="brand">Statix</div>', unsafe_allow_html=True)

    user = current_user()

    st.caption(
        (user or {}).get("email")
        or "Local user"
    )

    st.caption(
        "Model outputs are research signals, not guarantees or financial advice."
    )


# -------------------------------------------------------------------
# Main content
# -------------------------------------------------------------------

if page == "home":
    exec(open("src/ui/home_tab.py").read(), globals())

elif page == "stocks":
    exec(open("src/ui/stocks_tab.py").read(), globals())

elif page == "discover":
    exec(open("src/ui/discover_tab.py").read(), globals())

elif page == "settings":
    exec(open("src/ui/settings_tab.py").read(), globals())


# -------------------------------------------------------------------
# Fixed application navigation
#
# This is rendered AFTER the page so it stays visually at the bottom.
# It uses native Streamlit buttons, so navigation is guaranteed to
# trigger a Streamlit rerun rather than browser navigation.
# -------------------------------------------------------------------

bottom_nav(page)
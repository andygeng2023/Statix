from __future__ import annotations

import streamlit as st

from src.auth import ensure_authenticated, current_user
from src.config import APP_NAME
from src.storage.database import get_settings
from src.ui.components import bottom_navigation, inject_theme_css, t


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


params = st.query_params

url_page = params.get("page")
url_ticker = params.get("ticker")

valid_pages = {
    "home",
    "stocks",
    "discover",
    "settings",
}


if url_page in valid_pages:
    st.session_state["page"] = url_page
    if not url_ticker:
        st.session_state.pop("selected_ticker", None)

elif "page" not in st.session_state:
    st.session_state["page"] = "home"


if url_ticker:
    st.session_state["selected_ticker"] = str(
        url_ticker
    ).upper()


page = st.session_state.get("page", "home")


with st.sidebar:
    st.markdown(
        '<div class="brand">Statix</div>',
        unsafe_allow_html=True,
    )

    user = current_user()

    st.caption(
        (user or {}).get("email")
        or "Local user"
    )

    st.caption(
        "Model outputs are research signals, not guarantees or financial advice."
    )


labels = {
    "home": t("home", lang),
    "stocks": t("stocks", lang),
    "discover": t("discover", lang),
    "settings": t("settings", lang),
}


@st.fragment(run_every="30s")
def render_page():
    if page == "home":
        exec(open("src/ui/home_tab.py").read(), globals())
    elif page == "stocks":
        exec(open("src/ui/stocks_tab.py").read(), globals())
    elif page == "discover":
        exec(open("src/ui/discover_tab.py").read(), globals())
    elif page == "settings":
        exec(open("src/ui/settings_tab.py").read(), globals())


render_page()


# Native Streamlit navigation.
bottom_navigation(page, labels)
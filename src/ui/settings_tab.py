import streamlit as st

from src.config import LANGUAGES
from src.storage.database import get_settings, save_settings
from src.data.providers import PROVIDERS


settings = get_settings()

language_codes = list(LANGUAGES.values())
language_names = list(LANGUAGES.keys())

current_language = settings.get("language", "en")

if current_language not in language_codes:
    current_language = "en"

current_language_index = language_codes.index(current_language)

st.subheader("Settings")

# ---------------------------------------------------------
# Language
# ---------------------------------------------------------

selected_language_name = st.selectbox(
    "Language",
    language_names,
    index=current_language_index,
)

selected_language = LANGUAGES[selected_language_name]

# ---------------------------------------------------------
# Provider
# ---------------------------------------------------------

current_provider = settings.get("provider", "auto")

if current_provider not in PROVIDERS:
    current_provider = "auto"

provider_index = PROVIDERS.index(current_provider)

selected_provider = st.selectbox(
    "Market-data provider",
    PROVIDERS,
    index=provider_index,
    format_func=lambda value: {
        "auto": "Automatic fallback",
        "quantdash": "QuantDash",
        "akshare": "AKShare",
        "tushare": "TuShare",
        "yfinance": "Yahoo Finance",
    }.get(value, value),
)

st.caption(
    "Automatic order: QuantDash → AKShare → TuShare → yfinance"
)

# ---------------------------------------------------------
# Identity
# ---------------------------------------------------------

st.subheader("Identity")

user = getattr(st, "user", None)

if user is not None and getattr(user, "is_logged_in", False):
    email = getattr(user, "email", None)
    name = getattr(user, "name", None)

    if name:
        st.write(name)

    if email:
        st.caption(email)

    if st.button("Sign out"):
        st.logout()
else:
    st.caption("Not signed in.")

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

if st.button("Save settings", type="primary"):
    save_settings(
        selected_language,
        selected_provider,
    )

    st.session_state["language_preference"] = selected_language
    st.session_state["provider_preference"] = selected_provider

    st.success("Settings saved.")
    st.rerun()
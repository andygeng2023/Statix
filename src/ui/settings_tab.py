import streamlit as st

from src.config import LANGUAGES, TEXT
from src.storage.database import get_settings, save_settings
from src.data.providers import PROVIDERS

settings = get_settings()
lang = st.session_state.get("language_preference", settings.get("language", "en"))

st.title(TEXT.get(lang, TEXT["en"]).get("settings", "Settings"))

language_names = list(LANGUAGES.keys())
language_codes = list(LANGUAGES.values())
current_index = language_codes.index(lang) if lang in language_codes else 0

selected_name = st.selectbox(
    "Language",
    language_names,
    index=current_index,
)

selected_language = LANGUAGES[selected_name]

if selected_language != lang:
    save_settings(selected_language, settings.get("provider", "auto"))
    st.session_state["language_preference"] = selected_language
    st.rerun()

current_provider = st.session_state.get(
    "provider_preference",
    settings.get("provider", "auto"),
)
if current_provider not in PROVIDERS:
    current_provider = "auto"

provider_labels = {
    "auto": "Automatic fallback",
    "quantdash": "QuantDash",
    "akshare": "AKShare",
    "yfinance": "Yahoo Finance",
}

selected_provider = st.selectbox(
    "Market-data provider",
    PROVIDERS,
    index=PROVIDERS.index(current_provider),
    format_func=lambda x: provider_labels.get(x, x),
)

if selected_provider != current_provider:
    save_settings(selected_language, selected_provider)
    st.session_state["provider_preference"] = selected_provider
    st.rerun()

st.caption("Automatic order: QuantDash → AKShare → yfinance")

st.subheader(TEXT.get(lang, TEXT["en"]).get("identity", "Identity"))
user = getattr(st, "user", None)
if user is not None and getattr(user, "is_logged_in", False):
    if getattr(user, "name", None):
        st.write(user.name)
    if getattr(user, "email", None):
        st.caption(user.email)
    if st.button("Sign out"):
        st.logout()
else:
    st.caption("Not signed in.")

st.subheader("Model")
st.caption("Train the model in Codespaces, commit the generated artifact, then redeploy Streamlit Cloud.")

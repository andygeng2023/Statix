import streamlit as st
from src.config import LANGUAGES
from src.storage.database import get_settings,save_settings
from src.data.providers import PROVIDERS
from src.ui.components import t

s= get_settings()
lang_name=st.selectbox(t("language",s["language"]),list(LANGUAGES.keys()),index=list(LANGUAGES.values()).index(s["language"]))
new_lang=LANGUAGES[lang_name]
providers = [
    "auto",
    "quantdash",
    "akshare",
    "tushare",
    "yfinance",
]

labels = {
    "auto": "Automatic fallback",
    "quantdash": "QuantDash",
    "akshare": "AKShare",
    "tushare": "TuShare",
    "yfinance": "Yahoo Finance",
}

provider = st.selectbox(
    t("provider"),
    providers,
    format_func=lambda x: labels[x],
    index=providers.index(
        settings.get("provider", "auto")
    ),
)
st.subheader(t("identity",new_lang)); u=st.user if getattr(st.user,"is_logged_in",False) else None
st.caption(getattr(u,"email",None) or "Local development user")
st.subheader(t("data_source",new_lang)); st.write({"auto":"QuantDash → AKShare → TuShare → yfinance"}.get(provider,provider))
if st.button(t("save",new_lang),type="primary"):
 save_settings(
    language=language,
    provider=provider,
)

st.session_state["language_preference"] = language
st.session_state["provider_preference"] = provider
st.rerun()
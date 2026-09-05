import streamlit as st

from src.config import LANGUAGES
from src.data.providers import PROVIDERS
from src.storage.database import (
    get_settings,
    save_settings,
)
from src.ui.components import t


settings = get_settings()

lang = st.session_state.get(
    "language_preference",
    settings.get(
        "language",
        "en",
    ),
)


st.markdown(
    f"# {t('settings', lang)}"
)

st.caption(
    "Configure language, market data and account settings."
)


# ============================================================
# APPEARANCE / LANGUAGE
# ============================================================

st.subheader(
    "Language"
)

language_codes = list(
    LANGUAGES.values()
)

language_names = list(
    LANGUAGES.keys()
)

current_language = settings.get(
    "language",
    "en",
)

if current_language not in language_codes:
    current_language = "en"


selected_language_name = st.selectbox(
    t("language", lang),
    language_names,
    index=language_codes.index(
        current_language
    ),
)

selected_language = LANGUAGES[
    selected_language_name
]


# ============================================================
# DATA
# ============================================================

st.subheader(
    "Data"
)

current_provider = settings.get(
    "provider",
    "auto",
)

if current_provider not in PROVIDERS:
    current_provider = "auto"


provider_names = {
    "auto": "Automatic",
    "quantdash": "QuantDash",
    "akshare": "AKShare",
    "yfinance": "Yahoo Finance",
}


selected_provider = st.selectbox(
    t("data_source", lang),
    PROVIDERS,
    index=PROVIDERS.index(
        current_provider
    ),
    format_func=lambda value:
        provider_names.get(
            value,
            value,
        ),
)


st.caption(
    "Automatic uses QuantDash → AKShare → Yahoo Finance."
)


# ============================================================
# IDENTITY
# ============================================================

st.subheader(
    t("identity", lang)
)

user = getattr(
    st,
    "user",
    None,
)


if (
    user is not None
    and getattr(
        user,
        "is_logged_in",
        False,
    )
):

    if getattr(
        user,
        "name",
        None,
    ):

        st.write(
            user.name
        )

    if getattr(
        user,
        "email",
        None,
    ):

        st.caption(
            user.email
        )

    if st.button(
        t("sign_out", lang),
        key="settings_sign_out",
    ):

        st.logout()

else:

    st.caption(
        t(
            "not_signed_in",
            lang,
        )
    )


# ============================================================
# SAVE
# ============================================================

st.divider()

if st.button(
    t("save", lang),
    type="primary",
    key="settings_save",
):

    save_settings(
        selected_language,
        selected_provider,
    )

    st.session_state[
        "language_preference"
    ] = selected_language

    st.session_state[
        "provider_preference"
    ] = selected_provider

    st.success(
        t(
            "settings_saved",
            lang,
        )
    )

    st.rerun()
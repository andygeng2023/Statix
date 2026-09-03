import hashlib

import streamlit as st

from src.config import APP_NAME


def auth_configured() -> bool:
    try:
        return bool(st.secrets.get("auth"))
    except Exception:
        return False


def require_auth() -> bool:
    try:
        return bool(st.secrets.get("require_auth", False))
    except Exception:
        return False


def is_logged_in() -> bool:
    try:
        return bool(st.user.is_logged_in)
    except Exception:
        return False


def current_user_id() -> str:
    if not is_logged_in():
        return "local-anonymous"

    try:
        issuer = str(st.user.get("iss", ""))
        subject = str(
            st.user.get("sub")
            or st.user.get("email")
            or st.user.get("name")
            or ""
        )

        return hashlib.sha256(
            f"{issuer}:{subject}".encode()
        ).hexdigest()
    except Exception:
        return "local-anonymous"


def current_user_name() -> str:
    if not is_logged_in():
        return "Local User"

    try:
        return str(
            st.user.get("name")
            or st.user.get("email")
            or "User"
        )
    except Exception:
        return "User"


def render_auth_gate():
    if not require_auth():
        return

    if is_logged_in():
        return

    st.title(APP_NAME)
    st.write("Sign in to continue.")

    try:
        st.login()
    except Exception:
        st.error(
            "Authentication is enabled, but the OIDC configuration "
            "is incomplete."
        )

    st.stop()
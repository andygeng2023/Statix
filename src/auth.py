import hashlib

import streamlit as st

from src.config import SETTINGS


def auth_configured() -> bool:
    return SETTINGS.require_auth


def is_logged_in() -> bool:
    try:
        return bool(st.user.is_logged_in)
    except Exception:
        return False


def current_user_id() -> str:
    if not auth_configured():
        return "local-anonymous"

    try:
        issuer = str(st.user.get("iss", ""))
        subject = str(
            st.user.get(
                "sub",
                st.user.get("email", ""),
            )
        )

        raw = f"{issuer}|{subject}"

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:40]

    except Exception:
        return "unknown-user"


def current_user_name() -> str:
    if not auth_configured():
        return "Local user"

    try:
        return (
            st.user.get("name")
            or st.user.get("email")
            or "User"
        )
    except Exception:
        return "User"


def render_auth_gate() -> bool:
    if not auth_configured():
        return True

    if is_logged_in():

        with st.sidebar:
            st.caption(
                f"Signed in as {current_user_name()}"
            )

            st.button(
                "Sign out",
                use_container_width=True,
                on_click=st.logout,
            )

        return True

    st.title("Statix")

    st.subheader(
        "Market prediction research platform"
    )

    st.write(
        "Sign in to keep your watchlist, "
        "view history, and prediction history "
        "separate from other users."
    )

    st.button(
        "Sign in",
        type="primary",
        on_click=st.login,
    )

    return False
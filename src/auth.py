from __future__ import annotations

import hashlib
import os

import streamlit as st


def auth_configured() -> bool:
    try:
        return bool(st.secrets.get("auth"))
    except Exception:
        return False


def require_auth() -> bool:
    try:
        value = st.secrets.get(
            "require_auth",
            False,
        )
    except Exception:
        value = os.getenv(
            "STATIX_REQUIRE_AUTH",
            "false",
        )

    return str(value).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def is_logged_in() -> bool:
    try:
        return bool(
            getattr(
                st.user,
                "is_logged_in",
                False,
            )
        )
    except Exception:
        return False


def current_user_id() -> str:
    """
    Returns a stable non-PII identifier.

    The database uses this to separate each user's
    watchlist and prediction history.
    """

    if is_logged_in():

        try:
            user = st.user.to_dict()
        except Exception:
            user = {}

        subject = str(
            user.get("sub")
            or user.get("email")
            or ""
        )

        issuer = str(
            user.get("iss")
            or ""
        )

        if subject:
            raw = (
                f"{issuer}:{subject}"
                .encode("utf-8")
            )

            return hashlib.sha256(
                raw
            ).hexdigest()

    return "local-anonymous"


def current_user_name() -> str:
    if not is_logged_in():
        return "Local user"

    try:
        user = st.user.to_dict()
    except Exception:
        return "User"

    return str(
        user.get("name")
        or user.get("email")
        or "User"
    )


def render_auth_gate() -> None:
    if not require_auth():
        return

    if not auth_configured():
        st.error(
            "Authentication is required, but the "
            "[auth] section is missing from Streamlit secrets."
        )
        st.stop()

    if not is_logged_in():

        st.title("Statix")

        st.subheader(
            "Sign in to continue"
        )

        st.write(
            "Sign-in keeps your watchlist, viewed stocks, "
            "and prediction history separate from other users."
        )

        st.button(
            "Continue with Google",
            on_click=st.login,
            use_container_width=True,
        )

        st.stop()
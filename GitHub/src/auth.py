from __future__ import annotations
import hashlib
import streamlit as st
from src.config import require_auth, secret

def ensure_authenticated():
    if not require_auth():
        return True
    if getattr(st.user, "is_logged_in", False):
        return True
    st.title("Statix")
    st.write("Sign in to use your Statix account.")
    if secret("auth", None):
        st.login()
    else:
        st.error("Authentication is enabled, but the OIDC [auth] configuration is missing.")
    return False

def current_user():
    if not require_auth():
        return {"id":"local-anonymous","email":None,"name":"Local user"}
    u=st.user
    if not getattr(u,"is_logged_in",False): return None
    issuer=str(getattr(u,"iss","") or "")
    subject=str(getattr(u,"sub","") or getattr(u,"email","") or "")
    stable=hashlib.sha256((issuer+"|"+subject).encode()).hexdigest()
    return {"id":stable,"email":getattr(u,"email",None),"name":getattr(u,"name",None)}

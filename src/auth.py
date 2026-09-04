from __future__ import annotations
import hashlib
import streamlit as st
from src.config import require_auth

def ensure_authenticated():
    if not require_auth(): return True
    if getattr(st.user,"is_logged_in",False): return True
    st.title("Statix")
    st.write("Sign in to continue.")
    try: st.login()
    except Exception as exc: st.error(f"Authentication is not configured: {exc}")
    return False

def current_user():
    if not require_auth(): return {"id":"local-anonymous","email":None,"name":"Local user"}
    if not getattr(st.user,"is_logged_in",False): return None
    issuer=str(getattr(st.user,"iss","") or ""); subject=str(getattr(st.user,"sub","") or getattr(st.user,"email","") or "")
    return {"id":hashlib.sha256((issuer+"|"+subject).encode()).hexdigest(),"email":getattr(st.user,"email",None),"name":getattr(st.user,"name",None)}

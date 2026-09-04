from __future__ import annotations

import streamlit as st

from src.auth import ensure_authenticated, current_user
from src.config import APP_NAME, TEXT
from src.storage.database import get_settings

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container{max-width:1440px;padding-top:2rem;padding-bottom:4rem}
[data-testid="stHorizontalBlock"]{gap:1rem}
div[data-testid="stMetric"]{background:rgba(79,70,229,.06);border:1px solid rgba(79,70,229,.14);border-radius:14px;padding:.65rem}
.stButton>button{border-radius:10px}
.brand{font-size:1.8rem;font-weight:850;letter-spacing:-.05em;color:#4f46e5}
</style>
""", unsafe_allow_html=True)

if not ensure_authenticated():
    st.stop()

settings = get_settings()
lang = st.session_state.get("language_preference", settings.get("language", "en"))
st.session_state.setdefault("provider_preference", settings.get("provider", "auto"))

user = current_user()
with st.sidebar:
    st.markdown('<div class="brand">Statix</div>', unsafe_allow_html=True)
    st.caption((user or {}).get("email") or "Local user")
    st.caption("Model outputs are research signals, not guarantees or financial advice.")

# A segmented control is used instead of st.tabs so Open buttons can
# reliably switch to Stocks and only the active page performs expensive work.
labels = [
    TEXT.get(lang, TEXT["en"]).get("home", "Home"),
    TEXT.get(lang, TEXT["en"]).get("stocks", "Stocks"),
    TEXT.get(lang, TEXT["en"]).get("discover", "Discover"),
    TEXT.get(lang, TEXT["en"]).get("settings", "Settings"),
]
keys = ["home", "stocks", "discover", "settings"]

active = st.session_state.get("active_tab", "home")
if active not in keys:
    active = "home"

active = st.radio(
    "Navigation",
    keys,
    index=keys.index(active),
    format_func=lambda key: labels[keys.index(key)],
    horizontal=True,
    label_visibility="collapsed",
)
st.session_state["active_tab"] = active

if active == "home":
    exec(open("src/ui/home_tab.py", encoding="utf-8").read(), globals())
elif active == "stocks":
    exec(open("src/ui/stocks_tab.py", encoding="utf-8").read(), globals())
elif active == "discover":
    exec(open("src/ui/discover_tab.py", encoding="utf-8").read(), globals())
else:
    exec(open("src/ui/settings_tab.py", encoding="utf-8").read(), globals())

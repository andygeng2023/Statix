from __future__ import annotations
import streamlit as st
from src.auth import ensure_authenticated,current_user
from src.config import APP_NAME,LANGUAGES
from src.storage.database import database_status,get_settings,save_settings,get_watchlist

st.set_page_config(page_title=APP_NAME,page_icon="📈",layout="wide",initial_sidebar_state="collapsed")
st.markdown("""<style>.block-container{max-width:1440px;padding-top:3rem;padding-bottom:4rem}.statix-card{border:1px solid rgba(128,128,128,.16);border-radius:16px;padding:1rem}.muted{opacity:.65}.brand{font-size:1.7rem;font-weight:850;letter-spacing:-.05em}</style>""",unsafe_allow_html=True)
if not ensure_authenticated():st.stop()
settings=get_settings(); lang=st.session_state.get("language_preference", settings["language"]); st.session_state.setdefault("provider_preference", settings["provider"])
with st.sidebar:
 st.markdown('<div class="brand">Statix</div>',unsafe_allow_html=True); u=current_user(); st.caption((u or {}).get("email") or "Local user"); st.caption("Model outputs are research signals, not guarantees or financial advice.")

# The four requested top-level areas are tabs; stock detail is selected inside Stocks.
tabs=st.tabs(["Home","Stocks","Discover","Settings"])
with tabs[0]: exec(open("src/ui/home_tab.py").read(),globals())
with tabs[1]: exec(open("src/ui/stocks_tab.py").read(),globals())
with tabs[2]: exec(open("src/ui/discover_tab.py").read(),globals())
with tabs[3]: exec(open("src/ui/settings_tab.py").read(),globals())

import streamlit as st
from src.auth import ensure_authenticated, current_user
from src.config import APP_NAME

st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container{max-width:1400px;padding-top:1.25rem;padding-bottom:3rem}
[data-testid="stSidebar"]{border-right:1px solid rgba(128,128,128,.16)}
.statix-brand{font-size:1.65rem;font-weight:800;letter-spacing:-.04em}
.statix-muted{color:#888;font-size:.82rem}
.page-title{font-size:2rem;font-weight:800;letter-spacing:-.04em;margin-bottom:.15rem}
.page-subtitle{color:#888;margin-bottom:1.2rem}
.card{border:1px solid rgba(128,128,128,.18);border-radius:14px;padding:1rem;background:rgba(128,128,128,.035)}
.small{font-size:.8rem;color:#888}
</style>
""", unsafe_allow_html=True)

if not ensure_authenticated():
    st.stop()

with st.sidebar:
    st.markdown('<div class="statix-brand">Statix</div>', unsafe_allow_html=True)
    st.markdown('<div class="statix-muted">Market intelligence</div>', unsafe_allow_html=True)
    st.divider()
    user=current_user()
    if user:
        st.caption(user.get("email") or "Signed in")
        if st.button("Sign out", use_container_width=True):
            st.logout()
    st.caption("Predictions are model outputs, not guarantees or financial advice.")

pages={"Statix":[
    st.Page("pages/home.py", title="Home"),
    st.Page("pages/search.py", title="Search"),
    st.Page("pages/stock.py", title="Stock"),
    st.Page("pages/scanner.py", title="Scanner"),
    st.Page("pages/watchlist.py", title="Watchlist"),
]}
st.navigation(pages).run()

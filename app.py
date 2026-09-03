import streamlit as st
from src.auth import ensure_authenticated, current_user
from src.config import APP_NAME

st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container{max-width:1440px;padding-top:3rem;padding-bottom:4rem}
[data-testid="stSidebar"]{border-right:1px solid rgba(128,128,128,.16)}
.statix-brand{font-size:1.65rem;font-weight:850;letter-spacing:-.05em;margin-top:.25rem}
.statix-muted{color:#8a8f98;font-size:.82rem}
.page-title{font-size:2.15rem;font-weight:850;letter-spacing:-.055em;line-height:1.05;margin:0 0 .35rem}
.page-subtitle{color:#7d838c;margin:0 0 1.4rem;font-size:.98rem}
.statix-card{border:1px solid rgba(128,128,128,.16);border-radius:16px;padding:1rem 1.05rem;background:rgba(128,128,128,.025)}
.statix-kicker{text-transform:uppercase;letter-spacing:.09em;font-size:.7rem;font-weight:750;color:#858b94;margin-bottom:.35rem}
.statix-value{font-size:1.35rem;font-weight:800;letter-spacing:-.025em}
.statix-note{font-size:.78rem;color:#858b94}
.statix-positive{color:#138a55}.statix-negative{color:#c43d4b}
div[data-testid="stMetric"]{padding:.2rem 0}
button[kind="primary"]{font-weight:700}
@media (max-width: 800px){.block-container{padding-top:2rem}.page-title{font-size:1.8rem}}
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
    st.divider()
    st.caption("Predictions are model outputs, not guarantees or financial advice.")

pages={"Statix":[
    st.Page("pages/home.py", title="Home"),
    st.Page("pages/search.py", title="Search"),
    st.Page("pages/stock.py", title="Stock"),
    st.Page("pages/scanner.py", title="Scanner"),
    st.Page("pages/watchlist.py", title="Watchlist"),
]}
st.navigation(pages).run()

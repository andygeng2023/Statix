import streamlit as st

from src.storage.database import init_db


st.set_page_config(
    page_title="Statix",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()


st.markdown(
    """
    <style>
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}

    .block-container {
        max-width: 1500px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,.15);
    }

    .statix-logo {
        font-size: 30px;
        font-weight: 850;
        letter-spacing: -1.5px;
    }

    .muted {
        color: rgba(128,128,128,.85);
        font-size: 13px;
    }

    .hero {
        padding: 28px;
        border-radius: 20px;
        border: 1px solid rgba(128,128,128,.16);
        background: linear-gradient(
            135deg,
            rgba(128,128,128,.08),
            rgba(128,128,128,.025)
        );
        margin-bottom: 20px;
    }

    .hero-title {
        font-size: 42px;
        font-weight: 850;
        letter-spacing: -2px;
        margin-bottom: 5px;
    }

    .hero-subtitle {
        font-size: 16px;
        color: rgba(128,128,128,.9);
    }

    .section-title {
        font-size: 23px;
        font-weight: 750;
        letter-spacing: -.5px;
    }

    .stock-card {
        border: 1px solid rgba(128,128,128,.16);
        border-radius: 16px;
        padding: 17px;
        background: rgba(128,128,128,.025);
        min-height: 165px;
    }

    .signal-card {
        border: 1px solid rgba(128,128,128,.18);
        border-radius: 18px;
        padding: 22px;
        background: rgba(128,128,128,.035);
    }

    .metric-card {
        border: 1px solid rgba(128,128,128,.15);
        border-radius: 13px;
        padding: 13px;
        background: rgba(128,128,128,.025);
    }

    .metric-label {
        color: rgba(128,128,128,.8);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: .6px;
    }

    .metric-value {
        font-size: 19px;
        font-weight: 750;
        margin-top: 3px;
    }

    .ticker-title {
        font-size: 34px;
        font-weight: 850;
        letter-spacing: -1.5px;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.13);
        border-radius: 12px;
        padding: 10px;
        background: rgba(128,128,128,.02);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


pages = {
    "Statix": [
        st.Page("pages/home.py", title="Home", icon="🏠"),
        st.Page("pages/search.py", title="Search", icon="🔎"),
        st.Page("pages/watchlist.py", title="Watchlist", icon="⭐"),
        st.Page("pages/prediction.py", title="Prediction", icon="📊"),
    ]
}


pg = st.navigation(pages)


with st.sidebar:

    st.markdown(
        '<div class="statix-logo">Statix</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Market intelligence dashboard"
    )

    st.divider()

    st.markdown("**V6.1 Ensemble**")
    st.caption("Technical + market-relative features")

    st.divider()

    st.caption(
        "Market data may be delayed. Model outputs are estimates, not financial advice."
    )


pg.run()
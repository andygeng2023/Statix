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
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        .block-container {
            max-width: 1450px;
            padding-top: 1.2rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128,128,128,.18);
        }

        .statix-logo {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -1px;
        }

        .statix-muted {
            color: rgba(128,128,128,.9);
            font-size: 13px;
        }

        .metric-card {
            border: 1px solid rgba(128,128,128,.18);
            border-radius: 14px;
            padding: 16px;
            background: rgba(128,128,128,.035);
        }

        .signal-card {
            border: 1px solid rgba(128,128,128,.20);
            border-radius: 18px;
            padding: 22px;
            background: rgba(128,128,128,.045);
        }

        .ticker-title {
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -1px;
        }

        .small-label {
            font-size: 12px;
            color: rgba(128,128,128,.85);
            text-transform: uppercase;
            letter-spacing: .5px;
        }

        .small-value {
            font-size: 18px;
            font-weight: 700;
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,.15);
            border-radius: 12px;
            padding: 12px;
            background: rgba(128,128,128,.025);
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
    st.markdown('<div class="statix-logo">Statix</div>', unsafe_allow_html=True)
    st.caption("Market intelligence dashboard")

    st.divider()

    st.caption("Model")
    st.code("V6 • Ensemble", language=None)

    st.caption("Data")
    st.code("Yahoo Finance", language=None)

    st.divider()

    st.caption(
        "Predictions are model outputs, not financial advice. "
        "Market data may be delayed."
    )

pg.run()
import streamlit as st

st.set_page_config(
    page_title="Statix",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1450px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,.18);
    }

    .statix-brand {
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin-bottom: 0;
    }

    .statix-subtitle {
        color: #888;
        font-size: .85rem;
        margin-top: -.25rem;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 750;
        margin-top: 1.4rem;
        margin-bottom: .7rem;
    }

    .small-muted {
        color: #888;
        font-size: .82rem;
    }

    div[data-testid="stMetric"] {
        padding: .35rem 0;
    }

    button[kind="secondary"] {
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        <div class="statix-brand">Statix</div>
        <div class="statix-subtitle">Market intelligence</div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.caption("Navigation")
    st.caption("Use Search to select a stock, then open its prediction page.")

pages = {
    "Statix": [
        st.Page("pages/home.py", title="Home", icon="🏠"),
        st.Page("pages/search.py", title="Search", icon="🔎"),
        st.Page("pages/watchlist.py", title="Watchlist", icon="⭐"),
        st.Page("pages/prediction.py", title="Prediction", icon="📊"),
    ]
}

pg = st.navigation(pages)
pg.run()
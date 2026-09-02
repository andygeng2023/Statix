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
        max-width: 1400px;
        padding-top: 2rem;
    }

    .statix-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0;
    }

    .statix-subtitle {
        color: #777;
        margin-top: 0;
        margin-bottom: 2rem;
    }

    .metric-card {
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid rgba(128,128,128,.2);
    }

    button {
        border-radius: 10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

pg = st.navigation(
    [
        st.Page("pages/home.py", title="Home", icon="⌂"),
        st.Page("pages/search.py", title="Search", icon="⌕"),
        st.Page("pages/watchlist.py", title="Watchlist", icon="★"),
        st.Page("pages/prediction.py", title="Prediction", icon="◈"),
    ]
)

pg.run() 
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
        padding-bottom: 4rem;
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

    [data-testid="stMetric"] {
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


pg = st.navigation(
    [
        st.Page(
            "pages/home.py",
            title="Home",
            icon="🏠",
        ),
        st.Page(
            "pages/search.py",
            title="Search",
            icon="🔎",
        ),
        st.Page(
            "pages/watchlist.py",
            title="Watchlist",
            icon="⭐",
        ),
        st.Page(
            "pages/prediction.py",
            title="Prediction",
            icon="📊",
        ),
    ]
)


pg.run()
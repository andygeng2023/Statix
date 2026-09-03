import streamlit as st

from src.auth import current_user_name, render_auth_gate


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
        padding-top: 1.4rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,.18);
    }

    .statix-brand {
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: -.04em;
    }

    .statix-subtitle {
        color: #888;
        font-size: .85rem;
        margin-top: -.5rem;
    }

    .section-title {
        font-size: 1.2rem;
        font-weight: 750;
        margin-top: 1.4rem;
        margin-bottom: .7rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

render_auth_gate()


with st.sidebar:
    st.markdown(
        '<div class="statix-brand">Statix</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="statix-subtitle">Market intelligence</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    st.caption(f"User: {current_user_name()}")

    if getattr(st.user, "is_logged_in", False):
        if st.button(
            "Log out",
            use_container_width=True,
        ):
            st.logout()


pages = {
    "Statix": [
        st.Page(
            "pages/home.py",
            title="Home",
        ),
        st.Page(
            "pages/search.py",
            title="Search",
        ),
        st.Page(
            "pages/watchlist.py",
            title="Watchlist",
        ),
        st.Page(
            "pages/stock.py",
            title="Stock",
        ),
        st.Page(
            "pages/prediction.py",
            title="Prediction",
        ),
    ]
}


pg = st.navigation(pages)
pg.run()
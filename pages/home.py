import streamlit as st

from src.data.market import get_quotes
from src.data.provider import get_provider
from src.storage.database import (
    get_recently_viewed,
    get_watchlist,
)
from src.ui.components import stock_card


st.title("Statix")

st.caption(
    "Market intelligence and prediction research"
)

provider = get_provider()

st.info(
    f"Market data: {provider.name}. "
    "Data freshness depends on the provider."
)


watchlist = get_watchlist()

recent = get_recently_viewed()


st.subheader("Market Pulse")

if watchlist:

    quotes = get_quotes(
        tuple(watchlist[:8])
    )

    columns = st.columns(
        min(
            4,
            len(watchlist[:4]),
        )
    )

    for column, ticker in zip(
        columns,
        watchlist[:4],
    ):

        with column:

            quote = quotes.get(
                ticker,
                {},
            )

            stock_card(
                ticker,
                quote,
            )

else:

    st.write(
        "Your watchlist is empty."
    )


st.divider()


left, right = st.columns(
    [1.4, 1]
)


with left:

    st.subheader(
        "Statix Scanner"
    )

    st.write(
        "Rank a broad market universe "
        "using the fast prediction and "
        "reliability pipeline."
    )

    if st.button(
        "Open Scanner",
        type="primary",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/scanner.py"
        )


with right:

    st.subheader(
        "Quick Analysis"
    )

    ticker = st.text_input(
        "Ticker",
        placeholder="AAPL",
    )

    if st.button(
        "Analyze",
        use_container_width=True,
    ):

        if ticker.strip():

            st.session_state[
                "selected_ticker"
            ] = ticker.upper().strip()

            st.switch_page(
                "pages/stock.py"
            )


if recent:

    st.divider()

    st.subheader(
        "Recently Viewed"
    )

    cols = st.columns(
        min(6, len(recent))
    )

    for column, ticker in zip(
        cols,
        recent,
    ):

        with column:

            if st.button(
                ticker,
                use_container_width=True,
            ):

                st.session_state[
                    "selected_ticker"
                ] = ticker

                st.switch_page(
                    "pages/stock.py"
                )
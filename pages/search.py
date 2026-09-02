import streamlit as st

from src.data.market import get_quote
from src.data.search import search_symbols
from src.storage.database import (
    add_to_watchlist,
    is_watched,
    remove_from_watchlist,
)


st.title("Search")

query = st.text_input(
    "Search stocks, ETFs, or symbols",
    placeholder="Apple, Tesla, NVDA...",
)

if query:

    with st.spinner("Searching..."):

        results = search_symbols(query)

    if not results:

        st.warning(
            "No matching symbols found."
        )

    for result in results:

        ticker = result["symbol"]

        quote = get_quote(ticker)

        col1, col2, col3, col4 = st.columns(
            [2.8, 2, 1.3, 1.3]
        )

        with col1:

            st.markdown(
                f"### {ticker}"
            )

            st.caption(
                f'{result["name"]} • '
                f'{result["exchange"]}'
            )

        with col2:

            price = quote.get("price")

            if price is not None:
                st.metric(
                    "Price",
                    f"${price:,.2f}",
                    (
                        f'{quote["change_pct"] * 100:+.2f}%'
                        if quote.get("change_pct")
                        is not None
                        else None
                    ),
                )

        with col3:

            watched = is_watched(ticker)

            if watched:

                if st.button(
                    "Remove",
                    key=f"remove_{ticker}",
                ):

                    remove_from_watchlist(
                        ticker
                    )

                    st.rerun()

            else:

                if st.button(
                    "Watch",
                    key=f"watch_{ticker}",
                ):

                    add_to_watchlist(
                        ticker
                    )

                    st.rerun()

        with col4:

            if st.button(
                "Analyze",
                key=f"analyze_{ticker}",
            ):

                st.session_state[
                    "selected_ticker"
                ] = ticker

                st.switch_page(
                    "pages/prediction.py"
                )

        st.divider()


st.subheader("Popular")

popular = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "TSLA",
    "SPY",
]

cols = st.columns(6)

for col, ticker in zip(
    cols,
    popular,
):

    with col:

        if st.button(
            ticker,
            use_container_width=True,
        ):

            st.session_state[
                "selected_ticker"
            ] = ticker

            st.switch_page(
                "pages/prediction.py"
            )
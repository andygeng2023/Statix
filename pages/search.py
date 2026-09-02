import streamlit as st

from src.data.search import search_stocks

from src.data.market import (
    get_stock_data,
    get_quote,
)

from src.storage.database import (
    add_to_watchlist,
    remove_from_watchlist,
    is_watched,
)


st.title("Search")

query = st.text_input(
    "Search by ticker or company name",
    placeholder="Apple, Microsoft, AAPL...",
)

if not query:
    st.caption(
        "Enter a ticker or company name to search."
    )
    st.stop()


with st.spinner("Searching..."):
    results = search_stocks(query)


if not results:
    st.warning("No matching stocks found.")
    st.stop()


for result in results:

    ticker = result["symbol"]

    with st.container(border=True):

        col1, col2, col3 = st.columns(
            [4, 2, 1]
        )

        with col1:
            st.subheader(
                f"{ticker} — {result['name']}"
            )

            st.caption(
                f"{result['exchange']} · "
                f"{result['type']}"
            )

        try:
            quote = get_quote(ticker)

            with col2:
                st.metric(
                    "Price",
                    f"${quote['price']:,.2f}",
                    f"{quote['change_pct'] * 100:+.2f}%",
                )

        except Exception:
            with col2:
                st.caption(
                    "Quote unavailable"
                )

        with col3:

            if is_watched(ticker):

                if st.button(
                    "Remove",
                    key=f"remove_{ticker}",
                ):
                    remove_from_watchlist(ticker)
                    st.rerun()

            else:

                if st.button(
                    "Add",
                    key=f"add_{ticker}",
                ):
                    add_to_watchlist(ticker)
                    st.rerun()

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
import streamlit as st

from src.data.search import search_stocks
from src.data.market import get_quote
from src.storage.database import (
    add_to_watchlist,
    remove_from_watchlist,
    is_watched,
)


st.title("Search")
st.caption("Find stocks, ETFs, and companies.")


query = st.text_input(
    "Search",
    placeholder="Try Apple, Microsoft, NVDA, Tesla...",
)


if query.strip():

    results = search_stocks(query)

    if not results:
        st.warning(
            "No matching stocks were found."
        )

    for result in results:

        ticker = result["symbol"]
        name = result["name"]
        exchange = result.get("exchange", "")

        quote = get_quote(ticker)

        with st.container(border=True):

            col1, col2, col3 = st.columns(
                [4, 2, 2]
            )

            with col1:

                st.subheader(
                    f"{ticker}"
                )

                st.caption(
                    f"{name} • {exchange}"
                )

                if quote["price"] is not None:
                    st.write(
                        f"${quote['price']:,.2f}"
                    )

            with col2:

                if quote["change_pct"] is not None:
                    st.metric(
                        "Today",
                        f"{quote['change_pct']:+.2f}%",
                    )

            with col3:

                if is_watched(ticker):

                    if st.button(
                        "Remove",
                        key=f"remove_search_{ticker}",
                        use_container_width=True,
                    ):
                        remove_from_watchlist(ticker)
                        st.rerun()

                else:

                    if st.button(
                        "Add",
                        key=f"add_search_{ticker}",
                        use_container_width=True,
                    ):
                        add_to_watchlist(ticker)
                        st.rerun()

                if st.button(
                    "Analyze",
                    key=f"analyze_search_{ticker}",
                    use_container_width=True,
                ):
                    st.session_state[
                        "selected_ticker"
                    ] = ticker

                    st.switch_page(
                        "pages/prediction.py"
                    )


st.divider()

st.header("Discover")

discover = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "SPY",
]

cols = st.columns(4)

for index, ticker in enumerate(discover):

    with cols[index % 4]:

        quote = get_quote(ticker)

        with st.container(border=True):

            st.subheader(ticker)

            if quote["price"] is not None:
                st.write(
                    f"${quote['price']:,.2f}"
                )

            if quote["change_pct"] is not None:
                st.caption(
                    f"{quote['change_pct']:+.2f}%"
                )

            if st.button(
                "Analyze",
                key=f"search_discover_{ticker}",
                use_container_width=True,
            ):
                st.session_state[
                    "selected_ticker"
                ] = ticker

                st.switch_page(
                    "pages/prediction.py"
                )
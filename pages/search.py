import streamlit as st

from src.data.market import (
    get_quote,
    get_stock_data,
)

from src.data.search import (
    search_stocks,
)

from src.storage.database import (
    add_to_watchlist,
    is_watched,
    remove_from_watchlist,
)


st.title("Search")

st.markdown(
    "Search by company name or ticker."
)


query = st.text_input(
    "Search",
    placeholder=(
        "Apple, Microsoft, AAPL..."
    ),
)


if query:

    with st.spinner(
        "Searching..."
    ):
        results = search_stocks(
            query
        )

    if not results:
        st.warning(
            "No matching stocks found."
        )

    else:

        st.subheader(
            "Search Results"
        )

        for result in results:

            ticker = result[
                "symbol"
            ]

            with st.container(
                border=True
            ):

                c1, c2, c3 = st.columns(
                    [4, 2, 1]
                )

                with c1:

                    st.subheader(
                        f"{ticker} — "
                        f"{result['name']}"
                    )

                    st.caption(
                        f"{result['exchange']} · "
                        f"{result['type']}"
                    )

                try:

                    quote = get_quote(
                        ticker
                    )

                    with c2:

                        st.metric(
                            "Price",
                            (
                                f"${quote['price']:,.2f}"
                            ),
                            (
                                f"{quote['change_pct'] * 100:+.2f}%"
                            ),
                        )

                except Exception:

                    with c2:
                        st.caption(
                            "Quote unavailable"
                        )

                with c3:

                    if is_watched(
                        ticker
                    ):

                        if st.button(
                            "Remove",
                            key=(
                                f"remove_{ticker}"
                            ),
                        ):
                            remove_from_watchlist(
                                ticker
                            )
                            st.rerun()

                    else:

                        if st.button(
                            "Add",
                            key=(
                                f"add_{ticker}"
                            ),
                        ):
                            add_to_watchlist(
                                ticker
                            )
                            st.rerun()

                if st.button(
                    "Analyze",
                    key=(
                        f"analyze_{ticker}"
                    ),
                ):

                    st.session_state[
                        "selected_ticker"
                    ] = ticker

                    st.switch_page(
                        "pages/prediction.py"
                    )


# -------------------------
# Discover
# -------------------------

st.divider()

st.subheader(
    "Discover"
)

st.caption(
    "Start with one of these commonly followed symbols."
)


discover = [
    (
        "AAPL",
        "Apple",
    ),
    (
        "MSFT",
        "Microsoft",
    ),
    (
        "NVDA",
        "NVIDIA",
    ),
    (
        "AMZN",
        "Amazon",
    ),
    (
        "GOOGL",
        "Alphabet",
    ),
    (
        "META",
        "Meta",
    ),
    (
        "TSLA",
        "Tesla",
    ),
    (
        "SPY",
        "S&P 500 ETF",
    ),
]


columns = st.columns(4)


for index, (
    ticker,
    name,
) in enumerate(discover):

    with columns[index % 4]:

        with st.container(
            border=True
        ):

            st.markdown(
                f"**{ticker}**"
            )

            st.caption(name)

            try:

                quote = get_quote(
                    ticker
                )

                st.metric(
                    "Price",
                    f"${quote['price']:,.2f}",
                    (
                        f"{quote['change_pct'] * 100:+.2f}%"
                    ),
                )

            except Exception:

                st.caption(
                    "Quote unavailable"
                )

            if st.button(
                "Analyze",
                key=(
                    f"search_discover_{ticker}"
                ),
                use_container_width=True,
            ):

                st.session_state[
                    "selected_ticker"
                ] = ticker

                st.switch_page(
                    "pages/prediction.py"
                )
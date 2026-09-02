import streamlit as st

from src.data.market import get_quote
from src.data.search import search_symbols
from src.storage.database import (
    add_to_watchlist,
    is_watched,
    remove_from_watchlist,
)


st.title("Search")

st.caption(
    "Find stocks and ETFs, then open the full Statix analysis."
)


query = st.text_input(
    "Search",
    placeholder="Apple, Microsoft, NVDA, SPY...",
)


if query:

    with st.spinner(
        "Searching..."
    ):

        results = search_symbols(
            query
        )

    if not results:

        st.warning(
            "No matching securities found."
        )

    for result in results:

        ticker = result[
            "symbol"
        ]

        quote = get_quote(
            ticker
        )

        c1, c2, c3, c4 = st.columns(
            [2.8, 1.5, 1.1, 1.2]
        )

        with c1:

            st.markdown(
                f"### {ticker}"
            )

            st.caption(
                f'{result["name"]} • '
                f'{result["exchange"]}'
            )

        with c2:

            st.metric(
                "Price",
                (
                    f'${quote["price"]:,.2f}'
                    if quote.get("price")
                    is not None
                    else "—"
                ),
                (
                    f'{quote["change_pct"] * 100:+.2f}%'
                    if quote.get(
                        "change_pct"
                    )
                    is not None
                    else None
                ),
            )

        with c3:

            if is_watched(
                ticker
            ):

                if st.button(
                    "Remove",
                    key=f"remove_{ticker}",
                    use_container_width=True,
                ):

                    remove_from_watchlist(
                        ticker
                    )

                    st.rerun()

            else:

                if st.button(
                    "Watch",
                    key=f"watch_{ticker}",
                    use_container_width=True,
                ):

                    add_to_watchlist(
                        ticker
                    )

                    st.rerun()

        with c4:

            if st.button(
                "Analyze",
                key=f"search_analyze_{ticker}",
                use_container_width=True,
            ):

                st.session_state[
                    "selected_ticker"
                ] = ticker

                st.switch_page(
                    "pages/prediction.py"
                )

        st.divider()


st.subheader(
    "Popular"
)

popular = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "TSLA",
    "META",
    "SPY",
]


cols = st.columns(4)

for col, ticker in zip(
    cols,
    popular,
):

    with col:

        if st.button(
            ticker,
            key=f"popular_{ticker}",
            use_container_width=True,
        ):

            st.session_state[
                "selected_ticker"
            ] = ticker

            st.switch_page(
                "pages/prediction.py"
            )
from __future__ import annotations

import streamlit as st

from src.data.market import get_quote
from src.data.search import search_stocks
from src.storage.database import (
    add_to_watchlist,
    is_watched,
    remove_from_watchlist,
)
from src.ui.components import (
    format_money,
    format_percent,
    inject_css,
    page_header,
)


inject_css()


def open_stock(ticker: str) -> None:
    ticker = ticker.strip().upper()

    if not ticker:
        return

    st.session_state["selected_ticker"] = ticker
    st.switch_page("pages/prediction.py")


page_header(
    "Search",
    "Find a stock, ETF, or supported market symbol.",
)


query = st.text_input(
    "Search stocks",
    placeholder="Apple, Microsoft, NVDA, Tesla...",
    key="stock_search",
)


# ---------------------------------------------------------
# Search results
# ---------------------------------------------------------

if query.strip():

    with st.spinner("Searching market symbols..."):
        results = search_stocks(
            query.strip(),
            limit=12,
        )

    if not results:
        st.warning(
            "No matching securities were found."
        )

    else:
        st.markdown(
            '<div class="section-title">Results</div>',
            unsafe_allow_html=True,
        )

        for index, result in enumerate(results):

            ticker = result["symbol"]
            name = result["name"]
            exchange = result.get(
                "exchange"
            ) or result.get(
                "type",
                "",
            )

            with st.container(
                border=True
            ):

                left, middle, right = st.columns(
                    [3.0, 2.0, 1.4]
                )

                # -----------------------------------------
                # Security
                # -----------------------------------------

                with left:
                    st.markdown(
                        f"### {ticker}"
                    )

                    st.caption(
                        name
                    )

                    if exchange:
                        st.caption(
                            exchange
                        )

                # -----------------------------------------
                # Quote
                # -----------------------------------------

                with middle:

                    quote = get_quote(
                        ticker
                    )

                    price = quote.get(
                        "price"
                    )

                    change_pct = quote.get(
                        "change_pct"
                    )

                    st.caption(
                        "Latest quote"
                    )

                    st.write(
                        format_money(
                            price
                        )
                    )

                    if change_pct is not None:
                        st.caption(
                            format_percent(
                                change_pct
                            )
                        )

                # -----------------------------------------
                # Actions
                # -----------------------------------------

                with right:

                    if st.button(
                        "Analyze",
                        key=(
                            f"search_analyze_"
                            f"{ticker}_{index}"
                        ),
                        use_container_width=True,
                    ):
                        open_stock(
                            ticker
                        )

                    watched = is_watched(
                        ticker
                    )

                    if watched:

                        if st.button(
                            "Remove",
                            key=(
                                f"search_remove_"
                                f"{ticker}_{index}"
                            ),
                            use_container_width=True,
                        ):
                            remove_from_watchlist(
                                ticker
                            )
                            st.rerun()

                    else:

                        if st.button(
                            "Watch",
                            key=(
                                f"search_watch_"
                                f"{ticker}_{index}"
                            ),
                            use_container_width=True,
                        ):
                            add_to_watchlist(
                                ticker
                            )
                            st.rerun()


# ---------------------------------------------------------
# Popular
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">Popular</div>',
    unsafe_allow_html=True,
)

popular = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "SPY",
]

for row_start in range(
    0,
    len(popular),
    4,
):

    row = popular[
        row_start:row_start + 4
    ]

    columns = st.columns(4)

    for column, ticker in zip(
        columns,
        row,
    ):

        with column:

            quote = get_quote(
                ticker
            )

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### {ticker}"
                )

                st.write(
                    format_money(
                        quote.get(
                            "price"
                        )
                    )
                )

                change_pct = quote.get(
                    "change_pct"
                )

                if change_pct is not None:
                    st.caption(
                        format_percent(
                            change_pct
                        )
                    )

                if st.button(
                    "Analyze",
                    key=f"popular_{ticker}",
                    use_container_width=True,
                ):
                    open_stock(
                        ticker
                    )
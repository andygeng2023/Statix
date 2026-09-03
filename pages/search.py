from __future__ import annotations

import streamlit as st

from src.data.market import (
    get_quote,
)
from src.data.search import (
    search_stocks,
)
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


def open_stock(
    ticker: str,
) -> None:

    st.session_state[
        "selected_ticker"
    ] = ticker.upper()

    st.switch_page(
        "pages/stock.py"
    )


page_header(
    "Search",
    "Find a stock or ETF and open its fast market view.",
)


query = st.text_input(
    "Search",
    placeholder=(
        "Apple, Microsoft, NVDA, Tesla..."
    ),
)


if query.strip():

    results = search_stocks(
        query,
        limit=12,
    )

    if not results:

        st.warning(
            "No supported symbols were found."
        )

    for index, item in enumerate(
        results
    ):

        ticker = item[
            "symbol"
        ]

        with st.container(
            border=True
        ):

            left, middle, right = (
                st.columns(
                    [4, 2, 1.5]
                )
            )

            with left:

                st.subheader(
                    ticker
                )

                st.caption(
                    item["name"]
                )

                st.caption(
                    item.get(
                        "exchange"
                    )
                    or item.get(
                        "type"
                    )
                    or ""
                )

            with middle:

                # Avoid hitting Yahoo for all 12 results.
                if index < 4:

                    quote = get_quote(
                        ticker
                    )

                    st.write(
                        format_money(
                            quote.get(
                                "price"
                            )
                        )
                    )

                    st.caption(
                        format_percent(
                            quote.get(
                                "change_pct"
                            )
                        )
                    )

                else:

                    st.caption(
                        "Quote loads when opened"
                    )

            with right:

                if st.button(
                    "View",
                    key=f"view_{ticker}_{index}",
                    use_container_width=True,
                ):

                    open_stock(
                        ticker
                    )

                if is_watched(
                    ticker
                ):

                    if st.button(
                        "Remove",
                        key=f"remove_{ticker}_{index}",
                        use_container_width=True,
                    ):

                        remove_from_watchlist(
                            ticker
                        )

                        st.rerun()

                else:

                    if st.button(
                        "Watch",
                        key=f"watch_{ticker}_{index}",
                        use_container_width=True,
                    ):

                        add_to_watchlist(
                            ticker
                        )

                        st.rerun()


st.divider()

st.subheader(
    "Popular"
)


popular = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
]


cols = st.columns(4)


for col, ticker in zip(
    cols,
    popular,
):

    with col:

        quote = get_quote(
            ticker
        )

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

        st.caption(
            format_percent(
                quote.get(
                    "change_pct"
                )
            )
        )

        if st.button(
            "View",
            key=f"popular_{ticker}",
            use_container_width=True,
        ):

            open_stock(
                ticker
            )
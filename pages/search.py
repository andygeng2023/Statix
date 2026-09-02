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
    st.session_state["selected_ticker"] = ticker
    st.switch_page("pages/prediction.py")


page_header(
    "Search",
    "Find a stock, ETF, or other supported market symbol.",
)


query = st.text_input(
    "Search",
    placeholder="Apple, Microsoft, NVDA, Tesla...",
)


if query.strip():
    results = search_stocks(
        query,
        limit=12,
    )

    if not results:
        st.warning(
            "No matching securities were found."
        )

    for index, result in enumerate(results):
        ticker = result["symbol"]

        with st.container(border=True):
            left, middle, right = st.columns(
                [2.8, 2, 1.3]
            )

            with left:
                st.markdown(
                    f"### {ticker}"
                )
                st.caption(
                    result["name"]
                )

            with middle:
                st.caption(
                    result["exchange"]
                    or result["type"]
                )

                quote = get_quote(ticker)

                st.write(
                    format_money(
                        quote.get("price")
                    )
                )

                if quote.get("change_pct") is not None:
                    st.caption(
                        format_percent(
                            quote["change_pct"]
                        )
                    )

            with right:
                if st.button(
                    "Analyze",
                    key=f"analyze_{ticker}_{index}",
                    use_container_width=True,
                ):
                    open_stock(ticker)

                if is_watched(ticker):
                    if st.button(
                        "Remove",
                        key=f"remove_{ticker}_{index}",
                        use_container_width=True,
                    ):
                        remove_from_watchlist(ticker)
                        st.rerun()
                else:
                    if st.button(
                        "Watch",
                        key=f"watch_{ticker}_{index}",
                        use_container_width=True,
                    ):
                        add_to_watchlist(ticker)
                        st.rerun()


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

columns = st.columns(4)

for column, ticker in zip(
    columns,
    popular,
):
    with column:
        quote = get_quote(ticker)

        st.markdown(
            f"**{ticker}**"
        )

        st.caption(
            format_money(
                quote.get("price")
            )
        )

        if st.button(
            "Analyze",
            key=f"popular_{ticker}",
            use_container_width=True,
        ):
            open_stock(ticker)
import streamlit as st

from src.data.search import (
    search_stocks,
)


st.title("Search")

query = st.text_input(
    "Search stocks",
    placeholder=(
        "AAPL, Apple, Nvidia, Microsoft..."
    ),
)


if query:

    results = search_stocks(
        query,
        limit=15,
    )

    if not results:

        st.warning(
            "No matching securities found."
        )

    for result in results:

        left, middle, right = st.columns(
            [1.2, 5, 1]
        )

        left.write(
            f"**{result['symbol']}**"
        )

        middle.write(
            result["name"]
        )

        middle.caption(
            f"{result.get('exchange', '')} · "
            f"{result.get('type', '')}"
        )

        if right.button(
            "Open",
            key=f"open_{result['symbol']}",
        ):

            st.session_state[
                "selected_ticker"
            ] = result["symbol"]

            st.switch_page(
                "pages/stock.py"
            )
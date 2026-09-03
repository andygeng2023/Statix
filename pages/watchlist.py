import streamlit as st

from src.data.market import get_quotes
from src.storage.database import (
    get_watchlist,
    remove_watch,
)


st.title(
    "Watchlist"
)


watchlist = get_watchlist()


if not watchlist:

    st.info(
        "Your watchlist is empty. "
        "Open a stock and add it."
    )

    st.stop()


quotes = get_quotes(
    tuple(watchlist)
)


for index, ticker in enumerate(
    watchlist
):

    quote = quotes.get(
        ticker,
        {},
    )

    columns = st.columns(
        [1.4, 1.4, 1.4, 1]
    )

    columns[0].write(
        f"**{ticker}**"
    )

    price = quote.get(
        "price"
    )

    columns[1].write(
        (
            f"${price:,.2f}"
            if price is not None
            else "—"
        )
    )

    change = quote.get(
        "change_pct"
    )

    columns[2].write(
        (
            f"{change:+.2f}%"
            if change is not None
            else "—"
        )
    )

    if columns[3].button(
        "Open",
        key=f"watch_open_{index}",
    ):

        st.session_state[
            "selected_ticker"
        ] = ticker

        st.switch_page(
            "pages/stock.py"
        )

    if st.button(
        "Remove",
        key=f"watch_remove_{index}",
    ):

        remove_watch(ticker)

        st.rerun()
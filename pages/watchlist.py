import streamlit as st

from src.data.market import get_quote
from src.storage.database import (
    get_watchlist,
    remove_from_watchlist,
)


st.title("Watchlist")

watchlist = get_watchlist()

if not watchlist:

    st.info(
        "Your watchlist is empty."
    )

    st.stop()


for ticker in watchlist:

    quote = None

    try:
        quote = get_quote(ticker)
    except Exception:
        pass

    with st.container(
        border=True
    ):

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.subheader(ticker)

        with c2:

            if quote:
                price = quote.get(
                    "price"
                )

                if price is not None:
                    st.write(
                        f"${price:,.2f}"
                    )

        with c3:

            if quote:

                change = quote.get(
                    "change_pct"
                )

                if change is not None:
                    st.write(
                        f"{change:+.2f}%"
                    )

        with c4:

            if st.button(
                "Open",
                key=f"open_{ticker}",
            ):

                st.query_params[
                    "ticker"
                ] = ticker

                st.switch_page(
                    "pages/stock.py"
                )

            if st.button(
                "Remove",
                key=f"remove_{ticker}",
            ):

                remove_from_watchlist(
                    ticker
                )

                st.rerun()
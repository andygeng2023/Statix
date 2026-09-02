import streamlit as st

from src.storage.database import (
    get_watchlist,
    remove_from_watchlist,
)

from src.data.market import (
    get_quote,
    get_stock_data,
)

from src.ui.components import mini_chart


st.title("Watchlist")

watchlist = get_watchlist()

if not watchlist:
    st.info(
        "No stocks in your watchlist."
    )

    st.page_link(
        "pages/search.py",
        label="Search stocks",
        icon="🔎",
    )

    st.stop()


for ticker in watchlist:

    with st.container(border=True):

        col1, col2, col3 = st.columns(
            [2, 2, 1]
        )

        try:
            quote = get_quote(ticker)
            data = get_stock_data(
                ticker,
                period="3mo",
            )

            with col1:
                st.subheader(ticker)

            with col2:
                st.metric(
                    "Price",
                    f"${quote['price']:,.2f}",
                    f"{quote['change_pct'] * 100:+.2f}%",
                )

            with col3:
                if st.button(
                    "Remove",
                    key=f"watch_remove_{ticker}",
                ):
                    remove_from_watchlist(ticker)
                    st.rerun()

            st.plotly_chart(
                mini_chart(data),
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

        except Exception as e:
            st.error(
                f"{ticker}: {e}"
            )
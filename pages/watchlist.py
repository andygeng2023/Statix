import streamlit as st

from src.data.market import get_quote, get_stock_data
from src.storage.database import (
    get_watchlist,
    remove_from_watchlist,
)


st.title("Watchlist")
st.caption("Your saved stocks and their latest market data.")

watchlist = get_watchlist()

if not watchlist:
    st.info("Your watchlist is empty.")

    if st.button("Search up a stock", use_container_width=True):
        st.switch_page("pages/search.py")

    st.stop()


for ticker in watchlist:
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 2, 1])

        quote = get_quote(ticker)

        with col1:
            st.subheader(ticker)

            if quote["price"] is not None:
                st.write(
                    f"${quote['price']:,.2f}"
                )

        with col2:
            if quote["change_pct"] is not None:
                st.metric(
                    "Daily Change",
                    f"{quote['change_pct']:+.2f}%",
                )
            else:
                st.write("Market change unavailable")

        with col3:
            if st.button(
                "Analyze",
                key=f"analyze_{ticker}",
                use_container_width=True,
            ):
                st.session_state["selected_ticker"] = ticker
                st.switch_page("pages/prediction.py")

            if st.button(
                "Remove",
                key=f"remove_{ticker}",
                use_container_width=True,
            ):
                remove_from_watchlist(ticker)
                st.rerun()

        # Lightweight chart only.
        # This does NOT train the prediction model.
        chart_data = get_stock_data(
            ticker,
            period="6mo",
        )

        if not chart_data.empty:
            st.line_chart(
                chart_data["Close"],
                height=160,
            )
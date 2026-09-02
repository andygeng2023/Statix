import streamlit as st

from src.data.market import get_quote, get_stock_data
from src.storage.database import (
    get_watchlist,
    get_recently_viewed,
)


st.title("Statix")
st.caption(
    "Market intelligence and machine-learning predictions."
)


# --------------------------------------------------
# Quick actions
# --------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    if st.button(
        "Search up a stock",
        use_container_width=True,
    ):
        st.switch_page("pages/search.py")

with col2:
    if st.button(
        "Open Watchlist",
        use_container_width=True,
    ):
        st.switch_page("pages/watchlist.py")


# --------------------------------------------------
# Discover
# --------------------------------------------------

st.divider()

st.header("Discover")

discover = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "SPY",
]

cols = st.columns(4)

for index, ticker in enumerate(discover):

    with cols[index % 4]:

        quote = get_quote(ticker)

        with st.container(border=True):

            st.subheader(ticker)

            if quote["price"] is not None:
                st.write(
                    f"${quote['price']:,.2f}"
                )

            if quote["change_pct"] is not None:
                st.caption(
                    f"{quote['change_pct']:+.2f}% today"
                )

            if st.button(
                "Analyze",
                key=f"discover_{ticker}",
                use_container_width=True,
            ):
                st.session_state["selected_ticker"] = ticker
                st.switch_page("pages/prediction.py")


# --------------------------------------------------
# Watchlist
# --------------------------------------------------

st.divider()

st.header("Your Watchlist")

watchlist = get_watchlist()

if not watchlist:

    st.caption("No stocks saved yet.")

else:

    cols = st.columns(min(3, len(watchlist)))

    for index, ticker in enumerate(watchlist[:6]):

        with cols[index % len(cols)]:

            quote = get_quote(ticker)

            with st.container(border=True):

                st.subheader(ticker)

                if quote["price"] is not None:
                    st.write(
                        f"${quote['price']:,.2f}"
                    )

                if quote["change_pct"] is not None:
                    st.caption(
                        f"{quote['change_pct']:+.2f}%"
                    )

                if st.button(
                    "Open",
                    key=f"watch_{ticker}",
                    use_container_width=True,
                ):
                    st.session_state["selected_ticker"] = ticker
                    st.switch_page("pages/prediction.py")


# --------------------------------------------------
# Recently viewed
# --------------------------------------------------

st.divider()

st.header("Recently Viewed")

recent = get_recently_viewed()

if not recent:

    st.caption(
        "Stocks you analyze will appear here."
    )

else:

    for item in recent:

        ticker = item["ticker"]

        with st.container(border=True):

            left, middle, right = st.columns(
                [2, 3, 1]
            )

            with left:
                st.subheader(ticker)

            with middle:
                st.write(
                    item["direction"]
                )

                st.caption(
                    f"Up probability: "
                    f"{item['probability_up'] * 100:.1f}%"
                )

            with right:

                if st.button(
                    "Open",
                    key=f"recent_{ticker}",
                    use_container_width=True,
                ):
                    st.session_state["selected_ticker"] = ticker
                    st.switch_page("pages/prediction.py")
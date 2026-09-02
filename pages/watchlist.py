import streamlit as st

from src.data.market import get_quote, get_stock_data
from src.storage.database import (
    get_watchlist,
    get_cached_prediction,
    get_recently_viewed,
    remove_from_watchlist,
)
from src.models.ensemble import MODEL_VERSION


st.title("Watchlist")
st.caption(
    "Your saved stocks, market data, and analysis."
)


# --------------------------------------------------
# Header controls
# --------------------------------------------------

header_left, header_right = st.columns([4, 1])

with header_left:
    st.markdown("### Your stocks")

with header_right:
    if st.button(
        "Search",
        use_container_width=True,
    ):
        st.switch_page("pages/search.py")


watchlist = get_watchlist()


if not watchlist:
    st.info(
        "Your watchlist is empty. Search for a stock to add it."
    )

    if st.button(
        "Search up a stock",
        use_container_width=True,
    ):
        st.switch_page("pages/search.py")

    st.stop()


# --------------------------------------------------
# Card grid
# --------------------------------------------------

for row_start in range(0, len(watchlist), 2):

    row = watchlist[row_start:row_start + 2]

    columns = st.columns(2)

    for column, ticker in zip(columns, row):

        with column:

            # --------------------------------------
            # Fast quote
            # --------------------------------------

            quote = get_quote(ticker)

            # --------------------------------------
            # Saved prediction
            # --------------------------------------

            cached_prediction = None

            # We use the most recent viewed prediction.
            # No model training happens on this page.
            recent = get_recently_viewed(
                limit=len(watchlist) + 5
            )

            for item in recent:
                if item["ticker"] == ticker:
                    cached_prediction = item
                    break

            # --------------------------------------
            # Card
            # --------------------------------------

            with st.container(border=True):

                title_col, signal_col = st.columns(
                    [3, 1]
                )

                with title_col:

                    st.markdown(
                        f"### {ticker}"
                    )

                    if quote["price"] is not None:

                        price_text = (
                            f"${quote['price']:,.2f}"
                        )

                        if quote["change_pct"] is not None:
                            price_text += (
                                f"  "
                                f"{quote['change_pct']:+.2f}%"
                            )

                        st.markdown(
                            f"**{price_text}**"
                        )

                    else:
                        st.caption(
                            "Price unavailable"
                        )

                with signal_col:

                    if cached_prediction:

                        direction = (
                            cached_prediction.get(
                                "direction"
                            )
                        )

                        if direction:
                            st.markdown(
                                f"**{direction}**"
                            )

                # ----------------------------------
                # Metrics
                # ----------------------------------

                metric_1, metric_2, metric_3 = st.columns(3)

                if cached_prediction:

                    with metric_1:
                        st.caption("Up")
                        probability = (
                            cached_prediction.get(
                                "probability_up"
                            )
                        )

                        if probability is not None:
                            st.write(
                                f"{probability * 100:.0f}%"
                            )
                        else:
                            st.write("—")

                    with metric_2:
                        st.caption("Expected 5D")
                        expected = (
                            cached_prediction.get(
                                "expected_return"
                            )
                        )

                        if expected is not None:
                            st.write(
                                f"{expected * 100:+.1f}%"
                            )
                        else:
                            st.write("—")

                    with metric_3:
                        st.caption("Confidence")
                        confidence = (
                            cached_prediction.get(
                                "confidence"
                            )
                        )

                        if confidence is not None:
                            st.write(
                                f"{confidence * 100:.0f}%"
                            )
                        else:
                            st.write("—")

                else:

                    with metric_1:
                        st.caption("Analysis")
                        st.write("Not analyzed")

                    with metric_2:
                        st.caption("Expected 5D")
                        st.write("—")

                    with metric_3:
                        st.caption("Confidence")
                        st.write("—")

                # ----------------------------------
                # Graph
                # ----------------------------------

                chart_data = get_stock_data(
                    ticker,
                    period="6mo",
                    interval="1d",
                )

                if not chart_data.empty:

                    st.line_chart(
                        chart_data["Close"],
                        height=120,
                    )

                # ----------------------------------
                # Analysis status
                # ----------------------------------

                if cached_prediction:

                    market_date = (
                        cached_prediction.get(
                            "last_market_date"
                        )
                    )

                    if market_date:

                        st.caption(
                            f"Saved analysis: {market_date}"
                        )

                else:

                    st.caption(
                        "No saved prediction yet."
                    )

                # ----------------------------------
                # Buttons
                # ----------------------------------

                action_1, action_2 = st.columns(2)

                with action_1:

                    if st.button(
                        "Analyze",
                        key=f"watch_analyze_{ticker}",
                        use_container_width=True,
                    ):

                        st.session_state[
                            "selected_ticker"
                        ] = ticker

                        st.switch_page(
                            "pages/prediction.py"
                        )

                with action_2:

                    if st.button(
                        "Remove",
                        key=f"watch_remove_{ticker}",
                        use_container_width=True,
                    ):

                        remove_from_watchlist(
                            ticker
                        )

                        st.rerun()

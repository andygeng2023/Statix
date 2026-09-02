import streamlit as st

from src.data.market import (
    get_quote,
    get_stock_data,
)

from src.storage.database import (
    get_watchlist,
    remove_from_watchlist,
)

from src.ui.components import (
    mini_chart,
)


st.title("Watchlist")

watchlist = get_watchlist()


if not watchlist:

    st.info(
        "No stocks are currently saved."
    )

    st.page_link(
        "pages/search.py",
        label="Search stocks",
    )

    st.stop()


for ticker in watchlist:

    with st.container(
        border=True
    ):

        c1, c2, c3 = st.columns(
            [2, 4, 1]
        )

        try:

            quote = get_quote(
                ticker
            )

            data = get_stock_data(
                ticker,
                period="3mo",
            )

            with c1:

                st.subheader(
                    ticker
                )

                st.metric(
                    "Price",
                    (
                        f"${quote['price']:,.2f}"
                    ),
                    (
                        f"{quote['change_pct'] * 100:+.2f}%"
                    ),
                )

            with c2:

                st.plotly_chart(
                    mini_chart(data),
                    use_container_width=True,
                    config={
                        "displayModeBar": False
                    },
                )

            with c3:

                if st.button(
                    "Analyze",
                    key=(
                        f"watch_analyze_{ticker}"
                    ),
                ):

                    st.session_state[
                        "selected_ticker"
                    ] = ticker

                    st.switch_page(
                        "pages/prediction.py"
                    )

                if st.button(
                    "Remove",
                    key=(
                        f"watch_remove_{ticker}"
                    ),
                ):

                    remove_from_watchlist(
                        ticker
                    )

                    st.rerun()

        except Exception as error:

            st.error(
                f"{ticker}: {error}"
            )
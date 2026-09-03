from __future__ import annotations

import streamlit as st

from src.data.market import (
    get_quote,
    get_stock_data,
)

from src.storage.database import (
    get_recently_viewed,
    get_watchlist,
    remove_from_watchlist,
)

from src.ui.components import (
    format_confidence,
    format_money,
    format_percent,
    format_probability,
    inject_css,
    mini_chart,
    page_header,
)


inject_css()


def open_stock(
    ticker: str,
) -> None:

    st.session_state[
        "selected_ticker"
    ] = ticker

    st.switch_page(
        "pages/stock.py"
    )


page_header(
    "Watchlist",
    "Your stocks with current market data and saved predictions.",
)


watchlist = get_watchlist()


if not watchlist:

    st.info(
        "Your watchlist is empty."
    )

    if st.button(
        "Search stocks",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/search.py"
        )

    st.stop()


recent = get_recently_viewed(
    limit=100
)


prediction_lookup = {
    item["ticker"]: item
    for item in recent
}


for start in range(
    0,
    len(watchlist),
    2,
):

    row = watchlist[
        start:start + 2
    ]

    cols = st.columns(2)

    for col, ticker in zip(
        cols,
        row,
    ):

        with col:

            quote = get_quote(
                ticker
            )

            saved = (
                prediction_lookup.get(
                    ticker
                )
            )

            with st.container(
                border=True
            ):

                top_left, top_right = (
                    st.columns(
                        [2, 1]
                    )
                )

                with top_left:

                    st.markdown(
                        f"### {ticker}"
                    )

                    st.caption(
                        "Market data"
                    )

                with top_right:

                    if st.button(
                        "Analyze",
                        key=f"analyze_{ticker}",
                        use_container_width=True,
                    ):

                        open_stock(
                            ticker
                        )

                metrics = st.columns(3)

                with metrics[0]:

                    st.caption(
                        "Price"
                    )

                    st.write(
                        format_money(
                            quote.get(
                                "price"
                            )
                        )
                    )

                with metrics[1]:

                    st.caption(
                        "Daily"
                    )

                    st.write(
                        format_percent(
                            quote.get(
                                "change_pct"
                            )
                        )
                    )

                with metrics[2]:

                    st.caption(
                        "Signal"
                    )

                    st.write(
                        saved.get(
                            "direction"
                        )
                        if saved
                        else "—"
                    )

                chart = get_stock_data(
                    ticker,
                    period="6mo",
                    interval="1d",
                )

                mini_chart(
                    chart
                )

                if saved:

                    metrics = st.columns(
                        4
                    )

                    with metrics[0]:

                        st.caption(
                            "Up"
                        )

                        st.write(
                            format_probability(
                                saved.get(
                                    "probability_up"
                                )
                            )
                        )

                    with metrics[1]:

                        st.caption(
                            "5D return"
                        )

                        value = saved.get(
                            "expected_return"
                        )

                        st.write(
                            format_percent(
                                value * 100
                                if value is not None
                                else None
                            )
                        )

                    with metrics[2]:

                        st.caption(
                            "Confidence"
                        )

                        st.write(
                            format_confidence(
                                saved.get(
                                    "confidence"
                                )
                            )
                        )

                    with metrics[3]:

                        st.caption(
                            "Accuracy"
                        )

                        accuracy = (
                            saved.get(
                                "test_accuracy"
                            )
                        )

                        st.write(
                            format_percent(
                                accuracy * 100
                                if accuracy is not None
                                else None
                            )
                        )

                    st.caption(
                        "Analysis date: "
                        + str(
                            saved.get(
                                "market_date"
                            )
                            or "—"
                        )
                    )

                else:

                    st.caption(
                        "No prediction saved yet."
                    )

                if st.button(
                    "Remove",
                    key=f"remove_{ticker}",
                    use_container_width=True,
                ):

                    remove_from_watchlist(
                        ticker
                    )

                    st.rerun()
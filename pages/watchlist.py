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


def open_stock(ticker: str) -> None:
    st.session_state["selected_ticker"] = ticker
    st.switch_page("pages/prediction.py")


page_header(
    "Watchlist",
    "Compact market cards with price, prediction, confidence, and trend.",
)


watchlist = get_watchlist()

if not watchlist:
    st.info(
        "Your watchlist is empty. Search for a stock and add it."
    )

    if st.button(
        "Search stocks",
        use_container_width=True,
    ):
        st.switch_page("pages/search.py")

    st.stop()


recent = get_recently_viewed(
    limit=100
)

prediction_lookup = {
    item["ticker"]: item
    for item in recent
}


for row_start in range(
    0,
    len(watchlist),
    2,
):
    row = watchlist[
        row_start:row_start + 2
    ]

    columns = st.columns(2)

    for column, ticker in zip(
        columns,
        row,
    ):
        with column:

            quote = get_quote(ticker)

            price = quote.get(
                "price"
            )

            change_pct = quote.get(
                "change_pct"
            )

            saved = prediction_lookup.get(
                ticker
            )

            with st.container(
                border=True
            ):
                top_left, top_right = st.columns(
                    [2, 1]
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
                        open_stock(ticker)

                price_cols = st.columns(3)

                with price_cols[0]:
                    st.caption("Price")
                    st.write(
                        format_money(price)
                    )

                with price_cols[1]:
                    st.caption("Daily")
                    st.write(
                        format_percent(
                            change_pct
                        )
                    )

                with price_cols[2]:
                    st.caption("Signal")
                    st.write(
                        saved["direction"]
                        if saved
                        else "—"
                    )

                chart = get_stock_data(
                    ticker,
                    period="6mo",
                    interval="1d",
                )

                mini_chart(chart)

                if saved:
                    metric_cols = st.columns(4)

                    with metric_cols[0]:
                        st.caption("Up")
                        st.write(
                            format_probability(
                                saved[
                                    "probability_up"
                                ]
                            )
                        )

                    with metric_cols[1]:
                        st.caption("5D return")
                        st.write(
                            format_percent(
                                (
                                    saved[
                                        "expected_return"
                                    ] * 100
                                    if saved[
                                        "expected_return"
                                    ] is not None
                                    else None
                                )
                            )
                        )

                    with metric_cols[2]:
                        st.caption("Confidence")
                        st.write(
                            format_confidence(
                                saved[
                                    "confidence"
                                ]
                            )
                        )

                    with metric_cols[3]:
                        st.caption("Accuracy")
                        st.write(
                            format_percent(
                                (
                                    saved[
                                        "test_accuracy"
                                    ] * 100
                                    if saved[
                                        "test_accuracy"
                                    ] is not None
                                    else None
                                )
                            )
                        )

                    if saved["market_date"]:
                        st.caption(
                            "Analysis date: "
                            + str(
                                saved[
                                    "market_date"
                                ]
                            )
                        )
                else:
                    st.caption(
                        "No saved prediction yet. "
                        "Open Analyze to generate one."
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
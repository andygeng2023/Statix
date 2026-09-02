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
    format_money,
    format_percent,
    format_probability,
    mini_chart,
)


st.title("Watchlist")

st.caption(
    "Compact view of your saved securities."
)


top1, top2 = st.columns(
    [4, 1]
)

with top1:

    st.write(
        "Quotes refresh frequently. "
        "Historical charts are cached."
    )

with top2:

    if st.button(
        "Refresh",
        use_container_width=True,
    ):

        st.cache_data.clear()
        st.rerun()


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

            prediction = (
                prediction_lookup.get(
                    ticker
                )
            )

            st.markdown(
                f"## {ticker}"
            )

            left, right = st.columns(
                [1.4, 1]
            )

            with left:

                st.markdown(
                    f"### {format_money(quote.get('price'))}"
                )

                st.caption(
                    "Today: "
                    + format_percent(
                        quote.get(
                            "change_pct"
                        )
                    )
                )

            with right:

                if prediction:

                    st.markdown(
                        f"**{prediction.get('direction', 'Neutral')}**"
                    )

                    st.caption(
                        "Saved model signal"
                    )

                else:

                    st.caption(
                        "No saved analysis"
                    )

            chart = get_stock_data(
                ticker,
                period="6mo",
            )

            mini_chart(
                chart
            )

            if prediction:

                c1, c2, c3, c4 = st.columns(
                    4
                )

                with c1:

                    st.caption("UP")

                    st.write(
                        format_probability(
                            prediction.get(
                                "probability_up"
                            )
                        )
                    )

                with c2:

                    st.caption("5D")

                    st.write(
                        format_percent(
                            prediction.get(
                                "expected_return"
                            )
                        )
                    )

                with c3:

                    st.caption("CONF.")

                    st.write(
                        format_probability(
                            prediction.get(
                                "confidence"
                            )
                        )
                    )

                with c4:

                    st.caption("ACC.")

                    st.write(
                        format_probability(
                            prediction.get(
                                "accuracy"
                            )
                        )
                    )

                st.caption(
                    "Analysis: "
                    + str(
                        prediction.get(
                            "market_date",
                            "—",
                        )
                    )
                )

            else:

                st.caption(
                    "No model analysis saved yet."
                )

            a, b = st.columns(2)

            with a:

                if st.button(
                    "Analyze",
                    key=f"analyze_watch_{ticker}",
                    use_container_width=True,
                ):

                    st.session_state[
                        "selected_ticker"
                    ] = ticker

                    st.switch_page(
                        "pages/prediction.py"
                    )

            with b:

                if st.button(
                    "Remove",
                    key=f"remove_watch_{ticker}",
                    use_container_width=True,
                ):

                    remove_from_watchlist(
                        ticker
                    )

                    st.rerun()

            st.divider()
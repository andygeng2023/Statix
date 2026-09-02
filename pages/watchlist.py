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
    "Compact market view. Charts use historical data; saved predictions are shown without retraining."
)


if st.button(
    "Refresh quotes",
    use_container_width=False,
):

    st.cache_data.clear()
    st.rerun()


watchlist = get_watchlist()

if not watchlist:

    st.info(
        "Your watchlist is empty. Search for a stock and add it."
    )

    if st.button("Search stocks"):
        st.switch_page("pages/search.py")

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

            quote = get_quote(ticker)

            price = quote.get(
                "price"
            )

            daily_change = quote.get(
                "change_pct"
            )

            prediction = prediction_lookup.get(
                ticker
            )

            st.markdown(
                f"## {ticker}"
            )

            price_col, signal_col = st.columns(
                [1.3, 1]
            )

            with price_col:

                st.markdown(
                    f"### {format_money(price)}"
                )

                st.caption(
                    f"Today: {format_percent(daily_change)}"
                )

            with signal_col:

                if prediction:

                    st.markdown(
                        f"**{prediction.get('direction', '—')}**"
                    )

                    st.caption(
                        "Saved model analysis"
                    )

                else:

                    st.caption(
                        "No saved analysis"
                    )

            try:

                chart_df = get_stock_data(
                    ticker,
                    period="6mo",
                    interval="1d",
                )

                mini_chart(chart_df)

            except Exception:

                st.caption(
                    "Chart unavailable"
                )

            if prediction:

                c1, c2, c3, c4 = st.columns(4)

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
                    f"Analysis date: "
                    f"{prediction.get('market_date', '—')}"
                )

            else:

                st.caption(
                    "Analyze this stock to generate a model forecast."
                )

            a, b = st.columns(2)

            with a:

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

            with b:

                if st.button(
                    "Remove",
                    key=f"watch_remove_{ticker}",
                    use_container_width=True,
                ):

                    remove_from_watchlist(
                        ticker
                    )

                    st.rerun()

            st.divider()
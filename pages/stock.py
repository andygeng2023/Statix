from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.data.market import (
    get_quote,
    get_stock_data,
)

from src.storage.database import (
    add_to_watchlist,
    is_watched,
    remove_from_watchlist,
)

from src.ui.components import (
    format_money,
    format_percent,
    inject_css,
    page_header,
)


inject_css()


if "selected_ticker" not in st.session_state:
    st.session_state[
        "selected_ticker"
    ] = None


ticker = str(
    st.session_state.get(
        "selected_ticker"
    )
    or ""
).strip().upper()


if not ticker:

    page_header(
        "Stock",
        "Select a symbol from Search.",
    )

    if st.button(
        "Search stocks",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/search.py"
        )

    st.stop()


page_header(
    ticker,
    "Fast market view. Prediction is separate and on demand.",
)


@st.fragment(
    run_every="20s"
)
def live_quote():

    quote = get_quote(
        ticker
    )

    top_left, top_right = (
        st.columns(
            [4, 1]
        )
    )

    with top_left:

        st.caption(
            f"{quote.get('provider', 'Market data')} "
            "· refreshes approximately every 20 seconds"
        )

    with top_right:

        if is_watched(
            ticker
        ):

            if st.button(
                "Remove",
                key="stock_remove",
                use_container_width=True,
            ):

                remove_from_watchlist(
                    ticker
                )

                st.rerun()

        else:

            if st.button(
                "Watch",
                key="stock_watch",
                use_container_width=True,
            ):

                add_to_watchlist(
                    ticker
                )

                st.rerun()

    cols = st.columns(4)

    with cols[0]:

        st.metric(
            "Price",
            format_money(
                quote.get(
                    "price"
                )
            ),
        )

    with cols[1]:

        st.metric(
            "Daily",
            format_percent(
                quote.get(
                    "change_pct"
                )
            ),
        )

    with cols[2]:

        volume = quote.get(
            "volume"
        )

        st.metric(
            "Volume",
            (
                f"{volume:,.0f}"
                if volume is not None
                else "—"
            ),
        )

    with cols[3]:

        st.metric(
            "Data",
            "Yahoo",
        )


live_quote()


history = get_stock_data(
    ticker,
    period="1y",
    interval="1d",
)


st.divider()


if history.empty:

    st.warning(
        "No historical chart data is currently available."
    )

else:

    chart_range = st.segmented_control(
        "Chart range",
        [
            "1M",
            "3M",
            "6M",
            "1Y",
        ],
        default="6M",
    )

    rows = {
        "1M": 22,
        "3M": 66,
        "6M": 132,
        "1Y": 252,
    }

    chart_df = history.tail(
        rows.get(
            chart_range or "6M",
            132,
        )
    )

    fig = go.Figure(
        go.Candlestick(
            x=chart_df.index,
            open=chart_df["open"],
            high=chart_df["high"],
            low=chart_df["low"],
            close=chart_df["close"],
            name=ticker,
        )
    )

    fig.update_layout(
        height=560,
        xaxis_rangeslider_visible=False,
        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


if not history.empty:

    st.subheader(
        "Market stats"
    )

    close = history[
        "close"
    ]

    cols = st.columns(4)

    with cols[0]:

        st.metric(
            "52W high",
            format_money(
                close.tail(
                    252
                ).max()
            ),
        )

    with cols[1]:

        st.metric(
            "52W low",
            format_money(
                close.tail(
                    252
                ).min()
            ),
        )

    with cols[2]:

        if len(close) >= 22:

            return_1m = (
                close.iloc[-1]
                / close.iloc[-22]
                - 1
            ) * 100

        else:

            return_1m = None

        st.metric(
            "1M return",
            format_percent(
                return_1m
            ),
        )

    with cols[3]:

        if len(close) >= 132:

            return_6m = (
                close.iloc[-1]
                / close.iloc[-132]
                - 1
            ) * 100

        else:

            return_6m = None

        st.metric(
            "6M return",
            format_percent(
                return_6m
            ),
        )


st.divider()

left, right = st.columns(
    [2, 1]
)


with left:

    st.subheader(
        "Prediction"
    )

    st.write(
        "The stock view loads first. "
        "Statix only trains the prediction model "
        "when you request a prediction."
    )


with right:

    if st.button(
        "Generate prediction",
        type="primary",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/prediction.py"
        )
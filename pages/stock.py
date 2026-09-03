import streamlit as st
import plotly.graph_objects as go

from src.data.market import (
    get_quote,
    get_stock_data,
)
from src.storage.database import (
    add_viewed,
    add_watch,
    get_watchlist,
    remove_watch,
)


ticker = (
    st.query_params.get("ticker")
    or st.session_state.get(
        "selected_ticker"
    )
    or "AAPL"
).upper().strip()


st.session_state[
    "selected_ticker"
] = ticker

add_viewed(ticker)


@st.fragment(run_every="20s")
def live_header():

    quote = get_quote(ticker)

    st.title(ticker)

    price = quote.get(
        "price"
    )

    change = quote.get(
        "change_pct"
    )

    columns = st.columns(4)

    columns[0].metric(
        "Price",
        (
            f"${price:,.2f}"
            if price is not None
            else "—"
        ),
    )

    columns[1].metric(
        "Day",
        (
            f"{change:+.2f}%"
            if change is not None
            else "—"
        ),
    )

    columns[2].metric(
        "Provider",
        "Market feed",
    )

    columns[3].metric(
        "Status",
        (
            "Fresh"
            if quote.get("fresh")
            else "Delayed/estimated"
        ),
    )

    st.caption(
        "Quote refreshes while this page "
        "is open. Provider freshness varies."
    )


live_header()


watchlist = get_watchlist()

is_watched = (
    ticker in watchlist
)


if st.button(
    (
        "Remove from watchlist"
        if is_watched
        else "Add to watchlist"
    ),
    use_container_width=True,
):

    if is_watched:
        remove_watch(ticker)
    else:
        add_watch(ticker)

    st.rerun()


history = get_stock_data(
    ticker,
    "2y",
    "1d",
)


if history.empty:

    st.error(
        "No historical market data was returned."
    )

    st.stop()


st.subheader(
    "Price History"
)


chart = go.Figure()

chart.add_trace(
    go.Candlestick(
        x=history.index,
        open=history["Open"],
        high=history["High"],
        low=history["Low"],
        close=history["Close"],
        name=ticker,
    )
)

chart.update_layout(
    height=520,
    xaxis_rangeslider_visible=False,
    margin=dict(
        l=10,
        r=10,
        t=20,
        b=10,
    ),
)


st.plotly_chart(
    chart,
    use_container_width=True,
)


st.divider()


a, b, c = st.columns(3)


with a:

    if st.button(
        "Run Prediction",
        type="primary",
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
        "Search Another",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/search.py"
        )


with c:

    st.caption(
        "Prediction models are experimental "
        "research tools."
    )
import streamlit as st
import plotly.graph_objects as go

from src.data.market import (
    get_quote,
    get_stock_data,
)
from src.models.inference import predict
from src.storage.database import (
    add_to_watchlist,
    record_view,
    remove_from_watchlist,
    get_watchlist,
)
from src.ui.components import (
    prediction_card,
    stock_header,
)


ticker = st.query_params.get(
    "ticker",
    "",
)

ticker = ticker.upper().strip()

if not ticker:

    st.title("Stock")

    ticker = st.text_input(
        "Enter a ticker",
        placeholder="AAPL",
    ).upper().strip()

    if not ticker:
        st.stop()


record_view(ticker)

quote = get_quote(ticker)

stock_header(
    ticker,
    quote,
)

watchlist = get_watchlist()

if ticker in watchlist:

    if st.button(
        "Remove from watchlist"
    ):
        remove_from_watchlist(
            ticker
        )
        st.rerun()

else:

    if st.button(
        "Add to watchlist"
    ):
        add_to_watchlist(
            ticker
        )
        st.rerun()


@st.fragment(run_every="20s")
def live_market():

    fresh_quote = get_quote(ticker)

    if not fresh_quote:
        return

    price = fresh_quote.get(
        "price"
    )

    change = fresh_quote.get(
        "change_pct"
    )

    c1, c2 = st.columns(2)

    with c1:
        if price is not None:
            st.metric(
                "Current price",
                f"${price:,.2f}",
            )

    with c2:
        if change is not None:
            st.metric(
                "Session change",
                f"{change:+.2f}%",
            )


live_market()


df = get_stock_data(
    ticker,
    period="5y",
    interval="1d",
)

if df.empty:
    st.error(
        "No historical market data was returned."
    )
    st.stop()


st.divider()

st.subheader("Price")

chart = go.Figure()

chart.add_trace(
    go.Scatter(
        x=df.index,
        y=df["Close"],
        mode="lines",
        name="Close",
    )
)

chart.update_layout(
    height=400,
    margin=dict(
        l=0,
        r=0,
        t=20,
        b=0,
    ),
)

st.plotly_chart(
    chart,
    use_container_width=True,
)


st.divider()

st.subheader(
    "Statix prediction"
)

with st.spinner(
    "Running model..."
):

    result = predict(df)

prediction_card(
    result
)


if result.get("available"):

    st.subheader(
        "Prediction distribution"
    )

    probabilities = result[
        "class_probabilities"
    ]

    for name, probability in probabilities.items():

        st.progress(
            probability,
            text=(
                f"{name}: "
                f"{probability:.1%}"
            ),
        )


    st.caption(
        "The model estimates probabilities and "
        "returns from historical market patterns. "
        "This is not a guarantee of future performance."
    )


with st.expander(
    "Model details"
):

    st.write(
        "Architecture: PatchTST-style temporal encoder"
    )

    st.write(
        "Outputs: 1-day, 5-day and 20-day return estimates "
        "plus a five-class direction forecast."
    )

    st.write(
        "Inference uses a pre-trained model artifact; "
        "the model is not retrained when this page refreshes."
    )
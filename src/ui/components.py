import plotly.graph_objects as go
import streamlit as st


def mini_chart(df):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            hovertemplate=(
                "$%{y:.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=120,
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0,
        ),
        xaxis=dict(
            visible=False
        ),
        yaxis=dict(
            visible=False
        ),
        showlegend=False,
    )

    return fig


def show_prediction_metrics(
    prediction,
):
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Signal",
        prediction["direction"],
    )

    c2.metric(
        "Up Probability",
        (
            f"{prediction['probability_up'] * 100:.1f}%"
        ),
    )

    c3.metric(
        "Expected Return",
        (
            f"{prediction['expected_return'] * 100:+.2f}%"
        ),
    )

    c4.metric(
        "Confidence",
        (
            f"{prediction['confidence'] * 100:.1f}%"
        ),
    )


def prediction_card(
    item,
):
    ticker = item["ticker"]

    st.subheader(ticker)

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Price",
        (
            f"${item['price']:,.2f}"
            if item["price"] is not None
            else "—"
        ),
    )

    c2.metric(
        "Signal",
        item["direction"] or "—",
    )

    c3.metric(
        "Up Probability",
        (
            f"{item['probability_up'] * 100:.1f}%"
            if item[
                "probability_up"
            ]
            is not None
            else "—"
        ),
    )

    if item["expected_return"] is not None:
        st.caption(
            "Estimated return: "
            f"{item['expected_return'] * 100:+.2f}%"
        )
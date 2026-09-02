import streamlit as st
import plotly.graph_objects as go


def mini_chart(df):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            line=dict(width=2),
            hovertemplate="%{y:.2f}<extra></extra>",
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


def prediction_badge(prediction):
    direction = prediction["direction"]

    if direction == "Bullish":
        label = "BULLISH"
    elif direction == "Bearish":
        label = "BEARISH"
    else:
        label = "NEUTRAL"

    st.markdown(
        f"### {label}"
    )


def stock_card(
    ticker,
    quote,
    prediction=None,
    chart=None,
):
    st.subheader(ticker)

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Price",
            f"${quote['price']:,.2f}",
            f"{quote['change_pct'] * 100:+.2f}%",
        )

    if prediction:

        with col2:
            st.metric(
                "Up Probability",
                f"{prediction['probability_up'] * 100:.1f}%",
            )

        st.caption(
            f"{prediction['direction']} · "
            f"Expected return: "
            f"{prediction['expected_return'] * 100:+.2f}%"
        )

    if chart is not None:
        st.plotly_chart(
            mini_chart(chart),
            use_container_width=True,
            config={"displayModeBar": False},
        )
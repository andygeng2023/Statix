import plotly.graph_objects as go
import streamlit as st


def format_money(value):
    if value is None:
        return "—"

    return f"${value:,.2f}"


def format_percent(value, decimals=2):
    if value is None:
        return "—"

    return f"{value * 100:+.{decimals}f}%"


def format_probability(value):
    if value is None:
        return "—"

    return f"{value * 100:.0f}%"


def mini_chart(df, height=115):
    if df is None or df.empty or "Close" not in df.columns:
        return None

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            line=dict(width=2),
            hovertemplate="$%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        height=height,
        margin=dict(
            l=0,
            r=0,
            t=4,
            b=4,
        ),
        showlegend=False,
        xaxis=dict(
            visible=False,
            fixedrange=True,
        ),
        yaxis=dict(
            visible=False,
            fixedrange=True,
        ),
        hovermode="x",
    )

    return fig


def show_prediction_metrics(prediction):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Signal",
            prediction.get("direction", "—"),
        )

    with col2:
        st.metric(
            "Up Probability",
            format_probability(
                prediction.get("probability_up")
            ),
        )

    with col3:
        st.metric(
            "Expected Return",
            format_percent(
                prediction.get("expected_return")
            ),
        )

    with col4:
        confidence = prediction.get("confidence")

        if confidence is not None:
            st.metric(
                "Confidence",
                f"{confidence * 100:.0f}%",
            )
        else:
            st.metric("Confidence", "—")


def prediction_card(item):
    ticker = item.get("ticker", "—")
    price = item.get("last_price")
    direction = item.get("direction")
    probability = item.get("probability_up")
    expected_return = item.get("expected_return")
    confidence = item.get("confidence")

    with st.container(border=True):

        top_left, top_right = st.columns([3, 1])

        with top_left:
            st.markdown(
                f"### {ticker}"
            )

            if price is not None:
                st.caption(
                    format_money(price)
                )

        with top_right:
            if direction:
                st.markdown(
                    f"**{direction}**"
                )

        # Compact metric row
        c1, c2, c3 = st.columns(3)

        with c1:
            st.caption("Up probability")
            st.write(
                format_probability(probability)
            )

        with c2:
            st.caption("Expected 5D")
            st.write(
                format_percent(expected_return)
            )

        with c3:
            st.caption("Confidence")
            if confidence is not None:
                st.write(
                    f"{confidence * 100:.0f}%"
                )
            else:
                st.write("—")

        return True

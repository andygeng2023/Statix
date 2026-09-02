import pandas as pd
import streamlit as st


def format_money(value):

    if value is None:
        return "—"

    return f"${float(value):,.2f}"


def format_percent(value):

    if value is None:
        return "—"

    return f"{float(value) * 100:+.2f}%"


def format_probability(value):

    if value is None:
        return "—"

    return f"{float(value) * 100:.1f}%"


def signal_badge(direction):

    if direction == "Bullish":
        symbol = "▲"
    elif direction == "Bearish":
        symbol = "▼"
    else:
        symbol = "•"

    return f"{symbol} {direction}"


def mini_chart(df):

    if df is None or df.empty:
        st.caption("No chart data")
        return

    chart = df[["Close"]].tail(90).copy()

    chart.columns = ["Price"]

    st.line_chart(
        chart,
        height=120,
        use_container_width=True,
    )


def metric_grid(items):

    columns = st.columns(len(items))

    for column, item in zip(columns, items):

        with column:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="small-label">
                        {item["label"]}
                    </div>
                    <div class="small-value">
                        {item["value"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def prediction_card(prediction):

    direction = prediction.get(
        "direction",
        "Neutral",
    )

    st.markdown(
        '<div class="signal-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"### {signal_badge(direction)}"
    )

    st.caption(
        "5-session model outlook"
    )

    metric_grid(
        [
            {
                "label": "Probability Up",
                "value": format_probability(
                    prediction.get(
                        "probability_up"
                    )
                ),
            },
            {
                "label": "Expected Return",
                "value": format_percent(
                    prediction.get(
                        "expected_return"
                    )
                ),
            },
            {
                "label": "Confidence",
                "value": format_probability(
                    prediction.get(
                        "confidence"
                    )
                ),
            },
            {
                "label": "Model Agreement",
                "value": format_probability(
                    prediction.get(
                        "agreement"
                    )
                ),
            },
        ]
    )

    st.markdown("</div>", unsafe_allow_html=True)


def display_class_probabilities(prediction):

    probabilities = prediction.get(
        "class_probabilities",
        {},
    )

    if not probabilities:
        return

    frame = pd.DataFrame(
        {
            "Signal": list(
                probabilities.keys()
            ),
            "Probability": [
                value * 100
                for value in probabilities.values()
            ],
        }
    )

    frame = frame.set_index("Signal")

    st.bar_chart(
        frame,
        height=260,
    )
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


def metric_grid(items):

    columns = st.columns(
        len(items)
    )

    for column, item in zip(
        columns,
        items,
    ):

        with column:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        {item["label"]}
                    </div>
                    <div class="metric-value">
                        {item["value"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def mini_chart(df):

    if df is None or df.empty:

        st.caption(
            "Chart unavailable"
        )

        return

    chart = df[
        ["Close"]
    ].tail(90).copy()

    chart.columns = [
        "Price"
    ]

    st.line_chart(
        chart,
        height=120,
        use_container_width=True,
    )


def prediction_card(
    prediction
):

    direction = prediction.get(
        "direction",
        "Neutral",
    )

    st.markdown(
        '<div class="signal-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"### {direction}"
    )

    st.caption(
        "Model outlook: next 5 market sessions"
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
                "label": "Agreement",
                "value": format_probability(
                    prediction.get(
                        "agreement"
                    )
                ),
            },
        ]
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


def display_class_probabilities(
    prediction
):

    probabilities = prediction.get(
        "class_probabilities",
        {},
    )

    if not probabilities:
        return

    st.bar_chart(
        {
            key: [
                value * 100
                for value in probabilities.values()
            ]
            for key in probabilities.keys()
        },
        height=280,
    )
import streamlit as st


def signal_badge(signal):

    if "Bullish" in signal:
        return f"**{signal}**"

    if "Bearish" in signal:
        return f"**{signal}**"

    return f"**{signal}**"


def prediction_card(result):

    if not result.get("available"):
        st.warning(
            result.get(
                "reason",
                "Prediction unavailable.",
            )
        )
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Signal",
            result["signal"],
        )

    with col2:
        st.metric(
            "Probability",
            f"{result['probability']:.1%}",
        )

    with col3:
        st.metric(
            "5D model return",
            f"{result['return_5d']:.2%}",
        )

    with col4:
        st.metric(
            "Reliability",
            f"{result['confidence']:.1%}",
        )


def stock_header(
    ticker,
    quote,
):

    st.title(ticker)

    if not quote:
        return

    price = quote.get("price")

    change_pct = quote.get(
        "change_pct"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if price is not None:
            st.metric(
                "Price",
                f"${price:,.2f}",
            )

    with col2:
        if change_pct is not None:
            st.metric(
                "Today",
                f"{change_pct:+.2f}%",
            )

    with col3:
        st.caption(
            "Market data may be delayed depending on provider."
        )
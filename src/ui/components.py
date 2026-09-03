import streamlit as st


def metric_row(items):

    columns = st.columns(
        len(items)
    )

    for column, item in zip(
        columns,
        items,
    ):

        label = item[0]

        value = item[1]

        help_text = (
            item[2]
            if len(item) > 2
            else None
        )

        column.metric(
            label,
            value,
            help=help_text,
        )


def signal_color_class(signal):

    if "Strong Bullish" in signal:
        return "strong-bullish"

    if signal == "Bullish":
        return "bullish"

    if signal == "Neutral":
        return "neutral"

    if signal == "Bearish":
        return "bearish"

    return "strong-bearish"


def signal_badge(signal):

    css_class = signal_color_class(
        signal
    )

    st.markdown(
        f"""
        <div class="signal-badge {css_class}">
            {signal}
        </div>
        """,
        unsafe_allow_html=True,
    )


def probability_bars(
    probabilities: dict,
):

    for label, value in probabilities.items():

        st.progress(
            float(value),
            text=(
                f"{label} · "
                f"{value * 100:.1f}%"
            ),
        )


def stock_card(
    ticker,
    quote,
    prediction=None,
):

    price = quote.get(
        "price"
    )

    change = quote.get(
        "change_pct"
    )

    price_text = (
        f"${price:,.2f}"
        if price is not None
        else "—"
    )

    change_text = (
        f"{change:+.2f}%"
        if change is not None
        else "—"
    )

    st.markdown(
        f"""
        <div class="stock-card">
            <div class="stock-symbol">
                {ticker}
            </div>
            <div class="stock-price">
                {price_text}
            </div>
            <div class="stock-change">
                {change_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if prediction:

        st.caption(
            f"{prediction['signal']} · "
            f"{prediction['probability'] * 100:.0f}% "
            f"model probability · "
            f"{prediction['reliability'] * 100:.0f}% "
            f"reliability"
        )
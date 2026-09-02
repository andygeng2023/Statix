import streamlit as st
import plotly.graph_objects as go

from src.data.market import get_stock_data
from src.models.features import create_features
from src.models.ensemble import train_and_predict
from src.models.backtest import run_backtest

from src.storage.database import (
    add_to_watchlist,
    remove_from_watchlist,
    is_watched,
)


st.title("Prediction")

ticker = st.session_state.get(
    "selected_ticker",
    "AAPL",
)

ticker = st.text_input(
    "Ticker",
    value=ticker,
).upper().strip()


if not ticker:
    st.stop()


tab_overview, tab_prediction, tab_chart, tab_backtest = st.tabs(
    [
        "Overview",
        "Prediction",
        "Chart",
        "Backtest",
    ]
)


with st.status(
    f"Preparing {ticker}...",
    expanded=True,
) as status:

    st.write("Downloading historical market data...")

    data = get_stock_data(
        ticker,
        period="2y",
    )

    st.write("Downloading market context...")

    market = get_stock_data(
        "SPY",
        period="2y",
    )

    st.write("Building technical indicators...")

    features, feature_columns = create_features(
        data,
        market,
    )

    st.write(
        "Training ensemble prediction models..."
    )

    prediction = train_and_predict(
        features,
        feature_columns,
    )

    status.update(
        label=f"{ticker} analysis complete",
        state="complete",
        expanded=False,
    )


with tab_overview:

    latest_price = float(
        data["Close"].iloc[-1]
    )

    previous_price = float(
        data["Close"].iloc[-2]
    )

    change = (
        latest_price - previous_price
    ) / previous_price

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Price",
        f"${latest_price:,.2f}",
    )

    c2.metric(
        "Daily Change",
        f"{change * 100:+.2f}%",
    )

    c3.metric(
        "Up Probability",
        f"{prediction['probability_up'] * 100:.1f}%",
    )

    c4.metric(
        "Model Accuracy",
        f"{prediction['test_accuracy'] * 100:.1f}%",
    )

    st.divider()

    if prediction["direction"] == "Bullish":
        st.success(
            "Statix currently classifies the setup as Bullish."
        )

    elif prediction["direction"] == "Bearish":
        st.error(
            "Statix currently classifies the setup as Bearish."
        )

    else:
        st.warning(
            "Statix currently classifies the setup as Neutral."
        )

    st.write(
        f"Estimated 5-day return: "
        f"**{prediction['expected_return'] * 100:+.2f}%**"
    )

    st.write(
        f"Model confidence: "
        f"**{prediction['confidence'] * 100:.1f}%**"
    )

    if is_watched(ticker):

        if st.button(
            "Remove from Watchlist"
        ):
            remove_from_watchlist(ticker)
            st.rerun()

    else:

        if st.button(
            "Add to Watchlist"
        ):
            add_to_watchlist(ticker)
            st.rerun()


with tab_prediction:

    st.subheader("Prediction")

    probability_up = (
        prediction["probability_up"]
    )

    st.progress(
        probability_up,
        text=(
            f"Probability of positive "
            f"5-day return: "
            f"{probability_up * 100:.1f}%"
        ),
    )

    st.metric(
        "Expected 5-Day Return",
        f"{prediction['expected_return'] * 100:+.2f}%",
    )

    st.caption(
        "This is a statistical estimate, not a guaranteed future price."
    )

    st.divider()

    st.subheader("Model ensemble")

    model_cols = st.columns(3)

    model_cols[0].metric(
        "Gradient Boosting",
        "40% weight",
    )

    model_cols[1].metric(
        "Random Forest",
        "35% weight",
    )

    model_cols[2].metric(
        "Logistic Regression",
        "25% weight",
    )


with tab_chart:

    st.subheader("Price History")

    chart = go.Figure()

    chart.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name=ticker,
        )
    )

    chart.update_layout(
        height=650,
        xaxis_rangeslider_visible=False,
    )

    st.plotly_chart(
        chart,
        use_container_width=True,
    )


with tab_backtest:

    st.subheader("Historical Backtest")

    st.caption(
        "The backtest evaluates the model on historical data. "
        "Past performance does not guarantee future results."
    )

    if st.button(
        "Run Detailed Backtest"
    ):

        with st.status(
            "Running backtest...",
            expanded=True,
        ) as status:

            st.write(
                "Preparing historical dataset..."
            )

            st.write(
                "Training models on earlier observations..."
            )

            results = run_backtest(
                features,
                feature_columns,
            )

            st.write(
                "Calculating performance metrics..."
            )

            status.update(
                label="Backtest complete",
                state="complete",
                expanded=False,
            )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Accuracy",
            f"{results['accuracy'] * 100:.1f}%",
        )

        c2.metric(
            "Precision",
            f"{results['precision'] * 100:.1f}%",
        )

        c3.metric(
            "Recall",
            f"{results['recall'] * 100:.1f}%",
        )

        c4.metric(
            "Test Samples",
            results["samples"],
        )
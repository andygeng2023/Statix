import streamlit as st
import plotly.graph_objects as go

from src.data.market import (
    get_stock_data,
)

from src.models.features import (
    create_features,
)

from src.models.ensemble import (
    MODEL_VERSION,
    train_and_predict,
)

from src.models.backtest import (
    run_backtest,
)

from src.storage.database import (
    add_to_watchlist,
    get_cached_prediction,
    is_watched,
    remove_from_watchlist,
    save_prediction_history,
    save_viewed_prediction,
)

from src.ui.components import (
    show_prediction_metrics,
)


st.title("Prediction")


# -------------------------
# Selected ticker
# -------------------------

ticker = st.session_state.get(
    "selected_ticker"
)


if not ticker:

    st.info(
        "Search for a stock first."
    )

    if st.button(
        "Search up a stock",
        type="primary",
        use_container_width=True,
    ):
        st.switch_page(
            "pages/search.py"
        )

    st.stop()


ticker = ticker.upper().strip()


if st.button(
    "Search up a different stock",
):
    st.switch_page(
        "pages/search.py"
    )


st.subheader(
    ticker
)


# -------------------------
# Tabs
# -------------------------

(
    overview_tab,
    prediction_tab,
    chart_tab,
    backtest_tab,
) = st.tabs(
    [
        "Overview",
        "Prediction",
        "Chart",
        "Backtest",
    ]
)


# -------------------------
# Download data
# -------------------------

with st.status(
    f"Loading {ticker}...",
    expanded=True,
) as status:

    st.write(
        "Loading historical market data..."
    )

    data = get_stock_data(
        ticker,
        period="2y",
    )

    market = get_stock_data(
        "SPY",
        period="2y",
    )

    latest_market_date = (
        data.index[-1].strftime(
            "%Y-%m-%d"
        )
    )

    latest_price = float(
        data["Close"].iloc[-1]
    )

    status.update(
        label="Market data loaded",
        state="complete",
        expanded=False,
    )


# -------------------------
# Database cache
# -------------------------

cached_prediction = (
    get_cached_prediction(
        ticker=ticker,
        market_date=latest_market_date,
        model_version=MODEL_VERSION,
        horizon=5,
    )
)


if cached_prediction:

    prediction = cached_prediction

    st.caption(
        "Loaded saved analysis. "
        "The model did not need to be retrained."
    )

else:

    with st.status(
        f"Analyzing {ticker}...",
        expanded=True,
    ) as status:

        st.write(
            "Calculating technical indicators..."
        )

        features, feature_columns = (
            create_features(
                data,
                market,
                horizon=5,
            )
        )

        st.write(
            "Training prediction ensemble..."
        )

        prediction = train_and_predict(
            features,
            feature_columns,
            horizon=5,
        )

        st.write(
            "Saving analysis..."
        )

        save_viewed_prediction(
            ticker=ticker,
            market_date=latest_market_date,
            price=latest_price,
            prediction=prediction,
        )

        save_prediction_history(
            ticker=ticker,
            market_date=latest_market_date,
            price=latest_price,
            prediction=prediction,
        )

        status.update(
            label="Analysis complete",
            state="complete",
            expanded=False,
        )


# -------------------------
# Overview
# -------------------------

with overview_tab:

    previous_price = float(
        data["Close"].iloc[-2]
    )

    daily_change = (
        latest_price
        - previous_price
    ) / previous_price

    c1, c2, c3, c4 = st.columns(
        4
    )

    c1.metric(
        "Price",
        f"${latest_price:,.2f}",
    )

    c2.metric(
        "Daily Change",
        f"{daily_change * 100:+.2f}%",
    )

    c3.metric(
        "Signal",
        prediction["direction"],
    )

    c4.metric(
        "Up Probability",
        (
            f"{prediction['probability_up'] * 100:.1f}%"
        ),
    )

    st.divider()

    show_prediction_metrics(
        prediction
    )

    st.divider()

    if prediction[
        "direction"
    ] == "Bullish":

        st.success(
            "Statix currently classifies "
            "the historical setup as Bullish."
        )

    elif prediction[
        "direction"
    ] == "Bearish":

        st.error(
            "Statix currently classifies "
            "the historical setup as Bearish."
        )

    else:

        st.warning(
            "Statix currently classifies "
            "the historical setup as Neutral."
        )

    st.caption(
        "This is a statistical model output, "
        "not a guaranteed future result."
    )

    if is_watched(ticker):

        if st.button(
            "Remove from Watchlist"
        ):
            remove_from_watchlist(
                ticker
            )
            st.rerun()

    else:

        if st.button(
            "Add to Watchlist"
        ):
            add_to_watchlist(
                ticker
            )
            st.rerun()


# -------------------------
# Prediction
# -------------------------

with prediction_tab:

    st.subheader(
        "Statix Prediction"
    )

    st.progress(
        prediction[
            "probability_up"
        ],
        text=(
            "Probability of a positive "
            "5-day return: "
            f"{prediction['probability_up'] * 100:.1f}%"
        ),
    )

    c1, c2 = st.columns(2)

    with c1:

        st.metric(
            "Expected 5-Day Return",
            (
                f"{prediction['expected_return'] * 100:+.2f}%"
            ),
        )

    with c2:

        st.metric(
            "Model Validation Accuracy",
            (
                f"{prediction['test_accuracy'] * 100:.1f}%"
            ),
        )

    st.divider()

    st.subheader(
        "Model Ensemble"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Gradient Boosting",
        "40%",
    )

    c2.metric(
        "Random Forest",
        "35%",
    )

    c3.metric(
        "Logistic / Ridge",
        "25%",
    )

    st.divider()

    st.caption(
        f"Model version: "
        f"{prediction['model_version']}"
    )


# -------------------------
# Chart
# -------------------------

with chart_tab:

    st.subheader(
        f"{ticker} Price History"
    )

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


# -------------------------
# Backtest
# -------------------------

with backtest_tab:

    st.subheader(
        "Historical Backtest"
    )

    st.caption(
        "Backtesting evaluates historical observations "
        "and does not guarantee future performance."
    )

    if st.button(
        "Run Detailed Backtest",
        type="primary",
    ):

        with st.status(
            "Running backtest...",
            expanded=True,
        ) as status:

            st.write(
                "Building historical features..."
            )

            features, feature_columns = (
                create_features(
                    data,
                    market,
                    horizon=5,
                )
            )

            st.write(
                "Training historical models..."
            )

            results = run_backtest(
                features,
                feature_columns,
            )

            st.write(
                "Calculating validation metrics..."
            )

            status.update(
                label="Backtest complete",
                state="complete",
                expanded=False,
            )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Direction Accuracy",
            (
                f"{results['accuracy'] * 100:.1f}%"
            ),
        )

        c2.metric(
            "Return RMSE",
            (
                f"{results['return_rmse'] * 100:.2f}%"
            ),
        )

        c3.metric(
            "Test Samples",
            results["samples"],
        )
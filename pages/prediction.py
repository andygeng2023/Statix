import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data.market import (
    get_latest_market_date,
    get_quote,
    get_stock_data,
    format_volume,
)
from src.models.backtest import (
    walk_forward_backtest,
)
from src.models.ensemble import (
    MODEL_VERSION,
    CLASS_NAMES,
    train_and_predict,
)
from src.models.features import (
    FEATURE_VERSION,
    create_features,
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
    display_class_probabilities,
    format_money,
    format_percent,
    format_probability,
    metric_grid,
    prediction_card,
)


HORIZON = 5


ticker = st.session_state.get(
    "selected_ticker"
)


if not ticker:

    st.title("Prediction")

    st.info(
        "Choose a stock from Search first."
    )

    if st.button(
        "Search for a stock",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/search.py"
        )

    st.stop()


ticker = ticker.upper().strip()


# =========================================================
# HEADER / LIVE QUOTE
# =========================================================

quote_placeholder = st.empty()


@st.fragment(run_every="20s")
def live_quote():

    quote = get_quote(ticker)

    price = quote.get("price")
    change = quote.get("change")
    change_pct = quote.get("change_pct")

    with quote_placeholder.container():

        left, middle, right = st.columns(
            [2.2, 1.5, 1]
        )

        with left:

            st.markdown(
                f'<div class="ticker-title">{ticker}</div>',
                unsafe_allow_html=True,
            )

            if price is not None:

                st.markdown(
                    f"### {format_money(price)}"
                )

                st.caption(
                    f"Day: {format_percent(change_pct)} "
                    f"({format_money(change) if change is not None else '—'})"
                )

        with middle:

            st.caption("Volume")

            st.write(
                format_volume(
                    quote.get("volume")
                )
            )

            st.caption(
                "Market quote refreshes approximately every 20 seconds."
            )

        with right:

            if st.button(
                "Refresh",
                key=f"refresh_{ticker}",
                use_container_width=True,
            ):

                st.cache_data.clear()
                st.rerun()


live_quote()


if st.button(
    "Search up a different stock"
):

    st.switch_page(
        "pages/search.py"
    )


st.divider()


# =========================================================
# HISTORICAL DATA
# =========================================================

with st.status(
    "Loading market history...",
    expanded=False,
) as status:

    stock_df = get_stock_data(
        ticker,
        period="5y",
        interval="1d",
    )

    market_df = get_stock_data(
        "SPY",
        period="5y",
        interval="1d",
    )

    status.update(
        label="Market history loaded",
        state="complete",
    )


if stock_df.empty:

    st.error(
        f"No historical data found for {ticker}."
    )

    st.stop()


market_date = get_latest_market_date(
    stock_df
)

latest_price = float(
    stock_df["Close"].iloc[-1]
)


st.caption(
    f"Latest completed market session: {market_date}"
)


# =========================================================
# WATCHLIST
# =========================================================

watched = is_watched(ticker)

if watched:

    if st.button(
        "★ Remove from watchlist"
    ):

        remove_from_watchlist(ticker)
        st.rerun()

else:

    if st.button(
        "☆ Add to watchlist"
    ):

        add_to_watchlist(ticker)
        st.rerun()


# =========================================================
# CACHED PREDICTION
# =========================================================

cached = get_cached_prediction(
    ticker=ticker,
    market_date=market_date,
    model_version=MODEL_VERSION,
    horizon=HORIZON,
)


if cached:

    prediction = cached

    prediction["cached"] = True

    st.success(
        "Loaded saved analysis. Statix did not retrain the model."
    )

else:

    st.info(
        "New market session detected. Building a fresh model analysis."
    )

    with st.status(
        "Building V6 model...",
        expanded=True,
    ) as status:

        training_df, latest_df, feature_columns = (
            create_features(
                stock_df,
                market_df,
                horizon=HORIZON,
            )
        )

        st.write(
            f"Feature rows: {len(training_df):,}"
        )

        st.write(
            f"Features: {len(feature_columns)}"
        )

        if len(training_df) < 220:

            status.update(
                label="Not enough usable history",
                state="error",
            )

            st.error(
                "This stock does not currently have enough usable historical data for the V6 model."
            )

            st.stop()

        prediction = train_and_predict(
            training_df,
            latest_df,
            feature_columns,
        )

        prediction["cached"] = False

        save_viewed_prediction(
            ticker=ticker,
            market_date=market_date,
            price=latest_price,
            prediction=prediction,
            model_version=MODEL_VERSION,
            horizon=HORIZON,
        )

        save_prediction_history(
            ticker=ticker,
            market_date=market_date,
            price=latest_price,
            prediction=prediction,
            model_version=MODEL_VERSION,
            horizon=HORIZON,
        )

        status.update(
            label="V6 model complete",
            state="complete",
        )


# =========================================================
# TABS
# =========================================================

tabs = st.tabs(
    [
        "Overview",
        "Prediction",
        "Chart",
        "Model",
        "Backtest",
    ]
)


# =========================================================
# OVERVIEW
# =========================================================

with tabs[0]:

    st.subheader("Overview")

    prediction_card(
        prediction
    )

    st.divider()

    metric_grid(
        [
            {
                "label": "Price",
                "value": format_money(
                    latest_price
                ),
            },
            {
                "label": "5D Expected",
                "value": format_percent(
                    prediction.get(
                        "expected_return"
                    )
                ),
            },
            {
                "label": "Validation Accuracy",
                "value": format_probability(
                    prediction.get(
                        "accuracy"
                    )
                ),
            },
            {
                "label": "Return RMSE",
                "value": format_percent(
                    prediction.get(
                        "rmse"
                    )
                ),
            },
        ]
    )

    st.divider()

    st.subheader(
        "Signal distribution"
    )

    display_class_probabilities(
        prediction
    )


# =========================================================
# PREDICTION
# =========================================================

with tabs[1]:

    st.subheader(
        "Model prediction"
    )

    direction = prediction.get(
        "direction",
        "Neutral",
    )

    probability_up = prediction.get(
        "probability_up"
    )

    expected_return = prediction.get(
        "expected_return"
    )

    confidence = prediction.get(
        "confidence"
    )

    if direction == "Bullish":

        st.success(
            f"Model signal: {direction}"
        )

    elif direction == "Bearish":

        st.error(
            f"Model signal: {direction}"
        )

    else:

        st.warning(
            f"Model signal: {direction}"
        )

    st.write(
        "The model combines price structure, momentum, "
        "volatility, volume, technical indicators, and "
        "market-relative information."
    )

    st.divider()

    metric_grid(
        [
            {
                "label": "Probability Up",
                "value": format_probability(
                    probability_up
                ),
            },
            {
                "label": "Probability Down",
                "value": format_probability(
                    prediction.get(
                        "probability_down"
                    )
                ),
            },
            {
                "label": "Expected 5D Return",
                "value": format_percent(
                    expected_return
                ),
            },
            {
                "label": "Confidence",
                "value": format_probability(
                    confidence
                ),
            },
        ]
    )

    st.divider()

    st.subheader(
        "Model agreement"
    )

    agreement = prediction.get(
        "agreement"
    )

    st.progress(
        float(agreement or 0)
    )

    st.caption(
        f"Agreement: {format_probability(agreement)}"
    )

    st.write(
        "Agreement measures how closely the independent "
        "models align on the directional probability."
    )


# =========================================================
# CHART
# =========================================================

with tabs[2]:

    st.subheader(
        "Price history"
    )

    period = st.selectbox(
        "Timeframe",
        [
            "3mo",
            "6mo",
            "1y",
            "2y",
            "5y",
        ],
        index=2,
    )

    chart_df = get_stock_data(
        ticker,
        period=period,
        interval="1d",
    )

    if chart_df.empty:

        st.warning(
            "Chart data unavailable."
        )

    else:

        chart = go.Figure()

        chart.add_trace(
            go.Candlestick(
                x=chart_df.index,
                open=chart_df["Open"],
                high=chart_df["High"],
                low=chart_df["Low"],
                close=chart_df["Close"],
                name="Price",
            )
        )

        chart_df["MA20"] = (
            chart_df["Close"]
            .rolling(20)
            .mean()
        )

        chart_df["MA50"] = (
            chart_df["Close"]
            .rolling(50)
            .mean()
        )

        chart_df["MA200"] = (
            chart_df["Close"]
            .rolling(200)
            .mean()
        )

        for ma in [
            "MA20",
            "MA50",
            "MA200",
        ]:

            chart.add_trace(
                go.Scatter(
                    x=chart_df.index,
                    y=chart_df[ma],
                    mode="lines",
                    name=ma,
                )
            )

        chart.update_layout(
            height=600,
            xaxis_rangeslider_visible=False,
            margin=dict(
                l=10,
                r=10,
                t=30,
                b=10,
            ),
        )

        st.plotly_chart(
            chart,
            use_container_width=True,
        )

        st.subheader("Volume")

        volume = chart_df[
            ["Volume"]
        ].tail(180)

        st.bar_chart(
            volume,
            height=220,
        )


# =========================================================
# MODEL
# =========================================================

with tabs[3]:

    st.subheader(
        "Model information"
    )

    metric_grid(
        [
            {
                "label": "Model",
                "value": "V6 Ensemble",
            },
            {
                "label": "Feature Version",
                "value": FEATURE_VERSION,
            },
            {
                "label": "Training Rows",
                "value": f'{prediction.get("training_rows", "—"):,}',
            },
            {
                "label": "Validation Rows",
                "value": f'{prediction.get("validation_rows", "—"):,}',
            },
        ]
    )

    st.divider()

    st.write(
        "### Model stack"
    )

    st.write(
        """
        **Gradient Boosting**  
        Captures nonlinear relationships between technical and market features.

        **Random Forest**  
        Provides a different tree-based view of the same feature space.

        **Logistic Regression**  
        Provides a simpler linear baseline and improves ensemble diversity.

        **Regression ensemble**  
        Independently estimates the expected future return.
        """
    )

    st.divider()

    st.write(
        "### Validation"
    )

    metric_grid(
        [
            {
                "label": "Ensemble Accuracy",
                "value": format_probability(
                    prediction.get(
                        "accuracy"
                    )
                ),
            },
            {
                "label": "Baseline",
                "value": format_probability(
                    prediction.get(
                        "baseline_accuracy"
                    )
                ),
            },
            {
                "label": "Improvement",
                "value": format_percent(
                    prediction.get(
                        "improvement"
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


# =========================================================
# BACKTEST
# =========================================================

with tabs[4]:

    st.subheader(
        "Walk-forward backtest"
    )

    with st.spinner(
        "Running historical validation..."
    ):

        training_df, latest_df, feature_columns = (
            create_features(
                stock_df,
                market_df,
                horizon=HORIZON,
            )
        )

        backtest = walk_forward_backtest(
            training_df,
            feature_columns,
        )

    accuracy = backtest.get(
        "accuracy"
    )

    baseline = backtest.get(
        "baseline"
    )

    if accuracy is None:

        st.warning(
            "Not enough history to run the walk-forward backtest."
        )

    else:

        metric_grid(
            [
                {
                    "label": "Walk-forward Accuracy",
                    "value": format_probability(
                        accuracy
                    ),
                },
                {
                    "label": "Baseline",
                    "value": format_probability(
                        baseline
                    ),
                },
                {
                    "label": "Improvement",
                    "value": format_percent(
                        accuracy - baseline
                    ),
                },
            ]
        )

        results = backtest[
            "predictions"
        ]

        if not results.empty:

            results = results.copy()

            results["Actual"] = results[
                "actual"
            ].map(CLASS_NAMES)

            results["Predicted"] = results[
                "predicted"
            ].map(CLASS_NAMES)

            st.dataframe(
                results[
                    [
                        "date",
                        "Actual",
                        "Predicted",
                    ]
                ].tail(100),
                use_container_width=True,
                hide_index=True,
            )


st.caption(
    f"Statix {MODEL_VERSION} • "
    f"Feature set {FEATURE_VERSION} • "
    f"{time.strftime('%Y-%m-%d %H:%M:%S')}"
)
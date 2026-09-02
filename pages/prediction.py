import time

import plotly.graph_objects as go
import streamlit as st

from src.data.market import (
    format_volume,
    get_latest_market_date,
    get_quote,
    get_stock_data,
)
from src.models.backtest import (
    walk_forward_backtest,
)
from src.models.ensemble import (
    CLASS_NAMES,
    MODEL_VERSION,
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
        "Search for a stock to begin."
    )

    if st.button(
        "Search stocks",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/search.py"
        )

    st.stop()


ticker = ticker.upper().strip()


# =========================================================
# LIVE HEADER
# =========================================================

header = st.empty()


@st.fragment(run_every="20s")
def live_header():

    quote = get_quote(
        ticker
    )

    with header.container():

        c1, c2, c3 = st.columns(
            [2.3, 1.4, 1]
        )

        with c1:

            st.markdown(
                f'<div class="ticker-title">{ticker}</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f"### {format_money(quote.get('price'))}"
            )

            st.caption(
                "Today: "
                + format_percent(
                    quote.get(
                        "change_pct"
                    )
                )
            )

        with c2:

            st.caption(
                "Volume"
            )

            st.write(
                format_volume(
                    quote.get(
                        "volume"
                    )
                )
            )

            st.caption(
                "Quote refresh ≈ 20 sec"
            )

        with c3:

            if st.button(
                "Refresh",
                key=f"quote_refresh_{ticker}",
                use_container_width=True,
            ):

                st.cache_data.clear()
                st.rerun()


live_header()


if st.button(
    "Search a different stock"
):

    st.switch_page(
        "pages/search.py"
    )


st.divider()


# =========================================================
# HISTORY
# =========================================================

with st.status(
    "Loading 5-year market history...",
    expanded=False,
) as status:

    stock_df = get_stock_data(
        ticker,
        period="5y",
    )

    market_df = get_stock_data(
        "SPY",
        period="5y",
    )

    status.update(
        label="Historical data ready",
        state="complete",
    )


if stock_df.empty:

    st.error(
        f"No historical data is available for {ticker}."
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

if is_watched(ticker):

    if st.button(
        "★ Remove from watchlist"
    ):

        remove_from_watchlist(
            ticker
        )

        st.rerun()

else:

    if st.button(
        "☆ Add to watchlist"
    ):

        add_to_watchlist(
            ticker
        )

        st.rerun()


# =========================================================
# CACHE
# =========================================================

prediction = get_cached_prediction(
    ticker=ticker,
    market_date=market_date,
    model_version=MODEL_VERSION,
    horizon=HORIZON,
)


if prediction:

    prediction["cached"] = True

    st.success(
        "Loaded saved V6.1 analysis. No model retraining was needed."
    )

else:

    st.info(
        "New market session detected. Building the model once and saving the result."
    )

    with st.status(
        "Training V6.1 ensemble...",
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
            f"Historical sessions: {len(stock_df):,}"
        )

        st.write(
            f"Usable training rows: {len(training_df):,}"
        )

        st.write(
            f"Features: {len(feature_columns)}"
        )

        if len(training_df) < 220:

            status.update(
                label="Insufficient model history",
                state="error",
            )

            st.error(
                "This security does not have enough usable historical data for the V6.1 model."
            )

            st.stop()

        try:

            prediction = train_and_predict(
                training_df,
                latest_df,
                feature_columns,
            )

        except ValueError as error:

            status.update(
                label="Model could not train",
                state="error",
            )

            st.error(
                str(error)
            )

            st.stop()

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
            label="V6.1 analysis complete",
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

    prediction_card(
        prediction
    )

    st.divider()

    metric_grid(
        [
            {
                "label": "Current Price",
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
        "V6.1 prediction"
    )

    direction = prediction.get(
        "direction",
        "Neutral",
    )

    if direction == "Bullish":

        st.success(
            "Model signal: Bullish"
        )

    elif direction == "Bearish":

        st.error(
            "Model signal: Bearish"
        )

    else:

        st.warning(
            "Model signal: Neutral"
        )

    st.write(
        "The ensemble combines momentum, trend, volatility, "
        "volume, price structure, technical indicators, and "
        "market-relative features."
    )

    st.divider()

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
                "label": "Probability Down",
                "value": format_probability(
                    prediction.get(
                        "probability_down"
                    )
                ),
            },
            {
                "label": "Expected 5D",
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
        ]
    )

    st.divider()

    st.subheader(
        "Model agreement"
    )

    agreement = float(
        prediction.get(
            "agreement",
            0,
        )
    )

    st.progress(
        agreement
    )

    st.caption(
        format_probability(
            agreement
        )
        + " agreement across the model ensemble"
    )


# =========================================================
# CHART
# =========================================================

with tabs[2]:

    st.subheader(
        "Price and trend"
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
    )

    if chart_df.empty:

        st.warning(
            "Chart data unavailable."
        )

    else:

        chart_df = chart_df.copy()

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

        fig = go.Figure()

        fig.add_trace(
            go.Candlestick(
                x=chart_df.index,
                open=chart_df["Open"],
                high=chart_df["High"],
                low=chart_df["Low"],
                close=chart_df["Close"],
                name="Price",
            )
        )

        for column in [
            "MA20",
            "MA50",
            "MA200",
        ]:

            fig.add_trace(
                go.Scatter(
                    x=chart_df.index,
                    y=chart_df[column],
                    mode="lines",
                    name=column,
                )
            )

        fig.update_layout(
            height=600,
            xaxis_rangeslider_visible=False,
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.subheader(
            "Volume"
        )

        st.bar_chart(
            chart_df[
                ["Volume"]
            ].tail(180),
            height=220,
        )


# =========================================================
# MODEL
# =========================================================

with tabs[3]:

    st.subheader(
        "Model architecture"
    )

    metric_grid(
        [
            {
                "label": "Model",
                "value": "V6.1 Ensemble",
            },
            {
                "label": "Features",
                "value": FEATURE_VERSION,
            },
            {
                "label": "Training Rows",
                "value": f'{prediction.get("training_rows", 0):,}',
            },
            {
                "label": "Validation Rows",
                "value": f'{prediction.get("validation_rows", 0):,}',
            },
        ]
    )

    st.divider()

    st.write(
        """
        **HistGradientBoosting**  
        Nonlinear gradient-boosted decision trees.

        **Random Forest**  
        Independent randomized tree ensemble.

        **Logistic Regression**  
        Scaled linear model that adds diversity to the ensemble.

        **Return ensemble**  
        Separate regressors estimate the magnitude of the future return.
        """
    )

    st.divider()

    st.subheader(
        "Validation quality"
    )

    metric_grid(
        [
            {
                "label": "Accuracy",
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

    training_df, latest_df, feature_columns = (
        create_features(
            stock_df,
            market_df,
            horizon=HORIZON,
        )
    )

    with st.spinner(
        "Testing the model through historical periods..."
    ):

        result = walk_forward_backtest(
            training_df,
            feature_columns,
        )

    if result[
        "accuracy"
    ] is None:

        st.warning(
            "Not enough history for the walk-forward test."
        )

    else:

        metric_grid(
            [
                {
                    "label": "Walk-forward Accuracy",
                    "value": format_probability(
                        result[
                            "accuracy"
                        ]
                    ),
                },
                {
                    "label": "Baseline",
                    "value": format_probability(
                        result[
                            "baseline"
                        ]
                    ),
                },
                {
                    "label": "Improvement",
                    "value": format_percent(
                        result[
                            "accuracy"
                        ]
                        - result[
                            "baseline"
                        ]
                    ),
                },
            ]
        )

        results = result[
            "predictions"
        ]

        if not results.empty:

            results = results.copy()

            results["Actual"] = (
                results["actual"]
                .map(CLASS_NAMES)
            )

            results["Predicted"] = (
                results["predicted"]
                .map(CLASS_NAMES)
            )

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
    f"{FEATURE_VERSION} • "
    f"{time.strftime('%Y-%m-%d %H:%M:%S')}"
)
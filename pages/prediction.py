from __future__ import annotations

import time

import plotly.graph_objects as go
import streamlit as st

from src.data.market import (
    get_quote,
    get_stock_data,
    clear_market_cache,
)
from src.models.features import (
    FEATURE_VERSION,
    create_features,
)
from src.models.ensemble import (
    CLASS_NAMES,
    MODEL_VERSION,
    train_and_predict,
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
    format_confidence,
    format_money,
    format_percent,
    format_probability,
    inject_css,
    page_header,
)


inject_css()


HORIZON = 5


if "selected_ticker" not in st.session_state:
    st.session_state["selected_ticker"] = None


ticker = st.session_state.get(
    "selected_ticker"
)


if not ticker:
    page_header(
        "Prediction",
        "Select a stock from Search to begin.",
    )

    if st.button(
        "Search for a stock",
        use_container_width=True,
    ):
        st.switch_page("pages/search.py")

    st.stop()


ticker = ticker.upper().strip()


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

top_left, top_right = st.columns(
    [5, 1]
)

with top_left:
    page_header(
        ticker,
        "Statix model analysis",
    )

with top_right:
    if st.button(
        "Search another",
        use_container_width=True,
    ):
        st.switch_page("pages/search.py")


# ---------------------------------------------------------
# Quote
# ---------------------------------------------------------

@st.fragment(run_every="20s")
def live_quote():

    quote = get_quote(ticker)

    price = quote.get("price")
    change = quote.get("change")
    change_pct = quote.get("change_pct")

    cols = st.columns(4)

    with cols[0]:
        st.metric(
            "Price",
            format_money(price),
        )

    with cols[1]:
        st.metric(
            "Daily change",
            format_money(change),
            (
                format_percent(change_pct)
                if change_pct is not None
                else None
            ),
        )

    with cols[2]:
        volume = quote.get(
            "volume"
        )

        if volume is None:
            value = "—"
        else:
            value = f"{volume:,.0f}"

        st.metric(
            "Volume",
            value,
        )

    with cols[3]:
        elapsed = max(
            0,
            int(
                time.time()
                - quote.get(
                    "updated_at",
                    time.time(),
                )
            ),
        )

        st.metric(
            "Quote age",
            f"{elapsed}s",
        )

    st.caption(
        "Market quotes may be delayed depending on the data source. "
        "Refreshing this area does not retrain the prediction model."
    )


live_quote()


# ---------------------------------------------------------
# Historical data
# ---------------------------------------------------------

with st.status(
    "Loading historical market data...",
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

    if stock_df.empty:
        status.update(
            label="Could not load market data.",
            state="error",
        )
        st.stop()

    status.update(
        label="Historical data loaded.",
        state="complete",
    )


latest_market_date = (
    stock_df.index[-1]
)

market_date = str(
    latest_market_date.date()
)

latest_price = float(
    stock_df["close"].iloc[-1]
)


# ---------------------------------------------------------
# Cached prediction
# ---------------------------------------------------------

cached = get_cached_prediction(
    ticker=ticker,
    market_date=market_date,
    model_version=MODEL_VERSION,
    feature_version=FEATURE_VERSION,
    horizon=HORIZON,
)


if cached is not None:

    result = cached

    st.success(
        "Loaded saved analysis. "
        "Statix did not retrain the model."
    )

else:

    with st.status(
        "Building features and training Statix...",
        expanded=False,
    ) as status:

        try:
            (
                training_df,
                latest_df,
                feature_columns,
            ) = create_features(
                stock_df,
                market_df,
                horizon=HORIZON,
            )

            if len(training_df) < 250:
                status.update(
                    label="Not enough usable history.",
                    state="error",
                )

                st.error(
                    f"Statix found only "
                    f"{len(training_df)} usable training rows. "
                    f"At least 250 are required."
                )

                st.stop()

            result = train_and_predict(
                training_df,
                latest_df,
                feature_columns,
            )

            result["ticker"] = ticker
            result["market_date"] = market_date
            result["price"] = latest_price
            result["feature_version"] = (
                FEATURE_VERSION
            )
            result["horizon"] = HORIZON

            save_viewed_prediction(
                ticker,
                result,
            )

            save_prediction_history(
                ticker,
                result,
            )

            status.update(
                label="Prediction generated.",
                state="complete",
            )

        except Exception as exc:
            status.update(
                label="Prediction failed.",
                state="error",
            )

            st.error(
                "Statix could not generate this prediction."
            )

            st.exception(exc)
            st.stop()


# ---------------------------------------------------------
# Main prediction
# ---------------------------------------------------------

signal = result.get(
    "signal",
    "Neutral",
)

probability_up = result.get(
    "probability_up"
)

expected_return = result.get(
    "expected_return"
)

confidence = result.get(
    "confidence"
)

st.divider()

metric_cols = st.columns(4)

with metric_cols[0]:
    st.metric(
        "Model signal",
        signal,
    )

with metric_cols[1]:
    st.metric(
        "Probability up",
        format_probability(
            probability_up
        ),
    )

with metric_cols[2]:
    st.metric(
        "Expected 5D return",
        format_percent(
            expected_return * 100
            if expected_return is not None
            else None
        ),
    )

with metric_cols[3]:
    st.metric(
        "Model confidence",
        format_confidence(
            confidence
        ),
    )


st.caption(
    "This is a model output, not a guarantee or a recommendation."
)


# ---------------------------------------------------------
# Watchlist
# ---------------------------------------------------------

if is_watched(ticker):
    if st.button(
        "Remove from watchlist",
    ):
        remove_from_watchlist(ticker)
        st.rerun()
else:
    if st.button(
        "Add to watchlist",
    ):
        add_to_watchlist(ticker)
        st.rerun()


# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------

tab_overview, tab_prediction, tab_chart, tab_model = st.tabs(
    [
        "Overview",
        "Prediction",
        "Chart",
        "Model",
    ]
)


with tab_overview:

    st.subheader("Market context")

    cols = st.columns(3)

    with cols[0]:
        st.metric(
            "Latest price",
            format_money(
                latest_price
            ),
        )

    with cols[1]:
        st.metric(
            "Market session",
            market_date,
        )

    with cols[2]:
        st.metric(
            "Training rows",
            f"{result.get('training_rows', 0):,}",
        )


with tab_prediction:

    st.subheader(
        "Class probabilities"
    )

    class_probabilities = result.get(
        "class_probabilities",
        {},
    )

    for class_name in CLASS_NAMES:

        probability = class_probabilities.get(
            class_name,
            0,
        )

        st.progress(
            min(
                1.0,
                max(
                    0.0,
                    float(probability),
                ),
            ),
            text=(
                f"{class_name}: "
                f"{probability * 100:.1f}%"
            ),
        )


with tab_chart:

    st.subheader(
        "Price history"
    )

    chart_df = stock_df.tail(365).copy()

    chart_df["MA20"] = (
        chart_df["close"]
        .rolling(20)
        .mean()
    )

    chart_df["MA50"] = (
        chart_df["close"]
        .rolling(50)
        .mean()
    )

    chart_df["MA200"] = (
        chart_df["close"]
        .rolling(200)
        .mean()
    )

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=chart_df.index,
            open=chart_df["open"],
            high=chart_df["high"],
            low=chart_df["low"],
            close=chart_df["close"],
            name=ticker,
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


with tab_model:

    st.subheader(
        "Model information"
    )

    model_cols = st.columns(4)

    with model_cols[0]:
        st.metric(
            "Validation accuracy",
            format_percent(
                (
                    result.get(
                        "validation_accuracy"
                    )
                    * 100
                    if result.get(
                        "validation_accuracy"
                    ) is not None
                    else None
                )
            ),
        )

    with model_cols[1]:
        st.metric(
            "Baseline",
            format_percent(
                (
                    result.get(
                        "baseline_accuracy"
                    )
                    * 100
                    if result.get(
                        "baseline_accuracy"
                    ) is not None
                    else None
                )
            ),
        )

    with model_cols[2]:
        st.metric(
            "Model agreement",
            format_confidence(
                result.get(
                    "model_agreement"
                )
            ),
        )

    with model_cols[3]:
        st.metric(
            "Features",
            str(
                result.get(
                    "feature_count",
                    "—",
                )
            ),
        )

    st.write(
        f"Model version: `{result.get('model_version', MODEL_VERSION)}`"
    )

    st.write(
        f"Feature version: `{result.get('feature_version', FEATURE_VERSION)}`"
    )

    st.write(
        f"Walk-forward folds: "
        f"{result.get('validation_folds', 0)}"
    )

    st.write(
        f"Training rows: "
        f"{result.get('training_rows', 0):,}"
    )

    st.write(
        f"Return RMSE: "
        f"{result.get('rmse', 0):.4f}"
    )
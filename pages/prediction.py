from __future__ import annotations

import streamlit as st

from src.data.market import (
    get_stock_data,
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
    save_prediction_cache,
    save_prediction_history,
    save_viewed_prediction,
)

from src.ui.components import (
    format_confidence,
    format_percent,
    format_probability,
    inject_css,
    page_header,
)


inject_css()


HORIZON = 5


if "selected_ticker" not in st.session_state:

    st.session_state[
        "selected_ticker"
    ] = None


ticker = str(
    st.session_state.get(
        "selected_ticker"
    )
    or ""
).strip().upper()


if not ticker:

    page_header(
        "Prediction",
        "Select a stock first.",
    )

    if st.button(
        "Search stocks",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/search.py"
        )

    st.stop()


page_header(
    ticker,
    "Statix 5-session model prediction",
)


if st.button(
    "Back to stock overview"
):

    st.switch_page(
        "pages/stock.py"
    )


# Historical data is cached separately.
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

    st.error(
        "Historical data could not be loaded."
    )

    st.stop()


market_date = str(
    stock_df.index[-1].date()
)


price = float(
    stock_df[
        "close"
    ].iloc[-1]
)


# ---------------------------------------------------------
# Shared prediction cache
# ---------------------------------------------------------

cached = get_cached_prediction(
    ticker=ticker,
    market_date=market_date,
    model_version=MODEL_VERSION,
    feature_version=FEATURE_VERSION,
    horizon=HORIZON,
)


if cached:

    result = cached

    st.success(
        f"Using saved prediction for {market_date}."
    )

else:

    st.info(
        "The model does not run automatically. "
        "Generate it only when you need the prediction."
    )

    if not st.button(
        "Generate 5D prediction",
        type="primary",
        use_container_width=True,
    ):

        st.stop()

    progress = st.progress(
        0,
        text="Preparing market features...",
    )

    try:

        progress.progress(
            20,
            text="Building technical features...",
        )

        (
            training_df,
            latest_df,
            feature_columns,
        ) = create_features(
            stock_df=stock_df,
            market_df=market_df,
            horizon=HORIZON,
        )

        progress.progress(
            55,
            text="Training or loading the fast model...",
        )

        result = train_and_predict(
            training_df=training_df,
            latest_df=latest_df,
            feature_columns=feature_columns,
            ticker=ticker,
            market_date=market_date,
            validate=False,
        )

        progress.progress(
            85,
            text="Saving prediction...",
        )

        result.update(
            {
                "ticker": ticker,
                "market_date": market_date,
                "price": price,
                "feature_version": FEATURE_VERSION,
                "horizon": HORIZON,
            }
        )

        save_prediction_cache(
            ticker,
            result,
        )

        save_viewed_prediction(
            ticker,
            result,
        )

        save_prediction_history(
            ticker,
            result,
        )

        progress.progress(
            100,
            text="Prediction ready.",
        )

        st.success(
            "Prediction generated."
        )

    except Exception as exc:

        progress.empty()

        st.error(
            "Statix could not generate the prediction."
        )

        st.exception(
            exc
        )

        st.stop()


# ---------------------------------------------------------
# Results
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

st.subheader(
    "Statix prediction"
)

st.markdown(
    f"## {signal}"
)


cols = st.columns(3)


with cols[0]:

    st.metric(
        "Probability up",
        format_probability(
            probability_up
        ),
    )


with cols[1]:

    st.metric(
        "Expected 5D return",
        format_percent(
            expected_return * 100
            if expected_return is not None
            else None
        ),
    )


with cols[2]:

    st.metric(
        "Model confidence",
        format_confidence(
            confidence
        ),
    )


st.caption(
    f"Based on market data through {market_date}. "
    "Model confidence is not a guarantee of accuracy."
)


# ---------------------------------------------------------
# Class probabilities
# ---------------------------------------------------------

st.subheader(
    "Prediction distribution"
)


probabilities = result.get(
    "class_probabilities",
    {},
)


for name in CLASS_NAMES:

    value = float(
        probabilities.get(
            name,
            0,
        )
    )

    value = max(
        0.0,
        min(
            1.0,
            value,
        ),
    )

    st.progress(
        value,
        text=(
            f"{name}: "
            f"{value * 100:.1f}%"
        ),
    )


# ---------------------------------------------------------
# Model information
# ---------------------------------------------------------

st.subheader(
    "Model details"
)


cols = st.columns(4)


with cols[0]:

    st.metric(
        "Training rows",
        f"{result.get('training_rows', 0):,}",
    )


with cols[1]:

    st.metric(
        "Features",
        result.get(
            "feature_count",
            "—",
        ),
    )


with cols[2]:

    st.metric(
        "Model agreement",
        format_confidence(
            result.get(
                "model_agreement"
            )
        ),
    )


with cols[3]:

    st.metric(
        "Validation",
        "On demand",
    )


# ---------------------------------------------------------
# Watchlist
# ---------------------------------------------------------

if is_watched(
    ticker
):

    if st.button(
        "Remove from watchlist"
    ):

        remove_from_watchlist(
            ticker
        )

        st.rerun()

else:

    if st.button(
        "Add to watchlist"
    ):

        add_to_watchlist(
            ticker
        )

        st.rerun()
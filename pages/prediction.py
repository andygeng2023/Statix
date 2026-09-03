import streamlit as st

from src.config import SETTINGS
from src.data.market import (
    get_stock_data,
)
from src.models.ensemble import (
    MODEL_VERSION,
    predict_with_model,
    train_global_model,
)
from src.models.features import (
    FEATURE_VERSION,
    create_features,
)
from src.storage.database import (
    get_cached_prediction,
    save_prediction,
)
from src.data.market import get_stock_data


ticker = (
    st.query_params.get("ticker")
    or st.session_state.get(
        "selected_ticker"
    )
    or "AAPL"
).upper().strip()


st.title(
    f"Prediction · {ticker}"
)


history = get_stock_data(
    ticker,
    "5y",
    "1d",
)

market = get_stock_data(
    "SPY",
    "5y",
    "1d",
)


if history.empty:

    st.error(
        "Unable to retrieve stock history."
    )

    st.stop()


training, latest, features = (
    create_features(
        history,
        market,
        SETTINGS.prediction_horizon,
    )
)


market_date = str(
    history.index[-1].date()
)


cached = get_cached_prediction(
    ticker,
    market_date,
    MODEL_VERSION,
)


if cached:

    result = cached

    st.success(
        "Using cached prediction for "
        f"{market_date}."
    )

else:

    try:

        with st.spinner(
            "Preparing prediction model..."
        ):

            model = train_global_model(
                training,
                tuple(features),
            )

            result = predict_with_model(
                model,
                latest,
                features,
            )

        save_prediction(
            ticker,
            market_date,
            result,
        )

    except Exception as error:

        st.error(
            "Prediction unavailable."
        )

        st.caption(
            str(error)
        )

        st.stop()


columns = st.columns(5)


columns[0].metric(
    "Signal",
    result["signal"],
)

columns[1].metric(
    "Probability",
    f"{result['probability'] * 100:.1f}%",
)

columns[2].metric(
    "Expected 5D",
    (
        f"{result['expected_return'] * 100:+.2f}%"
    ),
)

columns[3].metric(
    "Reliability",
    (
        f"{result['reliability'] * 100:.0f}%"
    ),
)

columns[4].metric(
    "Agreement",
    (
        f"{result['model_agreement'] * 100:.0f}%"
    ),
)


st.divider()


st.subheader(
    "Prediction Distribution"
)


for label, probability in (
    result["class_probabilities"]
    .items()
):

    st.progress(
        float(probability),
        text=(
            f"{label} · "
            f"{probability * 100:.1f}%"
        ),
    )


st.divider()


left, right = st.columns(2)


with left:

    st.subheader(
        "Reliability"
    )

    st.metric(
        "Model reliability",
        f"{result['reliability'] * 100:.0f}%",
    )

    st.caption(
        "This is a model-derived quality "
        "score. It is not a probability that "
        "the prediction will be correct."
    )


with right:

    st.subheader(
        "Validation"
    )

    validation = result.get(
        "validation_accuracy"
    )

    if validation is not None:

        st.metric(
            "Validation accuracy",
            f"{validation * 100:.1f}%",
        )

    else:

        st.write(
            "Not available."
        )


st.divider()


st.subheader(
    "Model Information"
)


st.write(
    f"Model version: `{MODEL_VERSION}`"
)

st.write(
    f"Feature version: `{FEATURE_VERSION}`"
)

st.write(
    f"Training rows: "
    f"{result.get('training_rows', '—')}"
)

st.write(
    f"Market date: `{market_date}`"
)


st.info(
    "Statix predictions are experimental "
    "model outputs for research. They are "
    "not guarantees and should not be treated "
    "as individualized financial advice."
)
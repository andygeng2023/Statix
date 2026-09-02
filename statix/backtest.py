from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
)

from prediction import (
    FEATURES,
    train_model,
)


def fast_backtest(df):
    model, accuracy = train_model(df)

    return {
        "accuracy": accuracy,
    }
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

import pandas as pd

from src.data.market import (
    get_stock_data,
)
from src.models.features import (
    create_features,
)
from src.models.ensemble import (
    predict_with_model,
)


def liquidity_filter(
    history: pd.DataFrame,
) -> bool:

    if history.empty:
        return False

    if len(history) < 220:
        return False

    latest = history.iloc[-1]

    price = float(
        latest["Close"]
    )

    volume = float(
        latest["Volume"]
    )

    if price < 3:
        return False

    if volume <= 0:
        return False

    average_volume = float(
        history["Volume"]
        .tail(20)
        .mean()
    )

    if average_volume <= 0:
        return False

    return True


def score_symbol(
    ticker: str,
    model,
    market_df: pd.DataFrame,
):

    try:

        ticker = ticker.upper().strip()

        history = get_stock_data(
            ticker,
            "2y",
            "1d",
        )

        if not liquidity_filter(
            history
        ):
            return None

        train, latest, features = (
            create_features(
                history,
                market_df,
                horizon=5,
            )
        )

        result = predict_with_model(
            model,
            latest,
            features,
        )

        result.update(
            {
                "ticker": ticker,
                "price": float(
                    history["Close"].iloc[-1]
                ),
                "data_rows": len(history),
            }
        )

        return result

    except Exception:
        return None


def rank_results(
    results: list[dict],
    limit: int = 25,
):

    valid = [
        result
        for result in results
        if result is not None
    ]

    valid.sort(
        key=lambda x: (
            x.get(
                "reliability",
                0,
            ),
            x.get(
                "probability",
                0,
            ),
            abs(
                x.get(
                    "expected_return",
                    0,
                )
            ),
        ),
        reverse=True,
    )

    return valid[:limit]


def scan_universe(
    tickers,
    model,
    market_df,
    max_workers: int = 8,
    limit: int = 25,
):

    symbols = list(
        dict.fromkeys(
            str(x).upper().strip()
            for x in tickers
            if x
        )
    )

    results = []

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        futures = [
            executor.submit(
                score_symbol,
                ticker,
                model,
                market_df,
            )
            for ticker in symbols
        ]

        for future in as_completed(
            futures
        ):

            try:

                result = future.result()

                if result is not None:
                    results.append(result)

            except Exception:
                continue

    return rank_results(
        results,
        limit,
    )
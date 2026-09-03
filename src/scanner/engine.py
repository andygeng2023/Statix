from concurrent.futures import ThreadPoolExecutor

from src.data.market import get_quotes
from src.data.market import get_stock_data
from src.models.inference import predict


def liquidity_filter(quotes):

    result = []

    for ticker, quote in quotes.items():

        price = quote.get("price")

        if price is None:
            continue

        if price < 2:
            continue

        result.append(ticker)

    return result


def score_one(ticker):

    try:

        df = get_stock_data(
            ticker,
            period="1y",
            interval="1d",
        )

        if df.empty:
            return None

        prediction = predict(df)

        if not prediction.get("available"):
            return None

        return {
            "ticker": ticker,
            **prediction,
        }

    except Exception:
        return None


def scan(tickers, max_results=25):

    tickers = list(
        dict.fromkeys(
            t.upper()
            for t in tickers
        )
    )

    # Stage 1: cheap quote filtering.
    quotes = get_quotes(
        tuple(tickers)
    )

    candidates = liquidity_filter(
        quotes
    )

    # Stage 2: cap expensive inference.
    # A production worker should process this
    # asynchronously in batches.
    candidates = candidates[:2000]

    results = []

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        for result in executor.map(
            score_one,
            candidates,
        ):

            if result:
                results.append(result)

    # Highest confidence first.
    results.sort(
        key=lambda x: (
            x["confidence"],
            abs(x["return_5d"]),
        ),
        reverse=True,
    )

    return results[:max_results]
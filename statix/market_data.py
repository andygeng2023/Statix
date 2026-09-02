import pandas as pd
import yfinance as yf


def get_stock_data(ticker, period="5y"):
    """
    Download historical daily stock data.

    Parameters
    ----------
    ticker : str
        Stock ticker, e.g. "AAPL"
    period : str
        yfinance period, e.g. "1y", "5y", "10y"

    Returns
    -------
    pandas.DataFrame
    """

    ticker = ticker.upper().strip()

    if not ticker:
        raise ValueError("Ticker cannot be empty.")

    data = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    if data.empty:
        raise ValueError(
            f"No data found for '{ticker}'. "
            "Check that the ticker is correct."
        )

    # Some yfinance versions return multi-level columns.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    missing = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Missing market-data columns: {missing}"
        )

    data = data[required_columns].copy()

    data = data.dropna()

    return data
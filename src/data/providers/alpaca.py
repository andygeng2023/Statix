from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

from src.config import (
    ALPACA_FEED,
    ALPACA_KEY,
    ALPACA_SECRET,
)

from src.data.providers.base import (
    MarketDataProvider,
)


class AlpacaProvider(
    MarketDataProvider
):

    BASE_URL = (
        "https://data.alpaca.markets"
    )

    def __init__(self):

        if not ALPACA_KEY or not ALPACA_SECRET:
            raise RuntimeError(
                "Alpaca credentials are missing."
            )

        self.headers = {
            "APCA-API-KEY-ID":
                ALPACA_KEY,
            "APCA-API-SECRET-KEY":
                ALPACA_SECRET,
        }

    def _get(
        self,
        path,
        params=None,
    ):

        response = requests.get(
            self.BASE_URL + path,
            headers=self.headers,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    def get_quote(
        self,
        ticker: str,
    ) -> dict:

        ticker = ticker.upper()

        data = self._get(
            f"/v2/stocks/{ticker}/bars",
            params={
                "timeframe": "1Min",
                "limit": 1,
                "feed": ALPACA_FEED,
            },
        )

        bars = data.get(
            "bars",
            [],
        )

        if not bars:
            raise ValueError(
                f"No Alpaca data for {ticker}"
            )

        bar = bars[-1]

        price = float(
            bar["c"]
        )

        return {
            "ticker": ticker,
            "price": price,
            "timestamp": bar["t"],
            "source": "Alpaca",
        }

    def get_quotes(
        self,
        tickers: list[str],
    ) -> dict[str, dict]:

        result = {}

        for ticker in tickers:

            try:
                result[ticker] = (
                    self.get_quote(
                        ticker
                    )
                )
            except Exception:
                continue

        return result

    def get_history(
        self,
        ticker: str,
        period: str = "5y",
        interval: str = "1d",
    ) -> pd.DataFrame:

        if interval == "1d":
            timeframe = "1Day"
        elif interval == "1h":
            timeframe = "1Hour"
        else:
            timeframe = "1Day"

        days = {
            "1y": 365,
            "2y": 730,
            "5y": 1825,
            "10y": 3650,
        }.get(
            period,
            1825,
        )

        start = (
            datetime.now(
                timezone.utc
            )
            - timedelta(days=days)
        )

        data = self._get(
            f"/v2/stocks/{ticker}/bars",
            params={
                "timeframe": timeframe,
                "start": start.isoformat(),
                "limit": 10_000,
                "feed": ALPACA_FEED,
            },
        )

        bars = data.get(
            "bars",
            [],
        )

        if not bars:
            return pd.DataFrame()

        rows = []

        for bar in bars:

            rows.append(
                {
                    "Open": float(
                        bar["o"]
                    ),
                    "High": float(
                        bar["h"]
                    ),
                    "Low": float(
                        bar["l"]
                    ),
                    "Close": float(
                        bar["c"]
                    ),
                    "Volume": float(
                        bar["v"]
                    ),
                    "Timestamp": bar["t"],
                }
            )

        df = pd.DataFrame(rows)

        df["Timestamp"] = pd.to_datetime(
            df["Timestamp"],
            utc=True,
        )

        df = df.set_index(
            "Timestamp"
        )

        return df.sort_index()
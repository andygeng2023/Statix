from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from .base import MarketDataProvider


class YahooProvider(MarketDataProvider):

    name = "Yahoo Finance via yfinance"

    realtime = False

    bulk_quotes = False

    def get_quote(self, ticker: str) -> dict:

        ticker = ticker.upper().strip()

        empty = {
            "ticker": ticker,
            "price": None,
            "previous_close": None,
            "change": None,
            "change_pct": None,
            "timestamp": datetime.now(timezone.utc),
            "source": self.name,
            "fresh": False,
        }

        try:
            asset = yf.Ticker(ticker)

            info = asset.fast_info

            price = info.get("last_price")

            previous = info.get("previous_close")

            if price is not None:

                price = float(price)

                previous = (
                    float(previous)
                    if previous is not None
                    else None
                )

                change = (
                    price - previous
                    if previous is not None
                    else None
                )

                change_pct = (
                    change / previous * 100
                    if previous not in (None, 0)
                    else None
                )

                return {
                    "ticker": ticker,
                    "price": price,
                    "previous_close": previous,
                    "change": change,
                    "change_pct": change_pct,
                    "timestamp": datetime.now(
                        timezone.utc
                    ),
                    "source": self.name,
                    "fresh": True,
                }

        except Exception:
            pass

        try:
            history = yf.download(
                ticker,
                period="5d",
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=False,
            )

            if history.empty:
                return empty

            if isinstance(
                history.columns,
                pd.MultiIndex,
            ):
                history.columns = (
                    history.columns
                    .get_level_values(0)
                )

            history = history.dropna(
                subset=["Close"]
            )

            if history.empty:
                return empty

            latest = history.iloc[-1]

            price = float(latest["Close"])

            previous = (
                float(history.iloc[-2]["Close"])
                if len(history) >= 2
                else None
            )

            change = (
                price - previous
                if previous is not None
                else None
            )

            change_pct = (
                change / previous * 100
                if previous not in (None, 0)
                else None
            )

            return {
                "ticker": ticker,
                "price": price,
                "previous_close": previous,
                "change": change,
                "change_pct": change_pct,
                "timestamp": datetime.now(
                    timezone.utc
                ),
                "source": self.name,
                "fresh": False,
            }

        except Exception:
            return empty

    def get_quotes(
        self,
        tickers,
    ) -> dict[str, dict]:

        symbols = [
            str(x).upper().strip()
            for x in tickers
            if x
        ]

        result = {}

        for ticker in symbols:
            result[ticker] = self.get_quote(ticker)

        return result

    def get_history(
        self,
        ticker: str,
        period: str = "5y",
        interval: str = "1d",
    ) -> pd.DataFrame:

        ticker = ticker.upper().strip()

        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if data.empty:
            return pd.DataFrame()

        if isinstance(
            data.columns,
            pd.MultiIndex,
        ):
            data.columns = (
                data.columns
                .get_level_values(0)
            )

        required = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]

        missing = [
            column
            for column in required
            if column not in data.columns
        ]

        if missing:
            return pd.DataFrame()

        data = data[required].copy()

        data = data.replace(
            [float("inf"), float("-inf")],
            pd.NA,
        )

        data = data.dropna(
            subset=["Close"]
        )

        data.index = pd.to_datetime(
            data.index
        )

        data = data.sort_index()

        return data
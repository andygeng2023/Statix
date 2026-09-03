import pandas as pd
import yfinance as yf

from src.data.providers.base import MarketDataProvider


class YahooProvider(MarketDataProvider):

    def get_quote(self, ticker: str) -> dict:
        ticker = ticker.upper().strip()

        try:
            t = yf.Ticker(ticker)
            info = t.fast_info

            price = info.get("last_price")
            previous = info.get("previous_close")

            if price is None:
                raise ValueError("No price")

            change = None
            change_pct = None

            if previous:
                change = float(price - previous)
                change_pct = float(change / previous * 100)

            return {
                "ticker": ticker,
                "price": float(price),
                "previous_close": (
                    float(previous) if previous else None
                ),
                "change": change,
                "change_pct": change_pct,
            }

        except Exception:
            history = self.get_history(
                ticker,
                period="5d",
                interval="1d",
            )

            if history.empty:
                raise ValueError(f"No market data for {ticker}")

            close = float(history["Close"].iloc[-1])

            previous = (
                float(history["Close"].iloc[-2])
                if len(history) > 1
                else None
            )

            change = (
                close - previous
                if previous is not None
                else None
            )

            change_pct = (
                change / previous * 100
                if previous
                else None
            )

            return {
                "ticker": ticker,
                "price": close,
                "previous_close": previous,
                "change": change,
                "change_pct": change_pct,
            }

    def get_quotes(self, tickers: list[str]) -> dict[str, dict]:
        result = {}

        tickers = list(dict.fromkeys(
            t.upper().strip() for t in tickers
        ))

        for ticker in tickers:
            try:
                result[ticker] = self.get_quote(ticker)
            except Exception:
                continue

        return result

    def get_history(
        self,
        ticker: str,
        period: str = "5y",
        interval: str = "1d",
    ) -> pd.DataFrame:

        ticker = ticker.upper().strip()

        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        required = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]

        missing = [
            c for c in required
            if c not in df.columns
        ]

        if missing:
            return pd.DataFrame()

        df = df[required].copy()

        df.index = pd.to_datetime(df.index)
        df = df[~df.index.duplicated()]
        df = df.sort_index()

        return df.dropna(subset=["Close"])

    def get_universe(self) -> list[str]:
        # Production deployment should replace this with a maintained
        # exchange/universe provider.
        return []
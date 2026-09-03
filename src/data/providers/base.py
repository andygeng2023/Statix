from abc import ABC, abstractmethod
from typing import Iterable

import pandas as pd


class MarketDataProvider(ABC):

    name = "Unknown provider"

    realtime = False

    bulk_quotes = False

    @abstractmethod
    def get_quote(self, ticker: str) -> dict:
        raise NotImplementedError

    def get_quotes(
        self,
        tickers: Iterable[str],
    ) -> dict[str, dict]:

        return {
            ticker.upper(): self.get_quote(ticker)
            for ticker in tickers
        }

    @abstractmethod
    def get_history(
        self,
        ticker: str,
        period: str = "5y",
        interval: str = "1d",
    ) -> pd.DataFrame:

        raise NotImplementedError

    def get_universe(self) -> list[str]:
        return []
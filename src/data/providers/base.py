from abc import ABC, abstractmethod

import pandas as pd


class MarketDataProvider(ABC):

    @abstractmethod
    def get_quote(self, ticker: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_quotes(self, tickers: list[str]) -> dict[str, dict]:
        raise NotImplementedError

    @abstractmethod
    def get_history(
        self,
        ticker: str,
        period: str = "5y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def get_universe(self) -> list[str]:
        raise NotImplementedError
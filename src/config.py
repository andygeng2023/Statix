import os
from dataclasses import dataclass

import streamlit as st


def _secret(name: str, default=None):
    try:
        value = st.secrets.get(name, None)
        if value is not None:
            return value
    except Exception:
        pass

    return os.getenv(name, default)


@dataclass(frozen=True)
class Settings:
    app_name: str = "Statix"

    market_provider: str = "yahoo"

    quote_cache_seconds: int = 20
    history_cache_seconds: int = 300
    search_cache_seconds: int = 3600

    prediction_horizon: int = 5

    model_version: str = "statix-v9-global-1"
    feature_version: str = "statix-v9-features-1"

    minimum_training_rows: int = 500

    scanner_default_limit: int = 25
    scanner_max_symbols: int = 10000

    database_url: str = "sqlite:///statix.db"

    require_auth: bool = False


def get_settings() -> Settings:
    require_auth_raw = _secret("require_auth", False)

    if isinstance(require_auth_raw, str):
        require_auth = require_auth_raw.lower() == "true"
    else:
        require_auth = bool(require_auth_raw)

    return Settings(
        market_provider=str(
            _secret("market_provider", "yahoo")
        ).lower(),

        quote_cache_seconds=int(
            _secret("quote_cache_seconds", 20)
        ),

        history_cache_seconds=int(
            _secret("history_cache_seconds", 300)
        ),

        prediction_horizon=int(
            _secret("prediction_horizon", 5)
        ),

        model_version=str(
            _secret("model_version", "statix-v9-global-1")
        ),

        feature_version=str(
            _secret("feature_version", "statix-v9-features-1")
        ),

        minimum_training_rows=int(
            _secret("minimum_training_rows", 500)
        ),

        scanner_default_limit=int(
            _secret("scanner_default_limit", 25)
        ),

        scanner_max_symbols=int(
            _secret("scanner_max_symbols", 10000)
        ),

        database_url=str(
            _secret(
                "database_url",
                os.getenv("DATABASE_URL", "sqlite:///statix.db"),
            )
        ),

        require_auth=require_auth,
    )


SETTINGS = get_settings()
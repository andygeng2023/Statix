from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)

from src.auth import current_user_id


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

SQLITE_PATH = (
    BASE_DIR
    / "statix.db"
)


def _database_url() -> str:

    try:

        url = st.secrets.get(
            "database_url"
        )

        if url:
            return str(url)

    except Exception:
        pass

    url = os.getenv(
        "DATABASE_URL"
    )

    if url:
        return url

    return (
        f"sqlite:///{SQLITE_PATH}"
    )


DATABASE_URL = (
    _database_url()
)


connect_args = {}

if DATABASE_URL.startswith(
    "sqlite"
):

    connect_args = {
        "check_same_thread": False
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


class UserWatchlist(Base):

    __tablename__ = (
        "user_watchlist"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "ticker",
            name="uq_user_watchlist_ticker",
        ),
    )

    id: Mapped[int] = (
        mapped_column(
            Integer,
            primary_key=True,
        )
    )

    user_id: Mapped[str] = (
        mapped_column(
            String(128),
            index=True,
            nullable=False,
        )
    )

    ticker: Mapped[str] = (
        mapped_column(
            String(20),
            index=True,
            nullable=False,
        )
    )

    added_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            default=datetime.utcnow,
            nullable=False,
        )
    )


class UserViewedStock(Base):

    __tablename__ = (
        "user_viewed_stocks"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "ticker",
            name="uq_user_viewed_ticker",
        ),
    )

    id: Mapped[int] = (
        mapped_column(
            Integer,
            primary_key=True,
        )
    )

    user_id: Mapped[str] = (
        mapped_column(
            String(128),
            index=True,
            nullable=False,
        )
    )

    ticker: Mapped[str] = (
        mapped_column(
            String(20),
            index=True,
            nullable=False,
        )
    )

    last_viewed: Mapped[datetime] = (
        mapped_column(
            DateTime,
            default=datetime.utcnow,
            nullable=False,
        )
    )

    last_market_date: Mapped[str | None] = (
        mapped_column(
            String(30),
            nullable=True,
        )
    )

    last_price: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    direction: Mapped[str | None] = (
        mapped_column(
            String(40),
            nullable=True,
        )
    )

    probability_up: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    expected_return: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    confidence: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    test_accuracy: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    return_rmse: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    model_version: Mapped[str | None] = (
        mapped_column(
            String(100),
            nullable=True,
        )
    )

    feature_version: Mapped[str | None] = (
        mapped_column(
            String(100),
            nullable=True,
        )
    )

    horizon: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )

    model_agreement: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    validation_folds: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )

    training_rows: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )

    feature_count: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )


class UserPredictionHistory(Base):

    __tablename__ = (
        "user_prediction_history"
    )

    id: Mapped[int] = (
        mapped_column(
            Integer,
            primary_key=True,
        )
    )

    user_id: Mapped[str] = (
        mapped_column(
            String(128),
            index=True,
            nullable=False,
        )
    )

    ticker: Mapped[str] = (
        mapped_column(
            String(20),
            index=True,
            nullable=False,
        )
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            default=datetime.utcnow,
            nullable=False,
        )
    )

    market_date: Mapped[str | None] = (
        mapped_column(
            String(30),
            nullable=True,
        )
    )

    price: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    direction: Mapped[str | None] = (
        mapped_column(
            String(40),
            nullable=True,
        )
    )

    probability_up: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    expected_return: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    confidence: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    model_version: Mapped[str | None] = (
        mapped_column(
            String(100),
            nullable=True,
        )
    )

    feature_version: Mapped[str | None] = (
        mapped_column(
            String(100),
            nullable=True,
        )
    )

    horizon: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )


class PredictionCache(Base):

    __tablename__ = (
        "prediction_cache"
    )

    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "market_date",
            "model_version",
            "feature_version",
            "horizon",
            name="uq_prediction_cache_key",
        ),
    )

    id: Mapped[int] = (
        mapped_column(
            Integer,
            primary_key=True,
        )
    )

    ticker: Mapped[str] = (
        mapped_column(
            String(20),
            index=True,
            nullable=False,
        )
    )

    market_date: Mapped[str] = (
        mapped_column(
            String(30),
            nullable=False,
        )
    )

    model_version: Mapped[str] = (
        mapped_column(
            String(100),
            nullable=False,
        )
    )

    feature_version: Mapped[str] = (
        mapped_column(
            String(100),
            nullable=False,
        )
    )

    horizon: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
        )
    )

    price: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    direction: Mapped[str | None] = (
        mapped_column(
            String(40),
            nullable=True,
        )
    )

    probability_up: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    expected_return: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    confidence: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    validation_accuracy: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    rmse: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    model_agreement: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    validation_folds: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )

    training_rows: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )

    feature_count: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )

    class_probabilities_json: Mapped[str | None] = (
        mapped_column(
            Text,
            nullable=True,
        )
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            default=datetime.utcnow,
            nullable=False,
        )
    )


# Creates missing tables without modifying existing columns.
Base.metadata.create_all(
    engine
)


def _user() -> str:
    return current_user_id()


def add_to_watchlist(
    ticker: str,
) -> None:

    ticker = (
        ticker
        .strip()
        .upper()
    )

    if not ticker:
        return

    with SessionLocal() as session:

        existing = (
            session.query(
                UserWatchlist
            )
            .filter_by(
                user_id=_user(),
                ticker=ticker,
            )
            .first()
        )

        if existing is None:

            session.add(
                UserWatchlist(
                    user_id=_user(),
                    ticker=ticker,
                )
            )

            session.commit()


def remove_from_watchlist(
    ticker: str,
) -> None:

    ticker = (
        ticker
        .strip()
        .upper()
    )

    with SessionLocal() as session:

        row = (
            session.query(
                UserWatchlist
            )
            .filter_by(
                user_id=_user(),
                ticker=ticker,
            )
            .first()
        )

        if row:

            session.delete(
                row
            )

            session.commit()


def is_watched(
    ticker: str,
) -> bool:

    ticker = (
        ticker
        .strip()
        .upper()
    )

    with SessionLocal() as session:

        return (
            session.query(
                UserWatchlist
            )
            .filter_by(
                user_id=_user(),
                ticker=ticker,
            )
            .first()
            is not None
        )


def get_watchlist() -> list[str]:

    with SessionLocal() as session:

        rows = (
            session.query(
                UserWatchlist
            )
            .filter_by(
                user_id=_user()
            )
            .order_by(
                UserWatchlist.added_at.desc()
            )
            .all()
        )

        return [
            row.ticker
            for row in rows
        ]


def _result_dict(
    row: UserViewedStock,
) -> dict:

    return {
        "ticker": row.ticker,
        "market_date": row.last_market_date,
        "price": row.last_price,
        "signal": row.direction,
        "direction": row.direction,
        "probability_up": row.probability_up,
        "expected_return": row.expected_return,
        "confidence": row.confidence,
        "validation_accuracy": row.test_accuracy,
        "test_accuracy": row.test_accuracy,
        "rmse": row.return_rmse,
        "model_version": row.model_version,
        "feature_version": row.feature_version,
        "horizon": row.horizon,
        "model_agreement": row.model_agreement,
        "validation_folds": row.validation_folds,
        "training_rows": row.training_rows,
        "feature_count": row.feature_count,
        "class_probabilities": {},
    }


def save_viewed_prediction(
    ticker: str,
    result: dict,
) -> None:

    ticker = (
        ticker
        .strip()
        .upper()
    )

    with SessionLocal() as session:

        row = (
            session.query(
                UserViewedStock
            )
            .filter_by(
                user_id=_user(),
                ticker=ticker,
            )
            .first()
        )

        if row is None:

            row = UserViewedStock(
                user_id=_user(),
                ticker=ticker,
            )

            session.add(
                row
            )

        row.last_viewed = (
            datetime.utcnow()
        )

        row.last_market_date = (
            result.get(
                "market_date"
            )
        )

        row.last_price = (
            result.get(
                "price"
            )
        )

        row.direction = (
            result.get(
                "signal"
            )
        )

        row.probability_up = (
            result.get(
                "probability_up"
            )
        )

        row.expected_return = (
            result.get(
                "expected_return"
            )
        )

        row.confidence = (
            result.get(
                "confidence"
            )
        )

        row.test_accuracy = (
            result.get(
                "validation_accuracy"
            )
        )

        row.return_rmse = (
            result.get(
                "rmse"
            )
        )

        row.model_version = (
            result.get(
                "model_version"
            )
        )

        row.feature_version = (
            result.get(
                "feature_version"
            )
        )

        row.horizon = (
            result.get(
                "horizon"
            )
        )

        row.model_agreement = (
            result.get(
                "model_agreement"
            )
        )

        row.validation_folds = (
            result.get(
                "validation_folds"
            )
        )

        row.training_rows = (
            result.get(
                "training_rows"
            )
        )

        row.feature_count = (
            result.get(
                "feature_count"
            )
        )

        session.commit()


def get_recently_viewed(
    limit: int = 12,
) -> list[dict]:

    with SessionLocal() as session:

        rows = (
            session.query(
                UserViewedStock
            )
            .filter_by(
                user_id=_user()
            )
            .order_by(
                UserViewedStock.last_viewed.desc()
            )
            .limit(limit)
            .all()
        )

        return [
            _result_dict(row)
            for row in rows
        ]


def get_cached_prediction(
    ticker: str,
    market_date: str,
    model_version: str,
    feature_version: str,
    horizon: int,
) -> dict | None:

    ticker = (
        ticker
        .strip()
        .upper()
    )

    with SessionLocal() as session:

        row = (
            session.query(
                PredictionCache
            )
            .filter_by(
                ticker=ticker,
                market_date=market_date,
                model_version=model_version,
                feature_version=feature_version,
                horizon=horizon,
            )
            .first()
        )

        if row is None:
            return None

        probabilities = {}

        if row.class_probabilities_json:

            try:

                probabilities = json.loads(
                    row.class_probabilities_json
                )

            except Exception:

                probabilities = {}

        return {
            "ticker": row.ticker,
            "market_date": row.market_date,
            "price": row.price,
            "signal": row.direction,
            "probability_up": row.probability_up,
            "expected_return": row.expected_return,
            "confidence": row.confidence,
            "validation_accuracy": row.validation_accuracy,
            "rmse": row.rmse,
            "model_version": row.model_version,
            "feature_version": row.feature_version,
            "horizon": row.horizon,
            "model_agreement": row.model_agreement,
            "validation_folds": row.validation_folds,
            "training_rows": row.training_rows,
            "feature_count": row.feature_count,
            "class_probabilities": probabilities,
        }


def save_prediction_cache(
    ticker: str,
    result: dict,
) -> None:

    ticker = (
        ticker
        .strip()
        .upper()
    )

    with SessionLocal() as session:

        row = (
            session.query(
                PredictionCache
            )
            .filter_by(
                ticker=ticker,
                market_date=result.get(
                    "market_date"
                ),
                model_version=result.get(
                    "model_version"
                ),
                feature_version=result.get(
                    "feature_version"
                ),
                horizon=result.get(
                    "horizon"
                ),
            )
            .first()
        )

        if row is None:

            row = PredictionCache(
                ticker=ticker,
                market_date=result.get(
                    "market_date"
                ),
                model_version=result.get(
                    "model_version"
                ),
                feature_version=result.get(
                    "feature_version"
                ),
                horizon=result.get(
                    "horizon"
                ),
            )

            session.add(
                row
            )

        row.price = result.get(
            "price"
        )

        row.direction = result.get(
            "signal"
        )

        row.probability_up = result.get(
            "probability_up"
        )

        row.expected_return = result.get(
            "expected_return"
        )

        row.confidence = result.get(
            "confidence"
        )

        row.validation_accuracy = result.get(
            "validation_accuracy"
        )

        row.rmse = result.get(
            "rmse"
        )

        row.model_agreement = result.get(
            "model_agreement"
        )

        row.validation_folds = result.get(
            "validation_folds"
        )

        row.training_rows = result.get(
            "training_rows"
        )

        row.feature_count = result.get(
            "feature_count"
        )

        row.class_probabilities_json = json.dumps(
            result.get(
                "class_probabilities",
                {},
            ),
            separators=(
                ",",
                ":",
            ),
        )

        session.commit()


def save_prediction_history(
    ticker: str,
    result: dict,
) -> None:

    ticker = (
        ticker
        .strip()
        .upper()
    )

    with SessionLocal() as session:

        session.add(
            UserPredictionHistory(
                user_id=_user(),
                ticker=ticker,
                market_date=result.get(
                    "market_date"
                ),
                price=result.get(
                    "price"
                ),
                direction=result.get(
                    "signal"
                ),
                probability_up=result.get(
                    "probability_up"
                ),
                expected_return=result.get(
                    "expected_return"
                ),
                confidence=result.get(
                    "confidence"
                ),
                model_version=result.get(
                    "model_version"
                ),
                feature_version=result.get(
                    "feature_version"
                ),
                horizon=result.get(
                    "horizon"
                ),
            )
        )

        session.commit()
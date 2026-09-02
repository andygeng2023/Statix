from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


DATABASE_URL = "sqlite:///statix.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    ticker: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
    )

    added_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class ViewedStock(Base):
    __tablename__ = "viewed_stocks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    ticker: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
    )

    last_viewed: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    last_market_date: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    last_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    direction: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    probability_up: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    expected_return: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    test_accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    return_rmse: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    feature_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    horizon: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    ticker: Mapped[str] = mapped_column(
        String(20),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    market_date: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    direction: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    probability_up: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    expected_return: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    feature_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    horizon: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )


Base.metadata.create_all(engine)


def add_to_watchlist(ticker: str) -> None:
    ticker = ticker.upper().strip()

    with SessionLocal() as session:
        existing = (
            session.query(WatchlistStock)
            .filter_by(ticker=ticker)
            .first()
        )

        if existing is None:
            session.add(
                WatchlistStock(ticker=ticker)
            )
            session.commit()


def remove_from_watchlist(ticker: str) -> None:
    ticker = ticker.upper().strip()

    with SessionLocal() as session:
        item = (
            session.query(WatchlistStock)
            .filter_by(ticker=ticker)
            .first()
        )

        if item:
            session.delete(item)
            session.commit()


def is_watched(ticker: str) -> bool:
    ticker = ticker.upper().strip()

    with SessionLocal() as session:
        return (
            session.query(WatchlistStock)
            .filter_by(ticker=ticker)
            .first()
            is not None
        )


def get_watchlist() -> list[str]:
    with SessionLocal() as session:
        rows = (
            session.query(WatchlistStock)
            .order_by(WatchlistStock.added_at.desc())
            .all()
        )

        return [row.ticker for row in rows]


def save_viewed_prediction(
    ticker: str,
    result: dict,
) -> None:
    ticker = ticker.upper().strip()

    with SessionLocal() as session:
        item = (
            session.query(ViewedStock)
            .filter_by(ticker=ticker)
            .first()
        )

        if item is None:
            item = ViewedStock(
                ticker=ticker,
            )
            session.add(item)

        item.last_viewed = datetime.utcnow()
        item.last_market_date = result.get("market_date")
        item.last_price = result.get("price")
        item.direction = result.get("signal")
        item.probability_up = result.get("probability_up")
        item.expected_return = result.get("expected_return")
        item.confidence = result.get("confidence")
        item.test_accuracy = result.get("validation_accuracy")
        item.return_rmse = result.get("rmse")
        item.model_version = result.get("model_version")
        item.feature_version = result.get("feature_version")
        item.horizon = result.get("horizon")

        session.commit()


def get_recently_viewed(limit: int = 12) -> list[dict]:
    with SessionLocal() as session:
        rows = (
            session.query(ViewedStock)
            .order_by(ViewedStock.last_viewed.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "ticker": row.ticker,
                "market_date": row.last_market_date,
                "price": row.last_price,
                "direction": row.direction,
                "probability_up": row.probability_up,
                "expected_return": row.expected_return,
                "confidence": row.confidence,
                "test_accuracy": row.test_accuracy,
                "rmse": row.return_rmse,
                "model_version": row.model_version,
                "feature_version": row.feature_version,
                "horizon": row.horizon,
            }
            for row in rows
        ]


def get_cached_prediction(
    ticker: str,
    market_date: str,
    model_version: str,
    feature_version: str,
    horizon: int,
) -> dict | None:

    ticker = ticker.upper().strip()

    with SessionLocal() as session:
        row = (
            session.query(ViewedStock)
            .filter(
                ViewedStock.ticker == ticker,
                ViewedStock.last_market_date == market_date,
                ViewedStock.model_version == model_version,
                ViewedStock.feature_version == feature_version,
                ViewedStock.horizon == horizon,
            )
            .first()
        )

        if row is None:
            return None

        return {
            "ticker": row.ticker,
            "market_date": row.last_market_date,
            "price": row.last_price,
            "signal": row.direction,
            "probability_up": row.probability_up,
            "expected_return": row.expected_return,
            "confidence": row.confidence,
            "validation_accuracy": row.test_accuracy,
            "rmse": row.return_rmse,
            "model_version": row.model_version,
            "feature_version": row.feature_version,
            "horizon": row.horizon,
        }


def save_prediction_history(
    ticker: str,
    result: dict,
) -> None:

    with SessionLocal() as session:
        session.add(
            PredictionHistory(
                ticker=ticker.upper().strip(),
                market_date=result.get("market_date"),
                price=result.get("price"),
                direction=result.get("signal"),
                probability_up=result.get("probability_up"),
                expected_return=result.get("expected_return"),
                confidence=result.get("confidence"),
                model_version=result.get("model_version"),
                feature_version=result.get("feature_version"),
                horizon=result.get("horizon"),
            )
        )

        session.commit()
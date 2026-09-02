import os
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
)
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///statix.db",
)

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ViewedStock(Base):
    __tablename__ = "viewed_stocks"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)

    last_viewed = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    last_market_date = Column(String)
    last_price = Column(Float)

    direction = Column(String)
    probability_up = Column(Float)
    expected_return = Column(Float)
    confidence = Column(Float)

    test_accuracy = Column(Float)
    return_rmse = Column(Float)

    model_version = Column(String)
    horizon = Column(Integer)


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    market_date = Column(String)
    price = Column(Float)

    direction = Column(String)
    probability_up = Column(Float)
    expected_return = Column(Float)
    confidence = Column(Float)

    model_version = Column(String)
    horizon = Column(Integer)


Base.metadata.create_all(engine)


def add_to_watchlist(ticker):
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


def remove_from_watchlist(ticker):
    ticker = ticker.upper().strip()

    with SessionLocal() as session:
        existing = (
            session.query(WatchlistStock)
            .filter_by(ticker=ticker)
            .first()
        )

        if existing:
            session.delete(existing)
            session.commit()


def get_watchlist():
    with SessionLocal() as session:
        rows = (
            session.query(WatchlistStock)
            .order_by(WatchlistStock.added_at.desc())
            .all()
        )

        return [row.ticker for row in rows]


def is_watched(ticker):
    ticker = ticker.upper().strip()

    with SessionLocal() as session:
        return (
            session.query(WatchlistStock)
            .filter_by(ticker=ticker)
            .first()
            is not None
        )


def save_viewed_prediction(
    ticker,
    market_date,
    price,
    prediction,
):
    ticker = ticker.upper().strip()

    with SessionLocal() as session:
        row = (
            session.query(ViewedStock)
            .filter_by(ticker=ticker)
            .first()
        )

        if row is None:
            row = ViewedStock(ticker=ticker)
            session.add(row)

        row.last_viewed = datetime.now(timezone.utc)
        row.last_market_date = market_date
        row.last_price = price

        row.direction = prediction["direction"]
        row.probability_up = prediction["probability_up"]
        row.expected_return = prediction["expected_return"]
        row.confidence = prediction["confidence"]

        row.test_accuracy = prediction["test_accuracy"]
        row.return_rmse = prediction["return_rmse"]

        row.model_version = prediction["model_version"]
        row.horizon = prediction["horizon"]

        session.commit()


def get_cached_prediction(
    ticker,
    market_date,
    model_version,
    horizon,
):
    ticker = ticker.upper().strip()

    with SessionLocal() as session:
        row = (
            session.query(ViewedStock)
            .filter_by(
                ticker=ticker,
                last_market_date=market_date,
                model_version=model_version,
                horizon=horizon,
            )
            .first()
        )

        if row is None:
            return None

        return {
            "direction": row.direction,
            "probability_up": row.probability_up,
            "expected_return": row.expected_return,
            "confidence": row.confidence,
            "test_accuracy": row.test_accuracy,
            "return_rmse": row.return_rmse,
            "model_version": row.model_version,
            "horizon": row.horizon,
            "price": row.last_price,
            "market_date": row.last_market_date,
            "cached": True,
        }


def save_prediction_history(
    ticker,
    market_date,
    price,
    prediction,
):
    ticker = ticker.upper().strip()

    with SessionLocal() as session:
        row = PredictionHistory(
            ticker=ticker,
            market_date=market_date,
            price=price,
            direction=prediction["direction"],
            probability_up=prediction["probability_up"],
            expected_return=prediction["expected_return"],
            confidence=prediction["confidence"],
            model_version=prediction["model_version"],
            horizon=prediction["horizon"],
        )

        session.add(row)
        session.commit()


def get_recently_viewed(limit=12):
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
                "last_viewed": row.last_viewed,
                "last_market_date": row.last_market_date,
                "last_price": row.last_price,
                "direction": row.direction,
                "probability_up": row.probability_up,
                "expected_return": row.expected_return,
                "confidence": row.confidence,
            }
            for row in rows
        ]
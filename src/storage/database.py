from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)


# =========================================================
# DATABASE
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = BASE_DIR / "statix.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

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


# =========================================================
# TABLES
# =========================================================

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
        nullable=False,
    )

    added_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
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
        nullable=False,
    )

    last_viewed: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
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
        String(40),
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

    model_agreement: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    validation_folds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    training_rows: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    feature_count: Mapped[int | None] = mapped_column(
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
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
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
        String(40),
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


# =========================================================
# DATABASE INITIALIZATION + MIGRATION
# =========================================================

def _add_missing_columns() -> None:
    """
    SQLite create_all() does not modify existing tables.

    This adds columns introduced by newer Statix versions.
    """

    inspector = inspect(engine)

    migrations = {
        "viewed_stocks": {
            "feature_version": "VARCHAR(100)",
            "horizon": "INTEGER",
            "model_agreement": "FLOAT",
            "validation_folds": "INTEGER",
            "training_rows": "INTEGER",
            "feature_count": "INTEGER",
        },
        "prediction_history": {
            "feature_version": "VARCHAR(100)",
            "horizon": "INTEGER",
        },
    }

    with engine.begin() as connection:

        for table_name, columns in migrations.items():

            if table_name not in inspector.get_table_names():
                continue

            existing = {
                column["name"]
                for column in inspector.get_columns(
                    table_name
                )
            }

            for column_name, column_type in columns.items():

                if column_name in existing:
                    continue

                connection.execute(
                    text(
                        f'ALTER TABLE "{table_name}" '
                        f'ADD COLUMN "{column_name}" '
                        f'{column_type}'
                    )
                )


Base.metadata.create_all(engine)
_add_missing_columns()


# =========================================================
# WATCHLIST
# =========================================================

def add_to_watchlist(ticker: str) -> None:
    ticker = ticker.strip().upper()

    if not ticker:
        return

    with SessionLocal() as session:

        existing = (
            session.query(WatchlistStock)
            .filter(
                WatchlistStock.ticker == ticker
            )
            .first()
        )

        if existing is None:
            session.add(
                WatchlistStock(
                    ticker=ticker
                )
            )
            session.commit()


def remove_from_watchlist(ticker: str) -> None:
    ticker = ticker.strip().upper()

    with SessionLocal() as session:

        existing = (
            session.query(WatchlistStock)
            .filter(
                WatchlistStock.ticker == ticker
            )
            .first()
        )

        if existing is not None:
            session.delete(existing)
            session.commit()


def is_watched(ticker: str) -> bool:
    ticker = ticker.strip().upper()

    with SessionLocal() as session:

        return (
            session.query(WatchlistStock)
            .filter(
                WatchlistStock.ticker == ticker
            )
            .first()
            is not None
        )


def get_watchlist() -> list[str]:
    with SessionLocal() as session:

        rows = (
            session.query(WatchlistStock)
            .order_by(
                WatchlistStock.added_at.desc()
            )
            .all()
        )

        return [
            row.ticker
            for row in rows
        ]


# =========================================================
# VIEWED / PREDICTIONS
# =========================================================

def save_viewed_prediction(
    ticker: str,
    result: dict,
) -> None:

    ticker = ticker.strip().upper()

    with SessionLocal() as session:

        item = (
            session.query(ViewedStock)
            .filter(
                ViewedStock.ticker == ticker
            )
            .first()
        )

        if item is None:
            item = ViewedStock(
                ticker=ticker
            )
            session.add(item)

        item.last_viewed = datetime.utcnow()

        item.last_market_date = result.get(
            "market_date"
        )

        item.last_price = result.get(
            "price"
        )

        item.direction = result.get(
            "signal"
        )

        item.probability_up = result.get(
            "probability_up"
        )

        item.expected_return = result.get(
            "expected_return"
        )

        item.confidence = result.get(
            "confidence"
        )

        item.test_accuracy = result.get(
            "validation_accuracy"
        )

        item.return_rmse = result.get(
            "rmse"
        )

        item.model_version = result.get(
            "model_version"
        )

        item.feature_version = result.get(
            "feature_version"
        )

        item.horizon = result.get(
            "horizon"
        )

        item.model_agreement = result.get(
            "model_agreement"
        )

        item.validation_folds = result.get(
            "validation_folds"
        )

        item.training_rows = result.get(
            "training_rows"
        )

        item.feature_count = result.get(
            "feature_count"
        )

        session.commit()


def get_recently_viewed(
    limit: int = 12,
) -> list[dict]:

    with SessionLocal() as session:

        rows = (
            session.query(ViewedStock)
            .order_by(
                ViewedStock.last_viewed.desc()
            )
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
                "model_agreement": row.model_agreement,
                "validation_folds": row.validation_folds,
                "training_rows": row.training_rows,
                "feature_count": row.feature_count,
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

    ticker = ticker.strip().upper()

    with SessionLocal() as session:

        row = (
            session.query(ViewedStock)
            .filter(
                ViewedStock.ticker == ticker,
                ViewedStock.last_market_date
                == market_date,
                ViewedStock.model_version
                == model_version,
                ViewedStock.feature_version
                == feature_version,
                ViewedStock.horizon
                == horizon,
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
            "model_agreement": row.model_agreement,
            "validation_folds": row.validation_folds,
            "training_rows": row.training_rows,
            "feature_count": row.feature_count,
        }


def save_prediction_history(
    ticker: str,
    result: dict,
) -> None:

    ticker = ticker.strip().upper()

    with SessionLocal() as session:

        session.add(
            PredictionHistory(
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
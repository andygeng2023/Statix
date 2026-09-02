from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = "sqlite:///statix.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


class WatchlistStock(Base):

    __tablename__ = "watchlist"

    id = Column(
        Integer,
        primary_key=True,
    )

    ticker = Column(
        String(20),
        unique=True,
        nullable=False,
    )

    added_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


class ViewedStock(Base):

    __tablename__ = "viewed"

    id = Column(
        Integer,
        primary_key=True,
    )

    ticker = Column(
        String(20),
        unique=True,
        nullable=False,
    )

    last_viewed = Column(
        DateTime,
        default=datetime.utcnow,
    )

    last_market_date = Column(
        String(20),
    )

    last_price = Column(Float)
    direction = Column(String(30))
    probability_up = Column(Float)
    expected_return = Column(Float)
    confidence = Column(Float)
    test_accuracy = Column(Float)
    return_rmse = Column(Float)
    model_version = Column(String(100))
    horizon = Column(Integer)


class PredictionHistory(Base):

    __tablename__ = "prediction_history"

    id = Column(
        Integer,
        primary_key=True,
    )

    ticker = Column(
        String(20),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    market_date = Column(String(20))
    price = Column(Float)

    direction = Column(String(30))
    probability_up = Column(Float)
    expected_return = Column(Float)
    confidence = Column(Float)

    model_version = Column(String(100))
    horizon = Column(Integer)


def init_db():
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
                WatchlistStock(
                    ticker=ticker
                )
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


def is_watched(ticker):

    ticker = ticker.upper().strip()

    with SessionLocal() as session:

        return (
            session.query(WatchlistStock)
            .filter_by(ticker=ticker)
            .first()
            is not None
        )


def get_watchlist():

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


def save_viewed_prediction(
    ticker,
    market_date,
    price,
    prediction,
    model_version,
    horizon,
):

    ticker = ticker.upper().strip()

    with SessionLocal() as session:

        row = (
            session.query(ViewedStock)
            .filter_by(ticker=ticker)
            .first()
        )

        if row is None:

            row = ViewedStock(
                ticker=ticker
            )

            session.add(row)

        row.last_viewed = datetime.utcnow()
        row.last_market_date = str(
            market_date
        )
        row.last_price = price

        row.direction = prediction[
            "direction"
        ]

        row.probability_up = prediction[
            "probability_up"
        ]

        row.expected_return = prediction[
            "expected_return"
        ]

        row.confidence = prediction[
            "confidence"
        ]

        row.test_accuracy = prediction[
            "accuracy"
        ]

        row.return_rmse = prediction[
            "rmse"
        ]

        row.model_version = model_version
        row.horizon = horizon

        session.commit()


def save_prediction_history(
    ticker,
    market_date,
    price,
    prediction,
    model_version,
    horizon,
):

    with SessionLocal() as session:

        session.add(
            PredictionHistory(
                ticker=ticker.upper(),
                market_date=str(market_date),
                price=price,
                direction=prediction[
                    "direction"
                ],
                probability_up=prediction[
                    "probability_up"
                ],
                expected_return=prediction[
                    "expected_return"
                ],
                confidence=prediction[
                    "confidence"
                ],
                model_version=model_version,
                horizon=horizon,
            )
        )

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
                last_market_date=str(
                    market_date
                ),
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
            "accuracy": row.test_accuracy,
            "rmse": row.return_rmse,
            "market_date": row.last_market_date,
        }


def get_recently_viewed(limit=12):

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
                "accuracy": row.test_accuracy,
            }
            for row in rows
        ]
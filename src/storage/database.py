import os

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)


Base = declarative_base()


class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"

    id = Column(
        Integer,
        primary_key=True,
    )

    ticker = Column(
        String(20),
        nullable=False,
        unique=True,
    )

    added_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


class ViewedStock(Base):
    __tablename__ = "viewed_stocks"

    id = Column(
        Integer,
        primary_key=True,
    )

    ticker = Column(
        String(20),
        nullable=False,
    )

    last_viewed = Column(
        DateTime,
        default=datetime.utcnow,
    )

    last_market_date = Column(
        String(40),
        nullable=True,
    )

    last_price = Column(
        Float,
        nullable=True,
    )

    direction = Column(
        String(20),
        nullable=True,
    )

    probability_up = Column(
        Float,
        nullable=True,
    )

    expected_return = Column(
        Float,
        nullable=True,
    )

    confidence = Column(
        Float,
        nullable=True,
    )

    test_accuracy = Column(
        Float,
        nullable=True,
    )

    return_rmse = Column(
        Float,
        nullable=True,
    )

    model_version = Column(
        String(100),
        nullable=True,
    )

    horizon = Column(
        Integer,
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "ticker",
            name="unique_viewed_ticker",
        ),
    )


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

    market_date = Column(
        String(40),
        nullable=False,
    )

    price = Column(
        Float,
        nullable=False,
    )

    direction = Column(
        String(20),
        nullable=False,
    )

    probability_up = Column(
        Float,
        nullable=False,
    )

    expected_return = Column(
        Float,
        nullable=False,
    )

    confidence = Column(
        Float,
        nullable=False,
    )

    model_version = Column(
        String(100),
        nullable=False,
    )

    horizon = Column(
        Integer,
        nullable=False,
    )


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///statix.db",
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
)


SessionLocal = sessionmaker(
    bind=engine
)


Base.metadata.create_all(
    engine
)


def add_to_watchlist(ticker):
    ticker = ticker.upper().strip()

    session = SessionLocal()

    try:
        existing = (
            session.query(
                WatchlistStock
            )
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

    finally:
        session.close()


def remove_from_watchlist(ticker):
    ticker = ticker.upper().strip()

    session = SessionLocal()

    try:
        existing = (
            session.query(
                WatchlistStock
            )
            .filter_by(ticker=ticker)
            .first()
        )

        if existing:
            session.delete(existing)
            session.commit()

    finally:
        session.close()


def get_watchlist():
    session = SessionLocal()

    try:
        stocks = (
            session.query(
                WatchlistStock
            )
            .order_by(
                WatchlistStock.added_at.desc()
            )
            .all()
        )

        return [
            stock.ticker
            for stock in stocks
        ]

    finally:
        session.close()


def is_watched(ticker):
    ticker = ticker.upper().strip()

    session = SessionLocal()

    try:
        return (
            session.query(
                WatchlistStock
            )
            .filter_by(ticker=ticker)
            .first()
            is not None
        )

    finally:
        session.close()


def save_viewed_prediction(
    ticker,
    market_date,
    price,
    prediction,
):
    ticker = ticker.upper().strip()

    session = SessionLocal()

    try:
        viewed = (
            session.query(
                ViewedStock
            )
            .filter_by(ticker=ticker)
            .first()
        )

        if viewed is None:
            viewed = ViewedStock(
                ticker=ticker
            )

            session.add(viewed)

        viewed.last_viewed = datetime.utcnow()

        viewed.last_market_date = (
            market_date
        )

        viewed.last_price = float(
            price
        )

        viewed.direction = prediction[
            "direction"
        ]

        viewed.probability_up = float(
            prediction[
                "probability_up"
            ]
        )

        viewed.expected_return = float(
            prediction[
                "expected_return"
            ]
        )

        viewed.confidence = float(
            prediction[
                "confidence"
            ]
        )

        viewed.test_accuracy = float(
            prediction[
                "test_accuracy"
            ]
        )

        viewed.return_rmse = float(
            prediction[
                "return_rmse"
            ]
        )

        viewed.model_version = (
            prediction[
                "model_version"
            ]
        )

        viewed.horizon = int(
            prediction[
                "horizon"
            ]
        )

        session.commit()

    finally:
        session.close()


def get_cached_prediction(
    ticker,
    market_date,
    model_version,
    horizon,
):
    ticker = ticker.upper().strip()

    session = SessionLocal()

    try:
        viewed = (
            session.query(
                ViewedStock
            )
            .filter_by(ticker=ticker)
            .first()
        )

        if viewed is None:
            return None

        if (
            viewed.last_market_date
            != market_date
        ):
            return None

        if (
            viewed.model_version
            != model_version
        ):
            return None

        if (
            viewed.horizon
            != horizon
        ):
            return None

        if (
            viewed.direction is None
            or viewed.probability_up is None
        ):
            return None

        return {
            "model_version": (
                viewed.model_version
            ),
            "horizon": viewed.horizon,
            "direction": viewed.direction,
            "probability_up": (
                viewed.probability_up
            ),
            "probability_down": (
                1 - viewed.probability_up
            ),
            "expected_return": (
                viewed.expected_return
            ),
            "confidence": (
                viewed.confidence
            ),
            "test_accuracy": (
                viewed.test_accuracy
            ),
            "return_rmse": (
                viewed.return_rmse
            ),
            "cached": True,
        }

    finally:
        session.close()


def save_prediction_history(
    ticker,
    market_date,
    price,
    prediction,
):
    session = SessionLocal()

    try:
        record = PredictionHistory(
            ticker=ticker.upper().strip(),
            market_date=market_date,
            price=float(price),
            direction=prediction[
                "direction"
            ],
            probability_up=float(
                prediction[
                    "probability_up"
                ]
            ),
            expected_return=float(
                prediction[
                    "expected_return"
                ]
            ),
            confidence=float(
                prediction[
                    "confidence"
                ]
            ),
            model_version=prediction[
                "model_version"
            ],
            horizon=int(
                prediction[
                    "horizon"
                ]
            ),
        )

        session.add(record)
        session.commit()

    finally:
        session.close()


def get_recently_viewed(
    limit=12,
):
    session = SessionLocal()

    try:
        stocks = (
            session.query(
                ViewedStock
            )
            .order_by(
                ViewedStock.last_viewed.desc()
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "ticker": stock.ticker,
                "price": stock.last_price,
                "direction": stock.direction,
                "probability_up": (
                    stock.probability_up
                ),
                "expected_return": (
                    stock.expected_return
                ),
                "confidence": (
                    stock.confidence
                ),
                "last_viewed": (
                    stock.last_viewed
                ),
            }
            for stock in stocks
        ]

    finally:
        session.close()
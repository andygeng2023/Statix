import os

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime


Base = declarative_base()


class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"

    id = Column(Integer, primary_key=True)

    ticker = Column(
        String(20),
        nullable=False,
    )

    added_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "ticker",
            name="unique_ticker",
        ),
    )


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///statix.db",
)

engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False}
        if DATABASE_URL.startswith("sqlite")
        else {}
    ),
)

SessionLocal = sessionmaker(
    bind=engine
)

Base.metadata.create_all(engine)


def get_watchlist():
    session = SessionLocal()

    try:
        stocks = (
            session.query(WatchlistStock)
            .order_by(
                WatchlistStock.added_at.desc()
            )
            .all()
        )

        return [stock.ticker for stock in stocks]

    finally:
        session.close()


def add_to_watchlist(ticker):
    ticker = ticker.upper().strip()

    session = SessionLocal()

    try:
        existing = (
            session.query(WatchlistStock)
            .filter_by(ticker=ticker)
            .first()
        )

        if not existing:
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
        stock = (
            session.query(WatchlistStock)
            .filter_by(ticker=ticker)
            .first()
        )

        if stock:
            session.delete(stock)
            session.commit()

    finally:
        session.close()


def is_watched(ticker):
    ticker = ticker.upper().strip()

    session = SessionLocal()

    try:
        return (
            session.query(WatchlistStock)
            .filter_by(ticker=ticker)
            .first()
            is not None
        )

    finally:
        session.close()
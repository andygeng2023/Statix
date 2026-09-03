from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    String,
    create_engine,
    select,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)

from src.auth import current_user_id
from src.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class Watchlist(Base):

    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[str] = mapped_column(
        String(128),
        index=True,
    )

    ticker: Mapped[str] = mapped_column(
        String(20),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class ViewedStock(Base):

    __tablename__ = "viewed_stock"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[str] = mapped_column(
        String(128),
        index=True,
    )

    ticker: Mapped[str] = mapped_column(
        String(20),
    )

    viewed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

Base.metadata.create_all(
    engine
)


def add_to_watchlist(ticker):

    user_id = current_user_id()

    with SessionLocal() as db:

        existing = db.scalar(
            select(Watchlist).where(
                Watchlist.user_id == user_id,
                Watchlist.ticker == ticker,
            )
        )

        if existing:
            return

        db.add(
            Watchlist(
                user_id=user_id,
                ticker=ticker,
            )
        )

        db.commit()


def remove_from_watchlist(ticker):

    user_id = current_user_id()

    with SessionLocal() as db:

        row = db.scalar(
            select(Watchlist).where(
                Watchlist.user_id == user_id,
                Watchlist.ticker == ticker,
            )
        )

        if row:
            db.delete(row)
            db.commit()


def get_watchlist():

    user_id = current_user_id()

    with SessionLocal() as db:

        rows = db.scalars(
            select(Watchlist)
            .where(
                Watchlist.user_id == user_id
            )
            .order_by(
                Watchlist.created_at.desc()
            )
        ).all()

        return [
            row.ticker
            for row in rows
        ]


def record_view(ticker):

    user_id = current_user_id()

    with SessionLocal() as db:

        db.add(
            ViewedStock(
                user_id=user_id,
                ticker=ticker,
            )
        )

        db.commit()


def get_recent_views(limit=10):

    user_id = current_user_id()

    with SessionLocal() as db:

        rows = db.scalars(
            select(ViewedStock)
            .where(
                ViewedStock.user_id == user_id
            )
            .order_by(
                ViewedStock.viewed_at.desc()
            )
            .limit(limit)
        ).all()

        return [
            row.ticker
            for row in rows
        ]
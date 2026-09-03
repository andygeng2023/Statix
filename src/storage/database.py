from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from src.auth import current_user
from src.config import database_url


def _normalize_database_url(url: str | None) -> str:
    """Normalize common PostgreSQL URLs to the installed psycopg 3 driver."""
    if not url:
        return "sqlite:///statix.db"
    value = str(url).strip()
    if value.startswith("postgres://"):
        value = "postgresql+psycopg://" + value[len("postgres://"): ]
    elif value.startswith("postgresql://"):
        value = "postgresql+psycopg://" + value[len("postgresql://"): ]
    elif value.startswith("postgresql+psycopg2://"):
        value = "postgresql+psycopg://" + value[len("postgresql+psycopg2://"): ]
    return value


URL = _normalize_database_url(database_url())
connect_args = {"check_same_thread": False} if URL.startswith("sqlite") else {}
engine = create_engine(
    URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=1800,
)
Session = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Watch(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    ticker: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_watch_user_ticker"),
    )


class View(Base):
    __tablename__ = "recent_views"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    ticker: Mapped[str] = mapped_column(String(20))
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


Base.metadata.create_all(engine)


def uid() -> str:
    user = current_user() or {"id": "anonymous"}
    return str(user["id"])


def get_watchlist() -> list[str]:
    with Session() as s:
        return [
            x.ticker
            for x in s.query(Watch)
            .filter_by(user_id=uid())
            .order_by(Watch.created_at.desc())
            .all()
        ]


def is_watched(ticker: str) -> bool:
    ticker = ticker.upper()
    with Session() as s:
        return s.query(Watch).filter_by(user_id=uid(), ticker=ticker).first() is not None


def add_to_watchlist(ticker: str) -> None:
    ticker = ticker.upper()
    with Session() as s:
        if not s.query(Watch).filter_by(user_id=uid(), ticker=ticker).first():
            s.add(Watch(user_id=uid(), ticker=ticker))
            s.commit()


def remove_from_watchlist(ticker: str) -> None:
    ticker = ticker.upper()
    with Session() as s:
        s.query(Watch).filter_by(user_id=uid(), ticker=ticker).delete()
        s.commit()


def record_view(ticker: str) -> None:
    ticker = ticker.upper()
    with Session() as s:
        s.query(View).filter_by(user_id=uid(), ticker=ticker).delete()
        s.add(View(user_id=uid(), ticker=ticker))
        s.commit()


def recent(limit: int = 8) -> list[str]:
    with Session() as s:
        return [
            x.ticker
            for x in s.query(View)
            .filter_by(user_id=uid())
            .order_by(View.viewed_at.desc())
            .limit(limit)
            .all()
        ]

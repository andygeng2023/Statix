import json
import os
from datetime import datetime, timezone

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
from src.config import SETTINGS


DB_URL = SETTINGS.database_url

if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace(
        "postgres://",
        "postgresql+psycopg://",
        1,
    )

connect_args = {}

if DB_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }


engine = create_engine(
    DB_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

Session = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


class UserWatchlist(Base):

    __tablename__ = "user_watchlist"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[str] = mapped_column(
        String(80),
        index=True,
    )

    ticker: Mapped[str] = mapped_column(
        String(20)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "ticker",
            name="uq_user_watchlist",
        ),
    )


class UserViewed(Base):

    __tablename__ = "user_viewed"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[str] = mapped_column(
        String(80),
        index=True,
    )

    ticker: Mapped[str] = mapped_column(
        String(20)
    )

    viewed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )


class UserPrediction(Base):

    __tablename__ = "user_predictions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[str] = mapped_column(
        String(80),
        index=True,
    )

    ticker: Mapped[str] = mapped_column(
        String(20)
    )

    market_date: Mapped[str] = mapped_column(
        String(40)
    )

    model_version: Mapped[str] = mapped_column(
        String(100)
    )

    result_json: Mapped[str] = mapped_column(
        Text
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )


class SharedScan(Base):

    __tablename__ = "shared_scans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    scan_key: Mapped[str] = mapped_column(
        String(300),
        unique=True,
    )

    result_json: Mapped[str] = mapped_column(
        Text
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )


def init_db():

    Base.metadata.create_all(
        engine
    )


def _session():

    return Session()


def add_watch(ticker: str):

    ticker = ticker.upper().strip()

    session = _session()

    try:

        existing = (
            session.query(
                UserWatchlist
            )
            .filter_by(
                user_id=current_user_id(),
                ticker=ticker,
            )
            .first()
        )

        if existing is None:

            session.add(
                UserWatchlist(
                    user_id=current_user_id(),
                    ticker=ticker,
                )
            )

            session.commit()

    finally:
        session.close()


def remove_watch(ticker: str):

    session = _session()

    try:

        (
            session.query(UserWatchlist)
            .filter_by(
                user_id=current_user_id(),
                ticker=ticker.upper(),
            )
            .delete()
        )

        session.commit()

    finally:
        session.close()


def get_watchlist():

    session = _session()

    try:

        rows = (
            session.query(
                UserWatchlist
            )
            .filter_by(
                user_id=current_user_id()
            )
            .order_by(
                UserWatchlist.created_at.desc()
            )
            .all()
        )

        return [
            row.ticker
            for row in rows
        ]

    finally:
        session.close()


def add_viewed(ticker: str):

    session = _session()

    try:

        session.add(
            UserViewed(
                user_id=current_user_id(),
                ticker=ticker.upper().strip(),
            )
        )

        session.commit()

    finally:
        session.close()


def get_recently_viewed(
    limit: int = 8,
):

    session = _session()

    try:

        rows = (
            session.query(
                UserViewed
            )
            .filter_by(
                user_id=current_user_id()
            )
            .order_by(
                UserViewed.viewed_at.desc()
            )
            .limit(100)
            .all()
        )

        seen = []

        for row in rows:

            if row.ticker not in seen:

                seen.append(
                    row.ticker
                )

            if len(seen) >= limit:
                break

        return seen

    finally:
        session.close()


def save_prediction(
    ticker: str,
    market_date: str,
    result: dict,
):

    session = _session()

    try:

        session.add(
            UserPrediction(
                user_id=current_user_id(),
                ticker=ticker.upper(),
                market_date=str(
                    market_date
                ),
                model_version=result[
                    "model_version"
                ],
                result_json=json.dumps(
                    result,
                    default=str,
                ),
            )
        )

        session.commit()

    finally:
        session.close()


def get_cached_prediction(
    ticker: str,
    market_date: str,
    model_version: str,
):

    session = _session()

    try:

        row = (
            session.query(
                UserPrediction
            )
            .filter_by(
                user_id=current_user_id(),
                ticker=ticker.upper(),
                market_date=str(
                    market_date
                ),
                model_version=model_version,
            )
            .order_by(
                UserPrediction.created_at.desc()
            )
            .first()
        )

        if row is None:
            return None

        return json.loads(
            row.result_json
        )

    finally:
        session.close()


def save_scan(
    scan_key: str,
    results: list[dict],
):

    session = _session()

    try:

        row = (
            session.query(
                SharedScan
            )
            .filter_by(
                scan_key=scan_key
            )
            .first()
        )

        payload = json.dumps(
            results,
            default=str,
        )

        if row is None:

            row = SharedScan(
                scan_key=scan_key,
                result_json=payload,
            )

            session.add(row)

        else:

            row.result_json = payload

            row.created_at = (
                datetime.now(timezone.utc)
            )

        session.commit()

    finally:
        session.close()


def get_scan(scan_key: str):

    session = _session()

    try:

        row = (
            session.query(
                SharedScan
            )
            .filter_by(
                scan_key=scan_key
            )
            .first()
        )

        if row is None:
            return None

        return json.loads(
            row.result_json
        )

    finally:
        session.close()
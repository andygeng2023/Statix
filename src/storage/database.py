from __future__ import annotations
from datetime import datetime, timezone
import json
from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from src.auth import current_user
from src.config import database_url


def _normalize_database_url(url):
    if not url: return "sqlite:///statix.db"
    v=str(url).strip()
    for prefix in ("postgres://","postgresql://","postgresql+psycopg2://"):
        if v.startswith(prefix): return "postgresql+psycopg://"+v[len(prefix):]
    return v

URL=_normalize_database_url(database_url())
connect_args={"check_same_thread":False} if URL.startswith("sqlite") else {}
engine=create_engine(URL,connect_args=connect_args,pool_pre_ping=True,pool_recycle=1800)
Session=sessionmaker(bind=engine,expire_on_commit=False)

class Base(DeclarativeBase): pass
class Watch(Base):
    __tablename__="watchlist"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[str]=mapped_column(String(128),index=True); ticker:Mapped[str]=mapped_column(String(20)); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc)); __table_args__=(UniqueConstraint("user_id","ticker",name="uq_watch_user_ticker"),)
class View(Base):
    __tablename__="recent_views"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[str]=mapped_column(String(128),index=True); ticker:Mapped[str]=mapped_column(String(20)); viewed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class ScanJob(Base):
    __tablename__="scan_jobs"; id:Mapped[int]=mapped_column(primary_key=True); status:Mapped[str]=mapped_column(String(20),index=True,default="queued"); limit:Mapped[int]=mapped_column(Integer,default=250); requested_by:Mapped[str]=mapped_column(String(128),index=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc)); started_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); finished_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); error:Mapped[str|None]=mapped_column(Text,nullable=True)
class ScanResult(Base):
    __tablename__="scan_results"; id:Mapped[int]=mapped_column(primary_key=True); job_id:Mapped[int]=mapped_column(Integer,index=True); ticker:Mapped[str]=mapped_column(String(20),index=True); signal:Mapped[str]=mapped_column(String(40)); confidence:Mapped[float]=mapped_column(Float); reliability:Mapped[float]=mapped_column(Float); expected_return:Mapped[float]=mapped_column(Float); provider:Mapped[str|None]=mapped_column(String(30),nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Cache(Base):
    __tablename__="scanner_cache"; id:Mapped[int]=mapped_column(primary_key=True); cache_key:Mapped[str]=mapped_column(String(128),unique=True,index=True); payload:Mapped[str]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
Base.metadata.create_all(engine)

def uid():
    u=current_user() or {"id":"anonymous"}; return str(u["id"])
def get_watchlist():
    with Session() as s:return [x.ticker for x in s.query(Watch).filter_by(user_id=uid()).order_by(Watch.created_at.desc()).all()]
def is_watched(t):
    with Session() as s:return s.query(Watch).filter_by(user_id=uid(),ticker=t.upper()).first() is not None
def add_to_watchlist(t):
    with Session() as s:
        if not s.query(Watch).filter_by(user_id=uid(),ticker=t.upper()).first():s.add(Watch(user_id=uid(),ticker=t.upper()));s.commit()
def remove_from_watchlist(t):
    with Session() as s:s.query(Watch).filter_by(user_id=uid(),ticker=t.upper()).delete();s.commit()
def record_view(t):
    with Session() as s:s.query(View).filter_by(user_id=uid(),ticker=t.upper()).delete();s.add(View(user_id=uid(),ticker=t.upper()));s.commit()
def recent(limit=8):
    with Session() as s:return [x.ticker for x in s.query(View).filter_by(user_id=uid()).order_by(View.viewed_at.desc()).limit(limit).all()]

def enqueue_scan(limit=250):
    with Session() as s:
        # Avoid duplicate queued/running scans; one shared scanner serves all users.
        existing=s.query(ScanJob).filter(ScanJob.status.in_(["queued","running"])).order_by(ScanJob.id.desc()).first()
        if existing:return existing.id
        j=ScanJob(status="queued",limit=int(limit),requested_by=uid());s.add(j);s.commit();return j.id

def latest_scan():
    with Session() as s:
        j=s.query(ScanJob).filter_by(status="done").order_by(ScanJob.finished_at.desc()).first()
        if not j:return None,[]
        rows=s.query(ScanResult).filter_by(job_id=j.id).order_by(ScanResult.reliability.desc(),ScanResult.confidence.desc()).limit(25).all()
        return j,[{"Ticker":r.ticker,"Signal":r.signal,"Confidence":r.confidence,"Reliability":r.reliability,"Expected 5D":r.expected_return,"Provider":r.provider} for r in rows]

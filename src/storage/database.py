from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import json, threading
from urllib.parse import urlparse
from sqlalchemy import DateTime,Float,Integer,String,UniqueConstraint,create_engine
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from src.config import database_url
from src.auth import current_user

def norm(url):
 if not url:return "sqlite:///statix.db"
 v=str(url).strip()
 for p in ("postgres://","postgresql://","postgresql+psycopg2://"):
  if v.startswith(p):return "postgresql+psycopg://"+v[len(p):]
 return v
URL=norm(database_url()); is_sqlite=URL.startswith("sqlite")
engine=create_engine(URL,pool_pre_ping=True,pool_recycle=1200,connect_args={"check_same_thread":False} if is_sqlite else {"connect_timeout":10},pool_size=5 if not is_sqlite else 1,max_overflow=10 if not is_sqlite else 0)
Session=sessionmaker(bind=engine,expire_on_commit=False)
class Base(DeclarativeBase):pass
class Watch(Base):
 __tablename__="watchlist"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[str]=mapped_column(String(128),index=True); ticker:Mapped[str]=mapped_column(String(40)); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc)); __table_args__=(UniqueConstraint("user_id","ticker",name="uq_watch_user_ticker"),)
class View(Base):
 __tablename__="recent_views"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[str]=mapped_column(String(128),index=True); ticker:Mapped[str]=mapped_column(String(40)); viewed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Setting(Base):
 __tablename__="user_settings"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[str]=mapped_column(String(128),unique=True,index=True); language:Mapped[str]=mapped_column(String(8),default="en"); provider:Mapped[str]=mapped_column(String(20),default="auto")
_ready=False; _lock=threading.Lock(); _err=None
def ensure_db():
 global _ready,_err
 if _ready:return True
 with _lock:
  if _ready:return True
  try:
   Base.metadata.create_all(engine); _ready=True; return True
  except Exception as e:_err=e; return False
def database_status(): return (True,"Connected") if ensure_db() else (False,"Persistent storage unavailable; check database settings.")
def uid(): return (current_user() or {"id":"anonymous"})["id"]
def get_watchlist():
 if not ensure_db():return []
 with Session() as s:return [x.ticker for x in s.query(Watch).filter_by(user_id=uid()).order_by(Watch.created_at.desc()).all()]
def is_watched(t):
 if not ensure_db():return False
 with Session() as s:return s.query(Watch).filter_by(user_id=uid(),ticker=t.upper()).first() is not None
def add_to_watchlist(t):
 if not ensure_db():return False
 with Session() as s:
  if not s.query(Watch).filter_by(user_id=uid(),ticker=t.upper()).first():s.add(Watch(user_id=uid(),ticker=t.upper()));s.commit()
 return True
def remove_from_watchlist(t):
 if not ensure_db():return False
 with Session() as s:s.query(Watch).filter_by(user_id=uid(),ticker=t.upper()).delete();s.commit()
def record_view(t):
 if not ensure_db():return
 with Session() as s:s.query(View).filter_by(user_id=uid(),ticker=t.upper()).delete();s.add(View(user_id=uid(),ticker=t.upper()));s.commit()
def recent(limit=6):
 if not ensure_db():return []
 with Session() as s:return [x.ticker for x in s.query(View).filter_by(user_id=uid()).order_by(View.viewed_at.desc()).limit(limit).all()]
def get_settings():
 if not ensure_db():return {"language":"en","provider":"auto"}
 with Session() as s:
  x=s.query(Setting).filter_by(user_id=uid()).first(); return {"language":x.language,"provider":x.provider} if x else {"language":"en","provider":"auto"}
def save_settings(language,provider):
 if not ensure_db():return
 with Session() as s:
  x=s.query(Setting).filter_by(user_id=uid()).first()
  if not x:x=Setting(user_id=uid());s.add(x)
  x.language=language;x.provider=provider;s.commit()

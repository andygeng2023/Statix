from __future__ import annotations
from datetime import datetime,timezone
from sqlalchemy import create_engine,String,DateTime,Integer,UniqueConstraint,Text
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,sessionmaker
from src.config import database_url
from src.auth import current_user

URL=database_url() or "sqlite:///statix.db"
connect_args={"check_same_thread":False} if URL.startswith("sqlite") else {}
engine=create_engine(URL,connect_args=connect_args,pool_pre_ping=True,pool_recycle=1800)
Session=sessionmaker(bind=engine,expire_on_commit=False)
class Base(DeclarativeBase): pass
class Watch(Base):
    __tablename__="watchlist"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[str]=mapped_column(String(128),index=True); ticker:Mapped[str]=mapped_column(String(20)); created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc)); __table_args__=(UniqueConstraint("user_id","ticker",name="uq_watch_user_ticker"),)
class View(Base):
    __tablename__="recent_views"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[str]=mapped_column(String(128),index=True); ticker:Mapped[str]=mapped_column(String(20)); viewed_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
Base.metadata.create_all(engine)

def uid(): return (current_user() or {"id":"anonymous"})["id"]
def get_watchlist():
    with Session() as s: return [x.ticker for x in s.query(Watch).filter_by(user_id=uid()).order_by(Watch.created_at.desc()).all()]
def is_watched(t):
    with Session() as s: return s.query(Watch).filter_by(user_id=uid(),ticker=t.upper()).first() is not None
def add_to_watchlist(t):
    with Session() as s:
        t=t.upper()
        if not s.query(Watch).filter_by(user_id=uid(),ticker=t).first(): s.add(Watch(user_id=uid(),ticker=t)); s.commit()
def remove_from_watchlist(t):
    with Session() as s: s.query(Watch).filter_by(user_id=uid(),ticker=t.upper()).delete(); s.commit()
def record_view(t):
    with Session() as s:
        t=t.upper(); s.query(View).filter_by(user_id=uid(),ticker=t).delete(); s.add(View(user_id=uid(),ticker=t)); s.commit()
def recent(limit=8):
    with Session() as s: return [x.ticker for x in s.query(View).filter_by(user_id=uid()).order_by(View.viewed_at.desc()).limit(limit).all()]

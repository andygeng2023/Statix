from __future__ import annotations
"""Persistent Statix scanner worker.
Run outside Streamlit, e.g. on Render/Railway/Fly or another always-on worker.
It uses the shared PostgreSQL database as a durable job queue/cache.
"""
import os, time
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.storage.database import Base, ScanJob, ScanResult, URL
from src.data.market import get_stock_data, get_quote
from src.models.features import create_features
from src.models.model import load_model
from src.config import ROOT, MAX_SCAN

engine=create_engine(URL,pool_pre_ping=True,pool_recycle=1800)
Session=sessionmaker(bind=engine,expire_on_commit=False)


def universe(limit):
    p=ROOT/"training"/"universe.txt"
    return [x.strip().upper() for x in p.read_text().splitlines() if x.strip() and not x.startswith("#")][:min(int(limit),MAX_SCAN)]


def run_job(job_id):
    model=load_model()
    if model is None: raise RuntimeError("Model artifact missing: artifacts/statix_model.pt")
    with Session() as s:
        job=s.get(ScanJob,job_id)
        if not job:return
        job.status="running";job.started_at=datetime.now(timezone.utc);s.commit()
    rows=[]
    for ticker in universe(job.limit):
        try:
            d=get_stock_data(ticker,period="6mo",interval="1d")
            if len(d)<64:continue
            f,_=create_features(d,None,include_target=False)
            if len(f)<64:continue
            X=f[model.feature_columns].tail(64).to_numpy(dtype="float32")
            p=model.predict(X)
            q=get_quote(ticker)
            rows.append({"ticker":ticker,"signal":p["direction"],"confidence":p["confidence"],"reliability":p["reliability"],"expected_return":p["expected_return"],"provider":q.get("provider")})
        except Exception:continue
    rows=sorted(rows,key=lambda x:(x["reliability"],x["confidence"],x["expected_return"]),reverse=True)[:25]
    with Session() as s:
        for r in rows:s.add(ScanResult(job_id=job_id,**r))
        j=s.get(ScanJob,job_id);j.status="done";j.finished_at=datetime.now(timezone.utc);s.commit()


def main():
    poll=float(os.getenv("STATIX_WORKER_POLL_SECONDS","5"))
    while True:
        job_id=None
        with Session() as s:
            j=s.query(ScanJob).filter_by(status="queued").order_by(ScanJob.id.asc()).first()
            if j:job_id=j.id
        if job_id:
            try:run_job(job_id)
            except Exception as exc:
                with Session() as s:
                    j=s.get(ScanJob,job_id)
                    if j:j.status="failed";j.error=str(exc);j.finished_at=datetime.now(timezone.utc);s.commit()
        else:time.sleep(poll)

if __name__=="__main__":main()

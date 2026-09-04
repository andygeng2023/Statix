from __future__ import annotations
import os,time
import pandas as pd
from src.config import MAX_SCAN,SEQUENCE_LENGTH
from src.storage.database import claim_job,finish_job,Session,ScanJob
from src.data.market import get_history,quote
from src.models.features import create_features
from src.models.model import load_model

def universe(limit):
 p="training/universe.txt"; rows=[x.strip().upper() for x in open(p) if x.strip() and not x.startswith("#")]; return rows[:min(int(limit),MAX_SCAN)]

def run(job_id):
 model=load_model()
 if model is None: raise RuntimeError("artifacts/statix_model.joblib is missing. Train the model first.")
 rows=[]
 for ticker in universe(2000):
  try:
   d=get_history(ticker,"1y",400)
   if len(d)<SEQUENCE_LENGTH:continue
   f,_=create_features(d,None,target=False)
   if len(f)<SEQUENCE_LENGTH:continue
   p=model.predict(f[model.feature_columns].tail(SEQUENCE_LENGTH).to_numpy()); q=quote(ticker)
   rows.append({"ticker":ticker,"signal":p["direction"],"confidence":p["confidence"],"reliability":p["reliability"],"expected_return":p["expected_return"],"price":q.get("price"),"change_pct":q.get("change_pct"),"provider":q.get("provider")})
  except Exception: continue
 rows.sort(key=lambda x:(x["reliability"],x["confidence"],x["expected_return"]),reverse=True); return rows[:25]

def main():
 poll=float(os.getenv("STATIX_WORKER_POLL_SECONDS","5"))
 while True:
  jid=claim_job()
  if jid is None: time.sleep(poll); continue
  try: finish_job(jid,run(jid))
  except Exception as e: finish_job(jid,[],e)
if __name__=="__main__":main()

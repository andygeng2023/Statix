from __future__ import annotations
from pathlib import Path
import sys,numpy as np,pandas as pd
from sklearn.metrics import accuracy_score,mean_squared_error
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.data.market import get_history
from src.models.features import create_features
from src.models.model import train_global,save_model,MODEL_VERSION
ROOT=Path(__file__).resolve().parents[1]; UNIVERSE=ROOT/"training"/"universe.txt"
SEQ=64
def seqs(f,cols):
 X=[];y=[];r=[]
 a=f[cols].to_numpy(float); yy=f.target.to_numpy(int); rr=f.future_return.to_numpy(float)
 for i in range(SEQ-1,len(f)):X.append(a[i-SEQ+1:i+1].mean(axis=0));y.append(yy[i]);r.append(rr[i])
 return X,y,r
def main():
 tickers=[x.strip().upper() for x in UNIVERSE.read_text().splitlines() if x.strip() and not x.startswith("#")]; market=get_history("SPY","5y",1500); frames=[];cols=None
 for i,t in enumerate(tickers,1):
  d=get_history(t,"5y",1500)
  if d.empty:continue
  f,cols=create_features(d,market,target=True)
  if len(f)>=180:f["_date"]=f.index;frames.append(f);print(f"[{i}/{len(tickers)}] {t} {len(f)} rows")
 if not frames:raise RuntimeError("No usable training data")

ytr = []
rtr = []

Xte = []
yte = []
rte = []

for frame in frames:
    X, y, r = seqs(frame, cols)

    if len(X) < 100:
        continue

    split = int(len(X) * 0.8)

    Xtr.extend(X[:split])
    ytr.extend(y[:split])
    rtr.extend(r[:split])

    Xte.extend(X[split:])
    yte.extend(y[split:])
    rte.extend(r[split:])

if not Xtr or not Xte:
    raise RuntimeError(
        "Not enough training/validation data."
    )

Xtr = np.asarray(Xtr, dtype=float)
Xte = np.asarray(Xte, dtype=float)

ytr = np.asarray(ytr, dtype=int)
yte = np.asarray(yte, dtype=int)

rtr = np.asarray(rtr, dtype=float)
rte = np.asarray(rte, dtype=float)

 # Build per-symbol sequences is unnecessary because the model consumes compact rolling feature vectors; keep chronological date split.
 for g in frames:
  X,y,r=seqs(g,cols); split=int(len(X)*.8); Xtr+=X[:split];ytr+=y[:split];rtr+=r[:split];Xte+=X[split:];yte+=y[split:];rte+=r[split:]
 Xtr=np.asarray(Xtr);Xte=np.asarray(Xte); ytr=np.asarray(ytr);yte=np.asarray(yte);rtr=np.asarray(rtr);rte=np.asarray(rte)
 logit,hgb,reg,mean,std=train_global(Xtr,ytr,rtr,cols)
 p=(logit.predict_proba((Xte-mean)/(std+1e-8))+hgb.predict_proba((Xte-mean)/(std+1e-8)))/2; pred=p.argmax(1); rp=reg.predict((Xte-mean)/(std+1e-8)); metrics={"training_rows":len(Xtr),"validation_rows":len(Xte),"validation_accuracy":float(accuracy_score(yte,pred)),"validation_rmse":float(np.sqrt(mean_squared_error(rte,rp))),"symbols":len(frames),"model_version":MODEL_VERSION}
 save_model(logit,hgb,reg,cols,mean,std,metrics);print(metrics)
if __name__=="__main__":main()

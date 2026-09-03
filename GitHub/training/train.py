from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
a=Path(__file__).resolve().parents[1]
import sys; sys.path.insert(0,str(a))
from src.data.market import get_stock_data
from src.models.features import create_features
from src.models.model import train_model,save_model
from sklearn.metrics import accuracy_score,mean_squared_error

UNIVERSE=a/"training"/"universe.txt"

def main():
    tickers=[x.strip().upper() for x in UNIVERSE.read_text().splitlines() if x.strip() and not x.startswith("#")]
    frames=[]; feature_cols=None
    print(f"Training on {len(tickers)} symbols")
    for i,t in enumerate(tickers,1):
        try:
            d=get_stock_data(t,period="5y")
            market=get_stock_data("SPY",period="5y")
            f,cols=create_features(d,market,horizon=5,include_target=True)
            f=f.dropna(subset=["target","future_return"])
            if len(f)<250: continue
            f["ticker"]=t; f["_date"]=f.index; frames.append(f); feature_cols=cols
            print(f"[{i}/{len(tickers)}] {t}: {len(f)} rows")
        except Exception as e: print(f"skip {t}: {e}")
    if not frames: raise RuntimeError("No usable training data. Check market data access and universe.txt")
    data=pd.concat(frames,ignore_index=True).dropna(subset=feature_cols+["target","future_return"])
    data=data.sort_values("_date")
    cut=int(len(data)*.8); train=data.iloc[:cut]; test=data.iloc[cut:]
    X=train[feature_cols]; y=train.target.astype(int); yr=train.future_return.astype(float)
    model=train_model(X,y,yr)
    pred_cls=model.clf_a.predict(test[feature_cols]); pred_ret=model.reg.predict(test[feature_cols])
    metrics={"training_rows":int(len(train)),"test_rows":int(len(test)),"test_accuracy":float(accuracy_score(test.target.astype(int),pred_cls)),"test_rmse":float(np.sqrt(mean_squared_error(test.future_return,pred_ret))),"symbols":len(set(data.ticker))}
    save_model(model,feature_cols,metrics); print(metrics)

if __name__=="__main__": main()

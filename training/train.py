from __future__ import annotations
from pathlib import Path
import sys, math
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset,DataLoader
from sklearn.metrics import accuracy_score,mean_squared_error

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.data.market import get_stock_data
from src.models.features import create_features
from src.models.model import PatchTemporalNet,save_model

UNIVERSE=ROOT/"training"/"universe.txt"
SEED=42
np.random.seed(SEED); torch.manual_seed(SEED)


def make_sequences(frame,feature_cols,seq=64):
    x=frame[feature_cols].to_numpy(dtype=np.float32); y=frame.target.to_numpy(dtype=np.int64); r=frame.future_return.to_numpy(dtype=np.float32)
    xs=[]; ys=[]; rs=[]
    for i in range(seq-1,len(frame)):
        xs.append(x[i-seq+1:i+1]); ys.append(y[i]); rs.append(r[i])
    return xs,ys,rs


def main():
    tickers=[x.strip().upper() for x in UNIVERSE.read_text().splitlines() if x.strip() and not x.startswith("#")]
    if not tickers: raise RuntimeError("training/universe.txt is empty")
    market=get_stock_data("SPY",period="5y")
    frames=[]; feature_cols=None
    print(f"Downloading training data for {len(tickers)} symbols…")
    for i,t in enumerate(tickers,1):
        d=get_stock_data(t,period="5y")
        if d.empty: print(f"skip {t}: no data"); continue
        f,cols=create_features(d,market,horizon=5,include_target=True)
        if len(f)<180: print(f"skip {t}: only {len(f)} usable rows"); continue
        f=f.copy(); f["_ticker"]=t; f["_date"]=f.index; frames.append(f); feature_cols=cols
        print(f"[{i}/{len(tickers)}] {t}: {len(f)} rows")
    if not frames: raise RuntimeError("No usable training data")
    # Chronological split by date prevents future leakage across stocks.
    data=pd.concat(frames,ignore_index=True).sort_values("_date")
    unique_dates=np.sort(data["_date"].unique()); cut_date=unique_dates[max(1,int(len(unique_dates)*.8)-1)]
    train=data[data["_date"]<=cut_date].copy(); test=data[data["_date"]>cut_date].copy()
    if len(test)<100: raise RuntimeError("Validation set is too small")
    mean=train[feature_cols].mean().to_numpy(dtype=np.float32); std=train[feature_cols].std().replace(0,1).fillna(1).to_numpy(dtype=np.float32)
    train_norm=train.copy(); test_norm=test.copy()
    train_norm[feature_cols]=(train_norm[feature_cols]-mean)/(std+1e-6); test_norm[feature_cols]=(test_norm[feature_cols]-mean)/(std+1e-6)
    Xtr=[]; ytr=[]; rtr=[]; Xte=[]; yte=[]; rte=[]
    for _,g in train_norm.groupby("_ticker"):
        a,b,c=make_sequences(g,feature_cols)
        Xtr+=a; ytr+=b; rtr+=c
    for _,g in test_norm.groupby("_ticker"):
        a,b,c=make_sequences(g,feature_cols)
        Xte+=a; yte+=b; rte+=c
    if not Xtr or not Xte: raise RuntimeError("Not enough sequences")
    Xtr=torch.tensor(np.asarray(Xtr)); ytr=torch.tensor(np.asarray(ytr)); rtr=torch.tensor(np.asarray(rtr))
    Xte=torch.tensor(np.asarray(Xte)); yte=torch.tensor(np.asarray(yte)); rte=torch.tensor(np.asarray(rte))
    net=PatchTemporalNet(len(feature_cols))
    opt=torch.optim.AdamW(net.parameters(),lr=2e-4,weight_decay=1e-4)
    loss_cls=nn.CrossEntropyLoss(label_smoothing=.04); loss_ret=nn.SmoothL1Loss()
    loader=DataLoader(TensorDataset(Xtr,ytr,rtr),batch_size=256,shuffle=True)
    epochs=12
    net.train()
    for epoch in range(epochs):
        total=0.0
        for xb,yb,rb in loader:
            opt.zero_grad(); logits,ret=net(xb); loss=loss_cls(logits,yb)+0.35*loss_ret(ret,rb); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(),1.0); opt.step(); total+=float(loss.item())*len(xb)
        net.eval()
        with torch.inference_mode():
            logits,ret=net(Xte[:min(len(Xte),4096)]); val=float(loss_cls(logits,yte[:len(logits)]).item())
        net.train(); print(f"epoch {epoch+1}/{epochs} train_loss={total/len(Xtr):.4f} val_cls_loss={val:.4f}")
    net.eval()
    with torch.inference_mode():
        logits,ret=net(Xte); probs=torch.softmax(logits,dim=-1); pred=probs.argmax(dim=-1).numpy(); pret=ret.numpy()
    acc=float(accuracy_score(yte.numpy(),pred)); rmse=float(np.sqrt(mean_squared_error(rte.numpy(),pret)))
    metrics={"training_rows":int(len(Xtr)),"validation_rows":int(len(Xte)),"validation_accuracy":round(acc,4),"validation_rmse":round(rmse,6),"symbols":int(data["_ticker"].nunique()),"model_version":"statix-patchtemporal-v1"}
    save_model(net,feature_cols,mean,std,metrics,temperature=1.0)
    print("Saved artifacts/statix_model.pt")
    print(metrics)

if __name__=="__main__": main()

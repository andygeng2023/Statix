from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import streamlit as st
from src.config import MODEL_PATH,MODEL_META_PATH,MODEL_VERSION,FEATURE_VERSION,SEQUENCE_LENGTH

CLASS_NAMES=["Strong bearish","Bearish","Neutral","Bullish","Strong bullish"]


class PatchTemporalNet(nn.Module):
    def __init__(self,n_features,patch_len=8,d_model=64,n_heads=4,n_layers=2,dropout=0.12):
        super().__init__()
        self.n_features=n_features; self.patch_len=patch_len; self.d_model=d_model
        self.proj=nn.Linear(n_features*patch_len,d_model)
        enc=nn.TransformerEncoderLayer(d_model=d_model,nhead=n_heads,dim_feedforward=d_model*2,dropout=dropout,batch_first=True,norm_first=True,activation="gelu")
        self.encoder=nn.TransformerEncoder(enc,num_layers=n_layers)
        self.norm=nn.LayerNorm(d_model)
        self.class_head=nn.Sequential(nn.Linear(d_model,d_model),nn.GELU(),nn.Dropout(dropout),nn.Linear(d_model,5))
        self.return_head=nn.Sequential(nn.Linear(d_model,d_model//2),nn.GELU(),nn.Linear(d_model//2,1))

    def forward(self,x):
        # x: [batch, sequence, features]. Trim to complete patches.
        b,s,f=x.shape; usable=(s//self.patch_len)*self.patch_len
        x=x[:,:usable,:].reshape(b,usable//self.patch_len,f*self.patch_len)
        z=self.proj(x)
        z=self.encoder(z)
        z=self.norm(z.mean(dim=1))
        return self.class_head(z),self.return_head(z).squeeze(-1)


class StatixModel:
    def __init__(self,net,feature_columns,mean,std,metrics,temperature=1.0):
        self.net=net.eval(); self.feature_columns=feature_columns; self.mean=np.asarray(mean); self.std=np.asarray(std); self.metrics=metrics; self.temperature=float(temperature or 1.0)

    def predict(self,Xseq):
        arr=np.asarray(Xseq,dtype=np.float32)
        if arr.ndim==2: arr=arr[None,:,:]
        arr=(arr-self.mean)/(self.std+1e-6)
        with torch.inference_mode():
            logits,ret=self.net(torch.from_numpy(arr))
            probs=torch.softmax(logits/self.temperature,dim=-1).cpu().numpy()[0]
            expected=float(ret.cpu().numpy()[0])
        idx=int(np.argmax(probs)); confidence=float(np.max(probs))
        # Reliability is deliberately conservative: high confidence is not enough by itself.
        accuracy=float(self.metrics.get("validation_accuracy",0.0))
        reliability=float(np.clip(confidence*(0.55+0.45*accuracy),0,1))
        return {"class_index":idx,"direction":CLASS_NAMES[idx],"class_probabilities":{CLASS_NAMES[i]:float(probs[i]) for i in range(5)},"expected_return":expected,"confidence":confidence,"model_agreement":reliability,"reliability":reliability}


def _build_from_payload(payload):
    cfg=payload["config"]; net=PatchTemporalNet(**cfg); net.load_state_dict(payload["state_dict"])
    return StatixModel(net,payload["feature_columns"],payload["mean"],payload["std"],payload.get("metrics",{}),payload.get("temperature",1.0))


def save_model(net,feature_columns,mean,std,metrics,temperature=1.0):
    MODEL_PATH.parent.mkdir(parents=True,exist_ok=True)
    payload={"config":{"n_features":len(feature_columns),"patch_len":8,"d_model":64,"n_heads":4,"n_layers":2,"dropout":0.12},"state_dict":net.state_dict(),"feature_columns":feature_columns,"mean":np.asarray(mean).tolist(),"std":np.asarray(std).tolist(),"metrics":metrics,"temperature":float(temperature),"model_version":MODEL_VERSION,"feature_version":FEATURE_VERSION}
    torch.save(payload,MODEL_PATH)
    MODEL_META_PATH.write_text(json.dumps({"model_version":MODEL_VERSION,"feature_version":FEATURE_VERSION,"metrics":metrics,"features":feature_columns},indent=2))


@st.cache_resource(ttl=21600,max_entries=4,show_spinner=False)
def load_model():
    if not MODEL_PATH.exists(): return None
    try:
        payload=torch.load(MODEL_PATH,map_location="cpu",weights_only=False)
        return _build_from_payload(payload)
    except Exception:
        return None

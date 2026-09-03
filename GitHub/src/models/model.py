from __future__ import annotations
import json, joblib, numpy as np, pandas as pd
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from src.config import MODEL_PATH, MODEL_VERSION, FEATURE_VERSION

CLASS_NAMES=["Strong bearish","Bearish","Neutral","Bullish","Strong bullish"]

class StatixModel:
    def __init__(self, clf_a, clf_b, reg): self.clf_a=clf_a; self.clf_b=clf_b; self.reg=reg
    def predict(self, X):
        pa=self.clf_a.predict_proba(X); pb=self.clf_b.predict_proba(X); p=(pa+pb)/2
        classes=np.arange(5); direction=int(np.argmax(p[0])); expected=float(self.reg.predict(X)[0]); agreement=float(1-np.mean(np.abs(pa-pb))/2)
        confidence=float(np.max(p[0])); return {"class_index":direction,"direction":CLASS_NAMES[direction],"class_probabilities":{CLASS_NAMES[i]:float(p[0,i]) for i in range(5)},"expected_return":expected,"confidence":confidence,"model_agreement":agreement}

def train_model(X,y_cls,y_ret):
    clf_a=HistGradientBoostingClassifier(max_iter=250,max_leaf_nodes=31,learning_rate=.05,l2_regularization=.5,random_state=42)
    clf_b=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,multi_class="auto",C=.5))
    reg=HistGradientBoostingRegressor(max_iter=250,max_leaf_nodes=31,learning_rate=.05,l2_regularization=.5,random_state=42)
    clf_a.fit(X,y_cls); clf_b.fit(X,y_cls); reg.fit(X,y_ret); return StatixModel(clf_a,clf_b,reg)

def save_model(model, feature_columns, metrics):
    MODEL_PATH.parent.mkdir(parents=True,exist_ok=True)
    joblib.dump({"model":model,"feature_columns":feature_columns,"metrics":metrics,"model_version":MODEL_VERSION,"feature_version":FEATURE_VERSION},MODEL_PATH)

def load_model():
    if not MODEL_PATH.exists(): return None
    return joblib.load(MODEL_PATH)

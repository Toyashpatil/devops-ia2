# python/model_server.py
from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import uvicorn
import os, sys

MODEL_PKL = "model.pkl"
META_PATH = "model_meta.pkl"

if not os.path.exists(MODEL_PKL) or not os.path.exists(META_PATH):
    print("ERROR: model.pkl or model_meta.pkl not found. Run train_model.py first.")
    sys.exit(1)

print("Loading model and metadata...")
clf = joblib.load(MODEL_PKL)
meta = joblib.load(META_PATH)
columns = meta['columns']

class Txn(BaseModel):
    txn_id: str = None
    app: str = None
    psp_candidate: str = None
    src_bank: str = None
    dest_bank: str = None
    amount: float = 0.0
    channel: str = None
    device_type: str = None
    network_latency_ms: float = 100.0
    hour: int = 0
    weekday: int = 0
    recent_fail_rate_src_dest_5m: float = 0.0
    psp_success_rate_5m: float = 0.95

app = FastAPI()

def txn_to_row(txn: Txn):
    # numeric fields
    row = {}
    for c in ['amount','network_latency_ms','hour','recent_fail_rate_src_dest_5m','psp_success_rate_5m']:
        row[c] = float(getattr(txn, c))
    cats = {
        'app': txn.app,
        'psp_candidate': txn.psp_candidate,
        'src_bank': txn.src_bank,
        'dest_bank': txn.dest_bank,
        'channel': txn.channel,
        'device_type': txn.device_type,
        'weekday': str(txn.weekday)
    }
    # fill columns in same order used during training
    values = []
    for col in columns:
        if col in row:
            values.append(row[col])
            continue
        # categorical columns encoded as colname_value
        matched = False
        if "_" in col:
            base, val = col.split("_", 1)
            if base in cats and cats[base] is not None and str(cats[base]) == val:
                values.append(1)
                matched = True
        if not matched:
            values.append(0)
    arr = np.array(values, dtype=float).reshape(1, -1)
    return arr

@app.post("/predict")
def predict(txn: Txn):
    x = txn_to_row(txn)
    prob = float(clf.predict_proba(x)[0][1])
    # clamp
    prob = max(0.0, min(1.0, prob))
    return {"txn_id": txn.txn_id, "failure_probability": round(prob,4)}

@app.get("/health")
def health():   
    return {"status":"ok"}

if __name__ == "__main__":
    uvicorn.run("model_server:app", host="0.0.0.0", port=8000)

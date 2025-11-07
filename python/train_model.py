import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from lightgbm import LGBMClassifier, early_stopping
import lightgbm as lgb
import joblib
import os, sys

CSV_PATH = "transactions.csv"
MODEL_PKL = "model.pkl"
META_PATH = "model_meta.pkl"

if not os.path.exists(CSV_PATH):
    print(f"ERROR: {CSV_PATH} not found. Run generate_data.py first.")
    sys.exit(1)

df = pd.read_csv(CSV_PATH)
if 'status' not in df.columns:
    print("ERROR: 'status' column missing in CSV.")
    sys.exit(1)

df['label'] = (df['status'] == "failure").astype(int)

cat_cols = ['app', 'psp_candidate', 'src_bank', 'dest_bank', 'channel', 'device_type', 'weekday']
num_cols = ['amount', 'network_latency_ms', 'hour', 'recent_fail_rate_src_dest_5m', 'psp_success_rate_5m']

missing = [c for c in cat_cols + num_cols if c not in df.columns]
if missing:
    print("ERROR: missing columns:", missing)
    sys.exit(1)

df_num = df[num_cols].apply(pd.to_numeric, errors='coerce').fillna(0.0)
df_cat = pd.get_dummies(df[cat_cols].astype(str), columns=cat_cols, drop_first=False)

X = pd.concat([df_num.reset_index(drop=True), df_cat.reset_index(drop=True)], axis=1)
y = df['label'].copy()

print("Feature matrix shape:", X.shape)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=True)

# ---- FIXED TRAINING SECTION ----
clf = LGBMClassifier(
    n_estimators=500,
    learning_rate=0.05,
    num_leaves=31,
    random_state=42
)

try:
    clf.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        eval_metric="auc",
        callbacks=[lgb.early_stopping(30, verbose=False)]
    )
except TypeError:
    clf.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        eval_metric="auc",
        early_stopping_rounds=30,
        verbose=False
    )

# Save model and metadata
joblib.dump(clf, MODEL_PKL)
print("Saved model to", MODEL_PKL)

meta = {'columns': list(X.columns)}
joblib.dump(meta, META_PATH)
print("Saved model metadata to", META_PATH)

# Evaluate
y_prob = clf.predict_proba(X_test)[:,1]
auc = roc_auc_score(y_test, y_prob)
pred_label = (y_prob > 0.5).astype(int)
prec, rec, f1, _ = precision_recall_fscore_support(y_test, pred_label, average='binary', zero_division=0)
print(f"AUC: {auc:.4f} Precision: {prec:.4f} Recall: {rec:.4f} F1: {f1:.4f}")

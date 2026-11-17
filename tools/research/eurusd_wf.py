"""Walk-forward evaluation of ML direction models on EURUSD (train 3 years -> test next year)."""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import warnings; warnings.filterwarnings("ignore")
X = pd.read_pickle(os.path.join(os.path.dirname(__file__), "eurusd_feat.pkl"))
FEATS = ["hour", "minute", "dow", "r5m", "r15m", "r1h", "r4h", "r24h", "rsi3", "rsi14", "h1rsi14", "d_ema20", "d_ema100", "h1_trend", "h1_d200",
         "volr", "m5vol", "d_open", "d_high", "d_low", "asia_pos", "asia_size", "prev_ret", "prev_rng", "prev_close_pos", "w_open"]
def clean(X):
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X[(X.atr_h1 > 1e-5) & (X.next_gap <= 600)].copy()
    for k in FEATS:
        if k not in ("hour", "minute", "dow", "rsi3", "rsi14", "h1rsi14"): X[k] = X[k].clip(-10, 10)
    X["asia_pos"] = X.asia_pos.clip(-2, 3)
    X["year"] = pd.to_datetime(X.time, unit="s").dt.year
    return X
X = clean(X)
X = X[X.dow.between(1, 5)]
print("rows", len(X))
res = []
for H in ["y1h", "y2h", "y4h"]:
    for test_y in range(2008, 2019):
        tr = X[(X.year >= test_y - 3) & (X.year < test_y)].dropna(subset=[H]).iloc[::3]
        te = X[X.year == test_y].dropna(subset=[H])
        ytr = (tr[H] > 0).astype(int); yte = (te[H] > 0).astype(int)
        g = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200, l2_regularization=1.0, min_samples_leaf=200)
        g.fit(tr[FEATS], ytr); pg = g.predict_proba(te[FEATS])[:, 1]
        mu, sd = tr[FEATS].mean(), tr[FEATS].std()
        Z = lambda d: ((d[FEATS] - mu) / sd).fillna(0).clip(-5, 5)
        hour_oh = lambda d: pd.get_dummies(d.hour.astype(int)).reindex(columns=range(24), fill_value=0).values
        lr = LogisticRegression(C=0.05, max_iter=500).fit(np.hstack([Z(tr), hour_oh(tr)]), ytr)
        pl = lr.predict_proba(np.hstack([Z(te), hour_oh(te)]))[:, 1]
        res.append(dict(H=H, year=test_y, auc_gbm=roc_auc_score(yte, pg), auc_lr=roc_auc_score(yte, pl),
                        # directional accuracy on the most confident 10%
                        acc_top_gbm=((pg > 0.5) == yte)[np.abs(pg - 0.5) >= np.quantile(np.abs(pg - 0.5), 0.9)].mean(),
                        acc_top_lr=((pl > 0.5) == yte)[np.abs(pl - 0.5) >= np.quantile(np.abs(pl - 0.5), 0.9)].mean()))
    R = pd.DataFrame(res); r = R[R.H == H]
    print(f"{H}: AUC GBM per year {r.auc_gbm.round(3).tolist()} mean {r.auc_gbm.mean():.3f} | LR mean {r.auc_lr.mean():.3f} | top10% acc GBM {r.acc_top_gbm.mean():.3f} LR {r.acc_top_lr.mean():.3f}")
R.to_csv("eurusd_wf_auc.csv", index=False)

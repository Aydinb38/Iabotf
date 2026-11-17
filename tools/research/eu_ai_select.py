"""Walk-forward AI trade selector on top of the prev-range filter: train on all previous years, test next year."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from eu_lib import *
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import warnings; warnings.filterwarnings("ignore")
FE = ["rsi3_sig", "rsi14", "h1rsi14", "r5m", "r15m", "r1h", "r4h", "r24h", "d_ema20", "d_ema100", "h1_trend", "h1_d200", "volr", "m5vol",
      "d_open", "d_high", "d_low", "asia_pos", "asia_size", "prev_ret", "prev_rng", "prev_close_pos", "w_open", "hour", "minute", "dow"]
D = load("ALL").replace([np.inf, -np.inf], np.nan)
D = D[(D.rsi3_sig > 65) & (D.prev_rng >= 6.0)].copy()
TARGET = "E7_be1_hold17"
D["p"] = np.nan; aucs = []
for y in range(2008, 2019):
    tr = D[D.year < y]; te = D[D.year == y]
    g = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=150, l2_regularization=1.0, min_samples_leaf=100)
    g.fit(tr[FE], (tr[TARGET] > 0).astype(int))
    D.loc[te.index, "p"] = g.predict_proba(te[FE])[:, 1]
    aucs.append(round(roc_auc_score((te[TARGET] > 0).astype(int), D.loc[te.index, "p"]), 3))
print("walk-forward AUC per year 2008-2018:", aucs, "mean", round(np.mean(aucs), 3))
T = D[D.year >= 2008]
base = select(T, T.index == T.index)
print("sans IA      :", stats(base, TARGET))
for q in (0.3, 0.5):
    thr = T.groupby("year").p.transform(lambda s: s.quantile(q))   # yearly quantile (uses only the scores, no labels)
    x = select(T, T.p >= thr)
    print(f"IA top {int((1-q)*100)}% :", stats(x, TARGET))

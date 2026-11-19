"""Pires périodes de la v9 et pondération par régime (tendance haussière de l'euro sur plusieurs jours), apprise sur 2007-2018."""
import v6lib as v, numpy as np, pandas as pd
from v10lib import *
E7 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0); HWB = {8: 1.5, 9: 1.0, 10: 0.9, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.2}
res = {}
for src in ("MT5", "2026"):
    X, m1 = v.build_features(src)
    T = broad(src, E7, rsi=65, bb=1.5, prev=6, volr=1.0)
    for c in ["d1_d20", "d1_d50", "h4_d50", "w_open", "r24h", "prev_ret", "h1_trend"]: T[c] = X[c].values[T.i]
    P = v.portfolio(T, 10, 10, 900); P["w"] = P.h.map(HWB); res[src] = P
P = res["MT5"]
# pires périodes (equity en R pondéré)
Q = P.sort_values("exit_t"); eq = (Q.R * Q.w).cumsum().values; pk = np.maximum.accumulate(eq); ddv = pk - eq
i = ddv.argmax(); j = np.argmax(eq[:i + 1]); print("pire baisse :", round(ddv[i], 1), "R du", pd.to_datetime(Q.exit_t.iloc[j], unit="s").date(), "au", pd.to_datetime(Q.exit_t.iloc[i], unit="s").date())
mo = (P.R * P.w).groupby(pd.to_datetime(P.time, unit="s").dt.to_period("M")).sum(); print("pires mois :", mo.nsmallest(6).round(1).to_dict())
tr = P[P.year <= 2018]
for c in ["d1_d20", "d1_d50", "h4_d50", "w_open", "r24h", "prev_ret", "h1_trend"]:
    q = pd.qcut(tr[c], 5, labels=False, duplicates="drop"); g = tr.groupby(q).R.mean().round(3).values
    te = P[P.year >= 2019]; qt = pd.cut(te[c], pd.qcut(tr[c], 5, retbins=True, duplicates="drop")[1], labels=False, include_lowest=True)
    gt = te.groupby(qt).R.mean().round(3).values
    print(f"{c:9s} 2007-2018 quintiles {g}  | 2019-2025 {gt}")

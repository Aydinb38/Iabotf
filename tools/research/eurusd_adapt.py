import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
C = pd.read_pickle(os.path.join(os.path.dirname(__file__), "eurusd_candidates.pkl"))
sel = []; last = {}; cnt = {}
for i, row in C.iterrows():
    d = row.day
    if cnt.get(d, 0) >= 3 or (d in last and row.t - last[d] < 3600): continue
    sel.append(i); last[d] = row.t; cnt[d] = cnt.get(d, 0) + 1
x = C.loc[sel].dropna().reset_index(drop=True)
def evaluate(mult, name):
    r = x.R.values * mult; eq = np.cumsum(r); dd = (np.maximum.accumulate(eq) - eq).max()
    by = pd.Series(r).groupby(x.year).sum()
    print(f"{name:42s} sumR={r.sum():7.1f}  maxDD={dd:5.1f}R  ratio={r.sum()/dd:5.2f}  years+ {(by>0).sum()}/14  worst {by.min():6.1f}  risk moyen {mult.mean():.2f}")
evaluate(np.ones(len(x)), "risque fixe")
for N in (30, 60, 120):
    for low in (0.5, 0.25):
        roll = pd.Series(x.R.values).rolling(N, min_periods=N).sum().shift(1).fillna(0).values
        evaluate(np.where(roll < 0, low, 1.0), f"réduction x{low} si somme {N} derniers < 0")

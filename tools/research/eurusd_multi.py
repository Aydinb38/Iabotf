"""Concurrent positions: every RSI(3) pullback (spaced >= gap minutes) opens its own trade, max K per day.
Each candidate trade is simulated independently (positions may overlap). 14 years."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
f = prep("EURUSD", "ALL")
tod = f["m5"]["time"] % 86400; wk = (f["dow"] >= 1) & (f["dow"] <= 5)
S = wk & (tod >= 10 * 3600 - 300) & (tod < 13 * 3600 - 300) & (f["rsi3"] > 70)
idx = np.flatnonzero(S); idx = idx[idx + 1 < len(f["m5"]["time"])]
sl = 3 * f["h1_atr"]; m1 = f["m1"]
ent = f["m5"]["m1_start"][idx + 1]
cost = PIPS["EURUSD"] * 0.0001 * HOUR_MULT[f["hour"][idx + 1]]
R = np.empty(len(idx))
for k in range(len(idx)):   # independent simulation of every candidate
    r, e = sim(m1["open"], m1["high"], m1["low"], m1["time"], ent[k:k+1], np.array([-1], np.int64), sl[idx[k:k+1]], 3 * sl[idx[k:k+1]], cost[k:k+1], 0.5, 0.1, 99.0, 0.0, 15 * 60, 10**9)
    R[k] = r[0] if len(r) else np.nan
C = pd.DataFrame({"t": f["m5"]["time"][idx], "R": R}); C["day"] = C.t // 86400; C["year"] = pd.to_datetime(C.t, unit="s").dt.year
for gap, K in [(0, 1), (30, 2), (30, 3), (60, 3), (15, 5), (30, 5)]:
    sel = []; last = {}; cnt = {}
    for i, row in C.iterrows():
        d = row.day
        if cnt.get(d, 0) >= K: continue
        if d in last and row.t - last[d] < gap * 60: continue
        if gap == 0 and d in last: continue
        sel.append(i); last[d] = row.t; cnt[d] = cnt.get(d, 0) + 1
    x = C.loc[sel].dropna(); by = x.groupby("year").R.sum()
    print(f"gap {gap:>2}min max {K}/day: n={len(x)} ({len(x)/x.day.nunique():.2f}/jour) win={np.mean(x.R>0)*100:.1f}% pf={x.R[x.R>0].sum()/-x.R[x.R<0].sum():.3f} e={x.R.mean():+.4f} | sumR/yr mean {by.mean():.1f} | years+ {(by>0).sum()}/14 worst {by.min():.1f}")
C.to_pickle("eurusd_candidates.pkl")

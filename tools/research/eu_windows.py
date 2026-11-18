"""Validation of candidate trading windows (EA-like selection: >= 60 min between entries, max 3 per window per day)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
H = os.path.dirname(__file__)
D = pd.read_pickle(os.path.join(H, "eu_c24_ALL.pkl")).replace([np.inf, -np.inf], np.nan)
D26 = pd.read_pickle(os.path.join(H, "eu_c24_OOS2026.pkl")).replace([np.inf, -np.inf], np.nan)
def select(x, gap=3600, K=3):
    x = x.sort_values("time"); keep = []; last = {}; cnt = {}
    for i, t, day in zip(x.index, x.time.values, x.day.values):
        if cnt.get(day, 0) >= K or (day in last and t - last[day] < gap): continue
        keep.append(i); last[day] = t; cnt[day] = cnt.get(day, 0) + 1
    return x.loc[keep]
def st(x, col):
    r = x[col].values
    if len(r) < 5: return "n<5"
    by = x.groupby("year")[col].sum()
    return f"n={len(r)} win={np.mean(r>0)*100:.1f}% pf={r[r>0].sum()/-r[r<0].sum():.2f} e={r.mean():+.3f} sumR={r.sum():.0f} yrs+={int((by>0).sum())}/{len(by)}"
WINDOWS = {
    "SELL 10-13 (v3)": (-1, 10, 13), "SELL 9-14": (-1, 9, 14), "SELL 9-13": (-1, 9, 13), "SELL 10-14": (-1, 10, 14),
    "BUY 19-20": (1, 19, 20), "BUY 18-20": (1, 18, 20), "BUY 19-21": (1, 19, 21), "BUY 18-21": (1, 18, 21),
    "BUY 3-6": (1, 3, 6), "BUY 3-5": (1, 3, 5),
}
for name, (d, a, b) in WINDOWS.items():
    for filt in (0, 6):
        rows = []
        for lab, src in (("2005-11", D[D.year <= 2011]), ("2012-18", D[D.year >= 2012]), ("2026", D26)):
            m = (src.dir == d) & (src.entry_hour >= a) & (src.entry_hour < b) & ((src.prev_rng >= filt) if filt else True)
            x = select(src[m])
            rows.append(f"{lab}: {st(x, 'B')}")
        print(f"{name:16s} filtre>={filt}: " + " | ".join(rows))

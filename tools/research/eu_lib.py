import os, numpy as np, pandas as pd
HERE = os.path.dirname(__file__)
def load(tag="ALL"): return pd.read_pickle(os.path.join(HERE, f"eu_cand_{tag}.pkl"))
def select(D, mask, gap=3600, K=3):
    """EA-like selection: first qualifying signal, next ones >= gap seconds later, max K per day."""
    d = D[mask].sort_values("time"); keep = []; last = {}; cnt = {}
    for i, t, day in zip(d.index, d.time.values, d.day.values):
        if cnt.get(day, 0) >= K or (day in last and t - last[day] < gap): continue
        keep.append(i); last[day] = t; cnt[day] = cnt.get(day, 0) + 1
    return D.loc[keep]
def stats(x, col):
    r = x[col].values
    if len(r) == 0: return dict(n=0)
    by = x.groupby("year")[col].sum()
    eq = np.cumsum(r); dd = (np.maximum.accumulate(eq) - eq).max()
    return dict(n=len(r), per_day=round(len(r) / x.day.nunique(), 2), win=round((r > 0).mean() * 100, 1),
                pf=round(r[r > 0].sum() / max(-r[r < 0].sum(), 1e-9), 3), e=round(r.mean(), 4), sumR=round(r.sum(), 1),
                ddR=round(dd, 1), years_pos=int((by > 0).sum()), n_years=len(by), worst=round(by.min(), 1))

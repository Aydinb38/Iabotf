import os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__))
D = pd.read_pickle(os.path.join(H, "mt5_c24.pkl")).replace([np.inf, -np.inf], np.nan)
print("prev_rng non-null:", D.prev_rng.notna().mean().round(3), "| years", D.year.min(), "-", D.year.max())
D["per"] = pd.cut(D.year, [2006, 2012, 2018, 2025], labels=["07-12", "13-18", "19-25"])
for filt in (0, 6):
    x = D[(D.prev_rng >= filt)] if filt else D
    g = x.groupby(["entry_hour", "dir", "per"], observed=True).B.mean().unstack(["dir", "per"])
    yp = x.groupby(["entry_hour", "dir", "year"]).B.mean().gt(0).groupby(level=[0, 1]).sum().unstack("dir")
    g.columns = [f"{'BUY' if d > 0 else 'SELL'} {p}" for d, p in g.columns]
    g["BUY yrs+/19"] = yp[1]; g["SELL yrs+/19"] = yp[-1]
    print(f"===== mean R per candidate (conditional exit 3h+2h), filtre veille >= {filt} =====")
    print(g.round(3).to_string())

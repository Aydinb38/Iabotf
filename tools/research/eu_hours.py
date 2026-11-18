import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
D = pd.read_pickle(os.path.join(os.path.dirname(__file__), "eu_c24_ALL.pkl")).replace([np.inf, -np.inf], np.nan)
def tab(x, col):
    g = x.groupby(["entry_hour", "dir"])
    s = g[col].agg(n="size", e="mean", win=lambda r: (r > 0).mean() * 100)
    s["pf"] = g[col].apply(lambda r: r[r > 0].sum() / -r[r < 0].sum())
    yp = x.groupby(["entry_hour", "dir", "year"])[col].mean().gt(0).groupby(level=[0, 1]).sum()
    s["years+"] = yp
    return s
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
for filt_name, m in [("SANS filtre", D.index == D.index), ("filtre veille >= 6 ATR", D.prev_rng >= 6)]:
    t = tab(D[m], "B").round(3)
    t = t.reset_index()
    t["dir"] = t["dir"].map({1: "ACHAT", -1: "VENTE"})
    piv = t.pivot(index="entry_hour", columns="dir", values=["e", "win", "pf", "years+"])
    print(f"===== {filt_name} (sortie conditionnelle 3h + maintien 2h) =====")
    print(piv.to_string())

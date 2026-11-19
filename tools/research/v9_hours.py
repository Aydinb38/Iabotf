import v6lib as v, numpy as np, pandas as pd
from v9lib import *
E7 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0)
W = {"v7": HW,
     "A marqué": {8: 1.5, 9: 1.2, 10: 1.0, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.25},
     "B appris": {8: 1.5, 9: 1.0, 10: 0.9, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.2},
     "C très marqué": {8: 1.8, 9: 1.2, 10: 1.0, 11: 1.0, 12: 0.5, 13: 0.3, 14: 0.2},
     "D sans 14h": {8: 1.5, 9: 1.2, 10: 1.0, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.0},
     "E 7h-15h": {7: 0.6, 8: 1.5, 9: 1.2, 10: 1.0, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.25}}
cache = {}
def T_for(src, h0):
    k = (src, h0)
    if k not in cache: cache[k] = broad(src, E7, rsi=65, bb=1.5, prev=6, volr=1.0, h0=h0)
    return cache[k]
rows = []
for name, hw in W.items():
    for mp, gap in [(10, 900), (12, 600), (15, 600)]:
        if name not in ("A marqué", "v7") and (mp, gap) != (10, 900): continue
        out = {}
        for src in ("MT5", "2026"):
            T = T_for(src, 7 if "7h" in name else 8).copy(); T["w"] = T.h.map(hw).fillna(0.0)
            T = T[T.w > 0]
            out[src] = v.portfolio(T, mp, mp, gap)
        e = evaluate(out["MT5"], f"{name} {mp}pos/{gap // 60}min"); e.update(R26w=round((out["2026"].R * out["2026"].w).sum(), 1)); rows.append(e)
pd.set_option("display.width", 260); print(pd.DataFrame(rows).to_string(index=False))

import v6lib as v, numpy as np, pandas as pd
from v10lib import *
E7 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0)
HWB = {8: 1.5, 9: 1.0, 10: 0.9, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.2}
rows = []
for k, valid in [(0.0, 5), (0.05, 15), (0.1, 15), (0.1, 30), (0.2, 30), (0.2, 60), (0.3, 60), (0.5, 120)]:
    out = {}
    for src in ("MT5", "2026"):
        T = limit_trades(src, E7, k, valid, rsi=65, bb=1.5, prev=6, volr=1.0)
        T = T[T.h.between(8, 14)]
        P = v.portfolio(T, 10, 10, 900); P["w"] = P.h.map(HWB); out[src] = P
    lab = f"limite +{k} ATR, {valid} min"
    e = evaluate(out["MT5"], lab); P = out["MT5"]; tr = P[P.year <= 2018]; te = P[P.year >= 2019]
    e.update(Rtrain=round((tr.R * tr.w).sum()), Rtest=round((te.R * te.w).sum()), R26w=round((out["2026"].R * out["2026"].w).sum(), 1))
    rows.append(e); print(e, flush=True)
R = pd.DataFrame(rows); pd.set_option("display.width", 260)
print(R[["label", "n", "win", "PFw", "sumRw", "Rtrain", "Rtest", "sharpe", "mois_pos", "neg_y", "risk_dd", "ret19y", "ret2019", "R26w"]].to_string(index=False))

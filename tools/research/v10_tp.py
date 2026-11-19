import v6lib as v, numpy as np, pandas as pd
from v10lib import *
HWB = {8: 1.5, 9: 1.0, 10: 0.9, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.2}
rows = []
for tp, be in [(2.0, 0.7), (1.0, 0.7), (0.75, 0.5), (0.5, 0.3)]:
    for mp, gap in [(10, 900), (10, 600), (15, 600)]:
        ex = dict(tpR=tp, be_t=be, be_l=0.1, minp=0.05, slk=3.0)
        out = {}
        for src in ("MT5", "2026"):
            T = broad(src, ex, rsi=65, bb=1.5, prev=6, volr=1.0); P = v.portfolio(T, mp, mp, gap); P["w"] = P.h.map(HWB); out[src] = P
        e = evaluate(out["MT5"], f"TP {tp}R BE {be} {mp}pos/{gap // 60}min"); P = out["MT5"]
        e.update(Rtest=round((P[P.year >= 2019].R * P[P.year >= 2019].w).sum()), R26w=round((out["2026"].R * out["2026"].w).sum(), 1)); rows.append(e)
R = pd.DataFrame(rows); pd.set_option("display.width", 260)
print(R[["label", "n", "win", "PFw", "sumRw", "R1", "R2", "R3", "sharpe", "mois_pos", "neg_y", "risk_dd", "ret19y", "ret2019", "R26w"]].to_string(index=False))

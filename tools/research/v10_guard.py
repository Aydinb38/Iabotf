import v6lib as v, numpy as np, pandas as pd
from v10lib import *
E7 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0)
HWB = {8: 1.5, 9: 1.0, 10: 0.9, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.2}
D = {src: prepare(src, E7, rsi=65, bb=1.5, prev=6, volr=1.0) for src in ("MT5", "2026")}
rows = []
for mp, gap in [(10, 900), (15, 600), (20, 600)]:
    for mode, ths in [(0, [0.0]), (1, [-0.5, -0.3, -0.15, 0.0]), (2, [-0.5, -0.3, -0.15, 0.0]), (3, [-0.5, -0.3])]:
        for th in ths:
            out = {}
            for src, T in D.items():
                P = portfolio_guard(T, mp, mp, gap, mode, th); P["w"] = P.h.map(HWB); out[src] = P
            lab = f"{mp}pos/{gap // 60}min garde{mode}@{th:+.2f}"
            e = evaluate(out["MT5"], lab)
            P = out["MT5"]; tr = P[P.year <= 2018]; te = P[P.year >= 2019]
            e.update(Rtrain=round((tr.R * tr.w).sum()), Rtest=round((te.R * te.w).sum()), R26w=round((out["2026"].R * out["2026"].w).sum(), 1))
            rows.append(e)
R = pd.DataFrame(rows); pd.set_option("display.width", 260)
print(R[["label", "n", "win", "PFw", "sumRw", "Rtrain", "Rtest", "sharpe", "mois_pos", "neg_y", "risk_dd", "ret19y", "ret2019", "R26w"]].to_string(index=False))
R.to_csv("v6_cache/guard_v10.csv", index=False)

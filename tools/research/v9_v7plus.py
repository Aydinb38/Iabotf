"""Améliorer la v7 à drawdown égal : RSI 60, poids horaires plus marqués, TP 3 R, risque adaptatif sur la courbe de gains."""
import v6lib as v, numpy as np, pandas as pd
from v9lib import *
E7 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0); E7tp3 = dict(E7, tpR=3.0)
HW_steep = {8: 1.5, 9: 1.2, 10: 1.0, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.25}
HW_flat = {h: 1.0 for h in range(24)}
rows = []
def run(lab, ex, rsi, hw, mp=10, gap=900, adapt=None, src_list=("MT5", "2026")):
    out = {}
    for src in src_list:
        T = broad(src, ex, rsi=rsi, bb=1.5, prev=6, volr=1.0)
        P = v.portfolio(T, mp, mp, gap); P["w"] = P.h.map(hw).astype(float)
        if adapt:
            win, fac = adapt
            Q = P.sort_values("exit_t").reset_index(drop=True)
            # risque réduit si la somme des R des `win` derniers trades CLÔTURÉS avant l'entrée est négative
            ex_t = Q.exit_t.values; rr = Q.R.values; order = np.argsort(ex_t); cs = np.r_[0, np.cumsum(rr[order])]
            P = P.sort_values("entry_t").reset_index(drop=True)
            k = np.searchsorted(np.sort(ex_t), P.entry_t.values, side="right")
            s = cs[k] - cs[np.maximum(k - win, 0)]
            P["w"] = P.w * np.where((k >= win) & (s < 0), fac, 1.0)
        out[src] = P
    e = evaluate(out["MT5"], lab); e.update(R26w=round((out["2026"].R * out["2026"].w).sum(), 1)); rows.append(e)
run("v7 (référence)", E7, 65, HW)
run("v7 RSI>60", E7, 60, HW)
run("v7 poids horaires marqués", E7, 65, HW_steep)
run("v7 sans poids horaires", E7, 65, HW_flat)
run("v7 TP 3R", E7tp3, 65, HW)
for win in (30, 60, 120):
    run(f"v7 risque adaptatif {win} trades x0.5", E7, 65, HW, adapt=(win, 0.5))
run("v7 RSI>60 + TP3 + poids marqués", E7tp3, 60, HW_steep)
pd.set_option("display.width", 260); R = pd.DataFrame(rows); print(R.to_string(index=False))

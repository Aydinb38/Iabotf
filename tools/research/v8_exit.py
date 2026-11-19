"""Grille des sorties sur les entrées v7 (pondération horaire incluse) : taux de réussite, gain normalisé au drawdown, régularité, 2026."""
import v6lib as v, numpy as np, pandas as pd, itertools
from v7_final import mask
W = {8: 1.5, 9: 1.5, 10: 1.5, 11: 1.0, 12: 1.0, 13: 0.5, 14: 0.5}
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
D = {}
for src in ["MT5", "2026"]:
    X, m1 = v.build_features(src); tod = ((X.time.values + 300) % 86400) // 60
    D[src] = (X, m1, tod, mask(X, tod))
rows = []
for slk, tp, be, minp, t2 in itertools.product([2.5, 3.0, 3.5, 4.0], [1.5, 2.0, 3.0], [0.5, 0.7, 1.0], [0.0, 0.05, 0.15], [17, 18, 19]):
    r = dict(slk=slk, tp=tp, be=be, minp=minp, t2=t2)
    for src in ["MT5", "2026"]:
        X, m1, tod, m = D[src]
        P = v.portfolio(v.run(X, m1, m, -1, tpR=tp, be_t=be, be_l=0.1, minp=minp, slk=slk, t2=t2 * 60), 10, 10, 900)
        P["R"] = P.R * np.array([W[int(h)] for h in tod[P.i] // 60])
        if src == "MT5":
            n = v.norm(P, 15.0); p = per(P.time.values)
            mo = P.groupby(pd.to_datetime(P.time, unit="s").dt.to_period("M")).R.sum()
            r.update(n=len(P), win=round((P.R > 0).mean() * 100, 1), PF=v.stats(P)["PF"], ret19y=n["ret19y"], ret2019=n["ret2019"],
                     R1=round(P.R[p == 1].sum()), R2=round(P.R[p == 2].sum()), R3=round(P.R[p == 3].sum()), mois_pos=round((mo > 0).mean() * 100, 1),
                     neg_y=int((P.groupby("year").R.sum() < 0).sum()))
        else:
            r.update(R2026=round(P.R.sum(), 1), win2026=round((P.R > 0).mean() * 100, 1))
    rows.append(r)
G = pd.DataFrame(rows); G.to_csv("v6_cache/exit_v8.csv", index=False)
pd.set_option("display.width", 250)
print(G.sort_values("ret19y", ascending=False).head(20).to_string(index=False))
print(G.sort_values("win", ascending=False).head(20).to_string(index=False))
base = G[(G.slk == 3.0) & (G.tp == 2.0) & (G.be == 0.7) & (G.minp == 0.05) & (G.t2 == 17)]; print("v7:", base.to_string(index=False))

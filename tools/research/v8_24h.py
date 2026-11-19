"""24h : chaque heure d'entrée, vente des excès haussiers et achat des excès baissiers (logique v7 : RSI(3) + Bollinger 1,5),
sortie conditionnelle 3h après l'entrée, maintien 2h max. Validé sur 2007-2012 / 2013-2018 / 2019-2025 / 2026."""
import v6lib as v, numpy as np, pandas as pd
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
rows = []
for src in ["MT5", "2026"]:
    X, m1 = v.build_features(src); tod = ((X.time.values + 300) % 86400) // 60; hr = tod // 60
    base = ((X.dow >= 1) & (X.dow <= 5)).values & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) & np.isfinite(X.atr.values)
    for d, sig in [(-1, (X.rsi3.values > 65) & (X.bb.values > 1.5)), (1, (X.rsi3.values < 35) & (X.bb.values < -1.5))]:
        for flt, fm in [("aucun", np.ones(len(X), bool)), ("veille>=6 & vol<=1", (X.prev_rng.values >= 6) & (X.volr.values <= 1.0))]:
            m = base & sig & fm & (hr >= 1) & (hr <= 18)
            t1 = (hr + 3) * 60; t2 = (hr + 5) * 60
            T = v.run(X, m1, m, d, tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0, t1=t1, t2=t2)
            T["h"] = hr[T.i]
            for h, g in T.groupby("h"):
                P = v.portfolio(g, 3, 3, 1800); p = per(P.time.values) if src == "MT5" else np.full(len(P), 4)
                r = dict(src=src, sens="VENTE" if d < 0 else "ACHAT", filtre=flt, h=h, n=len(P), win=round((P.R > 0).mean() * 100, 1))
                for k in ((1, 2, 3) if src == "MT5" else (4,)):
                    r[f"e{k}"] = round(P.R[p == k].mean(), 3) if (p == k).any() else np.nan
                rows.append(r)
R = pd.DataFrame(rows)
A = R[R.src == "MT5"].merge(R[R.src == "2026"][["sens", "filtre", "h", "e4", "n"]].rename(columns={"n": "n26"}), on=["sens", "filtre", "h"], how="left")
A["min3"] = A[["e1", "e2", "e3"]].min(axis=1)
pd.set_option("display.width", 250)
print(A.sort_values(["sens", "filtre", "h"]).to_string(index=False))
A.to_csv("v6_cache/scan24_v8.csv", index=False)

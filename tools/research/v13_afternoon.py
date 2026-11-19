"""Module d'après-midi : après une forte baisse (ou hausse) de l'EURUSD depuis l'ouverture du jour, position inverse en séance US."""
import v6lib as v, numpy as np, pandas as pd
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
rows = []
for src in ("MT5", "2026"):
    X, m1 = v.build_features(src); tod = ((X.time.values + 300) % 86400) // 60
    wk = ((X.dow >= 1) & (X.dow <= 5)).values & (X.spread.values <= 20) & np.isfinite(X.atr.values)
    for e_min in (930, 960, 1020):
        at = wk & (tod == e_min)
        for d, cond_name in [(1, "achat après baisse"), (-1, "vente après hausse")]:
            for k in (1.0, 2.0, 3.0):
                cond = (X.d_open.values <= -k) if d > 0 else (X.d_open.values >= k)
                for xh in (19, 21):
                    for slk in (1.5, 3.0):
                        T = v.run(X, m1, at & cond, d, tpR=3.0, be_t=99, be_l=0, t1=xh * 60, t2=xh * 60, minp=99, slk=slk)
                        if len(T) == 0: continue
                        p = per(T.time.values) if src == "MT5" else np.full(len(T), 4)
                        r = dict(src=src, entree=f"{e_min // 60}h{e_min % 60:02d}", sens=cond_name, k=k, sortie=xh, sl=slk, n=len(T))
                        for q in ((1, 2, 3) if src == "MT5" else (4,)):
                            r[f"e{q}"] = round(T.R[p == q].mean(), 3) if (p == q).any() else np.nan
                        rows.append(r)
R = pd.DataFrame(rows)
A = R[R.src == "MT5"].merge(R[R.src == "2026"][["entree", "sens", "k", "sortie", "sl", "e4", "n"]].rename(columns={"n": "n26"}), on=["entree", "sens", "k", "sortie", "sl"], how="left")
A["min3"] = A[["e1", "e2", "e3"]].min(axis=1)
pd.set_option("display.width", 220)
print(A.sort_values("min3", ascending=False).head(25).to_string(index=False))
print("configurations positives sur les 3 périodes :", (A.min3 > 0).sum(), "sur", len(A))

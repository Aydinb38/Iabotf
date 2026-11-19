import v6lib as v, numpy as np, pandas as pd
from v7_final import mask
W = {8: 1.5, 9: 1.5, 10: 1.5, 11: 1.0, 12: 1.0, 13: 0.5, 14: 0.5}
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
EX8 = dict(tpR=2.0, be_t=0.5, be_l=0.1, minp=0.05, slk=3.5)
def asia8(X):
    """amplitude 1h-8h (heure serveur) du jour, en ATR H1, disponible à partir de 8h"""
    t = X.time.values; day = t // 86400; tod = t % 86400
    s = pd.DataFrame({"day": day, "h": X.close.values, "tod": tod})
    m1h = pd.Series(np.where((tod >= 3600) & (tod < 8 * 3600), 1, 0))
    # max/min des clôtures M5 sur 1h-8h (approximation de l'amplitude)
    sub = s[(tod >= 3600) & (tod < 8 * 3600)].groupby("day").h.agg(["max", "min"])
    rng = pd.Series(day).map(sub["max"] - sub["min"]).values
    return np.where(tod >= 8 * 3600 - 300, rng / X.atr.values, np.nan)
rows = []
res = {}
for src in ["MT5", "2026"]:
    X, m1 = v.build_features(src); tod = ((X.time.values + 300) % 86400) // 60
    X["asia8"] = asia8(X)
    base = mask(X, tod)
    T = v.run(X, m1, base, -1, **EX8)
    for c in ["volr", "asia8"]: T[c] = X[c].values[T.i]
    T["w"] = [W[int(h)] for h in tod[T.i] // 60]
    res[src] = T
qs = res["MT5"].asia8.quantile([0.2, 0.4]).round(2).tolist(); print("asia8 quantiles 20/40 %:", qs)
for lab, f in [("v8 base (sortie 3,5 ATR / BE 0,5)", lambda T: np.ones(len(T), bool)),
               ("volr<=0.9", lambda T: T.volr <= 0.9), ("volr<=0.8", lambda T: T.volr <= 0.8),
               (f"asia8>={qs[0]}", lambda T: T.asia8 >= qs[0]), (f"asia8>={qs[1]}", lambda T: T.asia8 >= qs[1]),
               (f"volr<=0.9 & asia8>={qs[0]}", lambda T: (T.volr <= 0.9) & (T.asia8 >= qs[0]))]:
    r = dict(filtre=lab)
    for src in ["MT5", "2026"]:
        T = res[src]; S = T[f(T).values if hasattr(f(T), "values") else f(T)]
        P = v.portfolio(S, 10, 10, 900); P["R"] = P.R * P.w
        if src == "MT5":
            n = v.norm(P, 15.0); p = per(P.time.values); mo = P.groupby(pd.to_datetime(P.time, unit="s").dt.to_period("M")).R.sum()
            r.update(n=len(P), win=round((P.R > 0).mean() * 100, 1), PF=v.stats(P)["PF"], ret19y=n["ret19y"], ret2019=n["ret2019"],
                     R1=round(P.R[p == 1].sum()), R2=round(P.R[p == 2].sum()), R3=round(P.R[p == 3].sum()), mois_pos=round((mo > 0).mean() * 100, 1),
                     neg_y=int((P.groupby("year").R.sum() < 0).sum()))
        else:
            r.update(n26=len(P), win26=round((P.R > 0).mean() * 100, 1), R26=round(P.R.sum(), 1))
    rows.append(r)
pd.set_option("display.width", 250); print(pd.DataFrame(rows).to_string(index=False))

import v6lib as v, numpy as np, pandas as pd
from v7_final import mask
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
X, m1 = v.build_features("MT5"); tod = ((X.time.values + 300) % 86400) // 60
EX8 = dict(tpR=2.0, be_t=0.5, be_l=0.1, minp=0.05, slk=3.5)
T = v.run(X, m1, mask(X, tod), -1, **EX8); P = v.portfolio(T, 10, 10, 900)
for c in ["bb", "rsi3", "prev_rng", "volr", "d_ema50", "r1h", "asia_size", "dow", "month", "dom", "h1_adx", "d_low", "atr"]:
    P[c] = X[c].values[P.i]
P["h"] = tod[P.i] // 60; P["per"] = per(P.time.values)
P["pos_jour"] = P.groupby("day").cumcount() + 1          # rang de l'entrée dans la journée
for c in ["bb", "rsi3", "prev_rng", "volr", "d_ema50", "r1h", "asia_size", "h1_adx", "d_low", "atr", "pos_jour"]:
    q = pd.qcut(P[c].rank(method="first"), 5, labels=False) if P[c].nunique() > 5 else P[c]
    g = P.groupby([q, "per"]).R.mean().unstack().round(3)
    print(c, "| quintiles (moyenne R par période) :", " ; ".join(f"q{i}: " + "/".join(f"{x:+.2f}" for x in g.loc[i].values) for i in g.index))
for c in ["dow", "h", "month"]:
    g = P.groupby([c, "per"]).R.mean().unstack().round(3); print(c, " ; ".join(f"{i}: " + "/".join(f"{x:+.2f}" for x in g.loc[i].values) for i in g.index))
P.to_pickle("v6_cache/P_v8.pkl")

import v6lib as v, numpy as np, pandas as pd, itertools
X, m1 = v.build_features()
tb = X.time.values + 300; tod = (tb % 86400) // 60
wk = ((X.dow >= 2) & (X.dow <= 5)).values
filt = wk & (X.day_fomc.values == 0) & (X.month_end.values == 0)
m = filt & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) & (tod >= 7 * 60) & (tod < 15 * 60) & (X.rsi3.values > 60) & (X.prev_rng.values >= 5) & (X.volr.values <= 1.3)
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
T = v.run(X, m1, m, -1, tpR=2.0, be_t=0.7, be_l=0.1, t1=15 * 60, t2=17 * 60, minp=0.05, slk=4.0)
for c in ["rsi3", "prev_rng", "volr", "s_EUR_day"]: T[c] = X[c].values[T.i]
T["tod"] = tod[T.i]
rows = []
for h0, h1, rs, pv, vr, eur, (mp, gap) in itertools.product([7, 8, 9], [14, 15], [60, 65, 70], [5, 6], [1.1, 1.3], [-99, -1.0, -0.5, 0.0], [(4, 30), (6, 30), (8, 20), (10, 15), (12, 10)]):
    S = T[(T.tod >= h0 * 60) & (T.tod < h1 * 60) & (T.rsi3 > rs) & (T.prev_rng >= pv) & (T.volr <= vr) & (T.s_EUR_day > eur)]
    P = v.portfolio(S, mp, mp, gap * 60); p = per(P.time.values); y = P.groupby("year").R.sum()
    r = v.norm(P, 20.0); s = v.stats(P, 0.5)
    r.update(h0=h0, h1=h1, rsi=rs, prev=pv, volr=vr, eur=eur, mp=mp, gap=gap, exp=s["exp"], R1=round(P.R[p == 1].sum()), R2=round(P.R[p == 2].sum()), R3=round(P.R[p == 3].sum()), neg=int((y < 0).sum()), worst=round(y.min()))
    rows.append(r)
G = pd.DataFrame(rows); G.to_csv("v6_cache/grid3.csv", index=False)
pd.set_option("display.width", 250)
cols = ["h0", "h1", "rsi", "prev", "volr", "eur", "mp", "gap", "n", "win", "PF", "exp", "risk", "ret19y", "ret2019", "dd2019", "R1", "R2", "R3", "neg", "worst"]
print(G.sort_values("ret19y", ascending=False)[cols].head(25).to_string(index=False))
print(G.sort_values("ret2019", ascending=False)[cols].head(10).to_string(index=False))
print(G.groupby("eur")[["ret19y", "ret2019", "win", "PF"]].median()); print(G.groupby(["mp"])[["ret19y", "ret2019", "win", "PF", "n"]].median())
print(G.groupby("h0")[["ret19y", "ret2019", "win", "PF", "n"]].median()); print(G.groupby("rsi")[["ret19y", "ret2019", "win", "PF", "n"]].median())

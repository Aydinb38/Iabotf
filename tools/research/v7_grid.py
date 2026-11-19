import v6lib as v, numpy as np, pandas as pd, itertools
X, m1 = v.build_features("MT5")
tb = X.time.values + 300; tod = (tb % 86400) // 60
wk = ((X.dow >= 2) & (X.dow <= 5)).values
m = wk & (X.day_fomc.values == 0) & (X.month_end.values == 0) & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) \
    & (tod >= 420) & (tod < 900) & (X.rsi3.values > 60) & (X.prev_rng.values >= 5) & (X.volr.values <= 1.2)
EX = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=4.0)
T = v.run(X, m1, m, -1, **EX)
for c in ["rsi3", "bb", "prev_rng", "volr", "d_ema50"]: T[c] = X[c].values[T.i]
T["tod"] = tod[T.i]
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
rows = []
for h0, rs, bbt, pv, vr, (mp, gap) in itertools.product([7, 8], [60, 65, 70], [0.5, 1.0, 1.5, 2.0], [5, 6], [1.0, 1.1], [(6, 1800), (10, 900), (12, 600), (15, 600)]):
    S = T[(T.tod >= h0 * 60) & (T.rsi3 > rs) & (T.bb > bbt) & (T.prev_rng >= pv) & (T.volr <= vr)]
    P = v.portfolio(S, mp, mp, gap); p = per(P.time.values); y = P.groupby("year").R.sum()
    r = v.norm(P, 15.0); s = v.stats(P, 0.2)
    r.update(h0=h0, rsi=rs, bb=bbt, prev=pv, volr=vr, mp=mp, gap=gap // 60, exp=s["exp"], R1=round(P.R[p == 1].sum()), R2=round(P.R[p == 2].sum()),
             R3=round(P.R[p == 3].sum()), neg=int((y < 0).sum()), worst=round(y.min()))
    rows.append(r)
G = pd.DataFrame(rows); G.to_csv("v6_cache/grid_v7.csv", index=False)
pd.set_option("display.width", 250)
cols = ["h0", "rsi", "bb", "prev", "volr", "mp", "gap", "n", "win", "PF", "exp", "risk", "ret19y", "ret2019", "R1", "R2", "R3", "neg", "worst"]
print(G.sort_values("ret19y", ascending=False)[cols].head(25).to_string(index=False))
for c in ["h0", "rsi", "bb", "prev", "volr", "mp"]:
    print(G.groupby(c)[["n", "win", "PF", "ret19y", "ret2019"]].median().round(2).to_string())

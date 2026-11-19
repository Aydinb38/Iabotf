import v6lib as v, numpy as np, pandas as pd, itertools, sys
X, m1 = v.build_features()
tb = X.time.values + 300; tod = (tb % 86400) // 60; hr = tod // 60
wk = ((X.dow >= 1) & (X.dow <= 5)).values
base = wk & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) & (X.rsi3.values > 60) & (tod >= 8 * 60) & (tod < 15 * 60)
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
rows = []
for t1, t2 in [(15, 17), (16, 18), (15, 18)]:
    T = v.run(X, m1, base, -1, t1=t1 * 60, t2=t2 * 60)
    T["tod"] = tod[T.i]; T["rsi"] = X.rsi3.values[T.i]; T["prev"] = X.prev_rng.values[T.i]; T["volr"] = X.volr.values[T.i]
    for h0, h1, rs, pv, vr in itertools.product([8, 9, 10, 11], [13, 14, 15], [60, 65, 70], [0, 5, 6], [99, 1.1, 1.3]):
        if h1 > t1: continue
        S = T[(T.tod >= h0 * 60) & (T.tod < h1 * 60) & (T.rsi > rs) & (T.prev >= pv) & (T.volr <= vr)]
        for mp, gap in [(2, 60), (3, 60), (4, 60), (3, 30), (5, 30), (6, 30)]:
            P = v.portfolio(S, mp, mp, gap * 60)
            s = v.stats(P); p = per(P.time.values); y = P.groupby("year").R.sum()
            rows.append(dict(t1=t1, t2=t2, h0=h0, h1=h1, rsi=rs, prev=pv, volr=vr, mp=mp, gap=gap, n=s["n"], win=s["win"], PF=s["PF"],
                             ret=s["ret"], dd=s["dd"], R=s["sumR"], R1=round(P.R[p == 1].sum(), 1), R2=round(P.R[p == 2].sum(), 1),
                             R3=round(P.R[p == 3].sum(), 1), neg=int((y < 0).sum()), worst=round(y.min(), 1)))
    print("exit", t1, t2, "done", len(rows), flush=True)
G = pd.DataFrame(rows); G["rdd"] = (G.ret / G.dd).round(2); G["minP"] = G[["R1", "R2", "R3"]].min(axis=1)
G.to_csv("v6_cache/grid.csv", index=False)
pd.set_option("display.width", 250)
print(G.sort_values("rdd", ascending=False).head(25).to_string(index=False))
print(G[G.minP > 15].sort_values("R", ascending=False).head(25).to_string(index=False))

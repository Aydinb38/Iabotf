import v6lib as v, numpy as np, pandas as pd, itertools
X, m1 = v.build_features()
tb = X.time.values + 300; tod = (tb % 86400) // 60
wk = ((X.dow >= 2) & (X.dow <= 5)).values  # no Monday
filt = wk & (X.day_fomc.values == 0) & (X.month_end.values == 0) & (X.s_EUR_day.values > -0.5)
base = filt & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) & (tod >= 7 * 60) & (tod < 15 * 60) & (X.rsi3.values > 60) & (X.prev_rng.values >= 5) & (X.volr.values <= 1.3)
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
rows = []
for t1, t2 in [(15, 17), (16, 18), (15, 18), (14, 17)]:
    T = v.run(X, m1, base, -1, t1=t1 * 60, t2=t2 * 60)
    T["tod"] = tod[T.i]; T["rsi"] = X.rsi3.values[T.i]; T["prev"] = X.prev_rng.values[T.i]; T["volr"] = X.volr.values[T.i]
    for h0, h1, rs, pv, vr in itertools.product([7, 8, 9], [13, 14, 15], [60, 65, 70], [5, 6], [1.1, 1.3]):
        if h1 > t1: continue
        S = T[(T.tod >= h0 * 60) & (T.tod < h1 * 60) & (T.rsi > rs) & (T.prev >= pv) & (T.volr <= vr)]
        for mp, gap in [(3, 60), (4, 30), (6, 30), (8, 20), (10, 15)]:
            P = v.portfolio(S, mp, mp, gap * 60); p = per(P.time.values); y = P.groupby("year").R.sum()
            r = v.norm(P, 20.0); s = v.stats(P, 0.5)
            r.update(t1=t1, t2=t2, h0=h0, h1=h1, rsi=rs, prev=pv, volr=vr, mp=mp, gap=gap, exp=s["exp"], R1=round(P.R[p == 1].sum()), R2=round(P.R[p == 2].sum()),
                     R3=round(P.R[p == 3].sum()), neg=int((y < 0).sum()), worst=round(y.min()))
            rows.append(r)
    print("exit", t1, t2, len(rows), flush=True)
G = pd.DataFrame(rows); G.to_csv("v6_cache/grid2.csv", index=False)
pd.set_option("display.width", 250)
cols = ["t1", "t2", "h0", "h1", "rsi", "prev", "volr", "mp", "gap", "n", "win", "PF", "exp", "risk", "ret19y", "ret2019", "R1", "R2", "R3", "neg", "worst"]
print(G.sort_values("ret19y", ascending=False)[cols].head(30).to_string(index=False))
print(G.sort_values("ret2019", ascending=False)[cols].head(15).to_string(index=False))

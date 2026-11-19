import v6lib as v, numpy as np, pandas as pd
X, m1 = v.build_features()
tb = X.time.values + 300; tod = (tb % 86400) // 60; hr = tod // 60
wk = ((X.dow >= 1) & (X.dow <= 5)).values
per = np.select([X.time < 1356998400, X.time < 1546300800], [1, 2], 3)  # 2007-12, 2013-18, 2019-25
base = wk & (X.spread.values <= 20) & np.isfinite(X.atr.values)
rows = []
for d, cond in [(-1, X.rsi3.values > 65), (1, X.rsi3.values < 35)]:
    m = base & cond & (hr >= 1) & (hr <= 21)
    t1 = np.minimum((hr + 3) * 60, 22 * 60); t2 = np.minimum(t1 + 120, 23 * 60 + 30)
    T = v.run(X, m1, m, d, t1=t1, t2=t2)
    T["hr"] = hr[T.i]; T["per"] = per[T.i]; T["prev6"] = X.prev_rng.values[T.i] >= 6
    for (h, p6), g in T.groupby(["hr", "prev6"]):
        r = {"dir": "SELL" if d < 0 else "BUY", "hr": h, "prev>=6": p6, "n": len(g), "win": round((g.R > 0).mean() * 100, 1)}
        for p in (1, 2, 3):
            gg = g[g.per == p]; r[f"exp{p}"] = round(gg.R.mean(), 3)
        rows.append(r)
R = pd.DataFrame(rows); pd.set_option("display.width", 200)
print(R.to_string(index=False))

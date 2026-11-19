import v6lib as v, numpy as np, pandas as pd
from v6_final import mask, EX
X, m1 = v.build_features("2026")
tb = X.time.values + 300; tod = (tb % 86400) // 60
print("FOMC days flagged:", sorted(set(pd.to_datetime(X.time[X.day_fomc == 1], unit="s").dt.date.astype(str))))
for lab, kw, mp, gap in [("v6", {}, 10, 900), ("v6 6pos", {}, 6, 1800)]:
    T = v.run(X, m1, mask(X, tod, **kw), -1, **EX); P = v.portfolio(T, mp, mp, gap)
    print(lab, v.stats(P, 0.3))
# v5 replica on the same data
wk = ((X.dow >= 1) & (X.dow <= 5)).values
m5 = wk & (tod >= 660) & (tod < 840) & (X.rsi3.values > 65) & (X.prev_rng.values >= 6) & (X.volr.values <= 1.1)
P5 = v.portfolio(v.run(X, m1, m5, -1), 2, 2, 3600); print("v5", v.stats(P5, 0.5))

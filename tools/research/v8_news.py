"""v8 : effet des annonces par type (jour de NFP, CPI US, BCE ; annonce majeure pendant la durée du trade)."""
import v6lib as v, numpy as np, pandas as pd
from v7_final import mask
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
X, m1 = v.build_features("MT5"); tod = ((X.time.values + 300) % 86400) // 60
t = X.time.values; day = t // 86400; tt = t % 86400
sub = pd.DataFrame({"day": day, "c": X.close.values})[(tt >= 3600) & (tt < 8 * 3600)].groupby("day").c.agg(["max", "min"])
X["asia8"] = np.where(tt >= 8 * 3600 - 300, pd.Series(day).map(sub["max"] - sub["min"]).values / X.atr.values, np.nan)
m = mask(X, tod, vr=0.9) & (X.asia8.values >= 1.4) & (X.cal_ok.values == 1)
P = v.portfolio(v.run(X, m1, m, -1, tpR=2.0, be_t=0.5, be_l=0.1, minp=0.05, slk=3.5), 10, 10, 900)
cal = v.calendar(); hi = cal[(cal.impact == 3) & cal.Currency.isin(["USD", "EUR"])]
et = np.sort(hi.time.values.astype(np.int64))
dd = P.time.values // 86400
end17 = dd * 86400 + 17 * 3600
P["news_pendant"] = np.searchsorted(et, end17) > np.searchsorted(et, P.entry_t.values)
for c in ["day_nfp", "day_uscpi", "day_ecb"]: P[c] = X[c].values[P.i] == 1
P["per"] = per(P.time.values)
for c in ["news_pendant", "day_nfp", "day_uscpi", "day_ecb"]:
    g = P.groupby([c, "per"]).R.agg(["size", "mean"]).round(3)
    print(c); print(g.unstack().to_string())

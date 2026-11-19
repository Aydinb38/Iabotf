import v6lib as v, numpy as np, pandas as pd, itertools
X, m1 = v.build_features()
tb = X.time.values + 300; tod = (tb % 86400) // 60
wk = ((X.dow >= 2) & (X.dow <= 5)).values
filt = wk & (X.day_fomc.values == 0) & (X.month_end.values == 0) & (X.s_EUR_day.values > -0.5)
m = filt & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) & (tod >= 8 * 60) & (tod < 15 * 60) & (X.rsi3.values > 65) & (X.prev_rng.values >= 6) & (X.volr.values <= 1.3)
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
rows = []
for slk, tpR, bet, bel, minp, t2 in itertools.product([2.5, 3.0, 4.0], [2.0, 3.0, 5.0], [0.7, 1.0, 1.5], [0.1], [0.0, 0.05, 0.15], [17, 18]):
    T = v.run(X, m1, m, -1, tpR=tpR, be_t=bet, be_l=bel, t1=15 * 60, t2=t2 * 60, minp=minp, slk=slk)
    P = v.portfolio(T, 10, 10, 900); p = per(P.time.values); y = P.groupby("year").R.sum()
    r = v.norm(P, 20.0); s = v.stats(P, 0.5)
    r.update(slk=slk, tp=tpR, be=bet, minp=minp, t2=t2, exp=s["exp"], R1=round(P.R[p == 1].sum()), R2=round(P.R[p == 2].sum()), R3=round(P.R[p == 3].sum()), neg=int((y < 0).sum()))
    rows.append(r)
G = pd.DataFrame(rows); G.to_csv("v6_cache/exit.csv", index=False)
pd.set_option("display.width", 250)
cols = ["slk", "tp", "be", "minp", "t2", "n", "win", "PF", "exp", "risk", "ret19y", "ret2019", "R1", "R2", "R3", "neg"]
print(G.sort_values("ret19y", ascending=False)[cols].head(20).to_string(index=False))
print(G.sort_values("win", ascending=False)[cols].head(15).to_string(index=False))

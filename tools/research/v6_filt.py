import v6lib as v, numpy as np, pandas as pd
X, m1 = v.build_features()
tb = X.time.values + 300; tod = (tb % 86400) // 60
wk = ((X.dow >= 1) & (X.dow <= 5)).values
base = wk & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) & (tod >= 8 * 60) & (tod < 14 * 60) & (X.rsi3.values > 65) & (X.prev_rng.values >= 6) & (X.volr.values <= 1.3)
T = v.run(X, m1, base, -1)
F = X.iloc[T.i.values].reset_index(drop=True); T = pd.concat([T.reset_index(drop=True), F.drop(columns=["time"]).add_prefix("f_")], axis=1)
T.to_pickle("v6_cache/T_base.pkl")
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
def ev(mask, lab, mp=6, gap=1800):
    P = v.portfolio(T[mask], mp, mp, gap)
    p = per(P.time.values); y = P.groupby("year").R.sum()
    r = v.norm(P, 20.0, lab); s = v.stats(P, 0.5)
    r.update(R1=round(P.R[p == 1].sum()), R2=round(P.R[p == 2].sum()), R3=round(P.R[p == 3].sum()), exp=s["exp"], neg=int((y < 0).sum()), y2024=round(y.get(2024, 0)))
    return r
q = lambda c, p: T[c].quantile(p)
noMon = T.f_dow != 1; noF = T.f_day_fomc == 0; noME = T.f_month_end == 0
rows = [ev(np.ones(len(T), bool), "base 8-14 6pos"), ev(noMon, "no Monday"), ev(noF, "no FOMC day"), ev(noME, "no month-end"),
        ev(noMon & noF & noME, "noMon+noFOMC+noME")]
for th in [-1.0, -0.5, 0.0, 0.5]:
    rows.append(ev(noMon & noF & noME & (T.f_s_EUR_day > th), f"3 + EURday>{th}"))
for th in [0.0, 0.5, 1.0]:
    rows.append(ev(noMon & noF & noME & (T.f_bb > th), f"3 + bb>{th}"))
for th in [0.5, 1.0]:
    rows.append(ev(noMon & noF & noME & (T.f_d_low > th), f"3 + d_low>{th}"))
rows.append(ev(noMon & noF & noME & (T.f_s_EUR_day > -0.5) & (T.f_bb > 0.5), "3 + EURday>-0.5 + bb>0.5"))
rows.append(ev(noMon & noF & noME & (T.f_s_USD_1h < 0.5), "3 + USD1h<0.5"))
rows.append(ev(noMon & noF & noME & (T.f_volr <= 1.1), "3 + volr<=1.1"))
pd.set_option("display.width", 250); print(pd.DataFrame(rows).to_string(index=False))

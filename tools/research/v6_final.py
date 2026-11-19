import v6lib as v, numpy as np, pandas as pd
X, m1 = v.build_features()
tb = X.time.values + 300; tod = (tb % 86400) // 60
def mask(X, tod, h0=8, h1=15, rs=65, eur=-0.5, mon=False, fomc=True, me=True):
    wk = ((X.dow >= (1 if mon else 2)) & (X.dow <= 5)).values
    m = wk & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) & (tod >= h0 * 60) & (tod < h1 * 60) & (X.rsi3.values > rs) & (X.prev_rng.values >= 6) & (X.volr.values <= 1.1) & (X.s_EUR_day.values > eur)
    if fomc: m &= X.day_fomc.values == 0
    if me: m &= X.month_end.values == 0
    return m
EX = dict(tpR=2.0, be_t=0.7, be_l=0.1, t1=15 * 60, t2=17 * 60, minp=0.05, slk=4.0)
if __name__ == "__main__":
    rows = []
    for lab, kw, extra, mp, gap in [("v6 10pos/15min", {}, 0, 10, 900), ("v6 +0.3pip", {}, 3, 10, 900), ("v6 +0.5pip", {}, 5, 10, 900),
                                    ("v6 6pos/30min", {}, 0, 6, 1800), ("v6 6pos +0.3pip", {}, 3, 6, 1800),
                                    ("v6 sans filtre EUR", dict(eur=-99), 0, 10, 900), ("v6 avec lundi", dict(mon=True), 0, 10, 900)]:
        T = v.run(X, m1, mask(X, tod, **kw), -1, extra_pts=extra, **EX)
        P = v.portfolio(T, mp, mp, gap)
        r = v.norm(P, 20.0, lab); s = v.stats(P, 0.3); r.update(ret_at03=s["ret"], dd_at03=s["dd"], sumR=s["sumR"]); rows.append(r)
        if lab == "v6 10pos/15min":
            print(v.yearly(P).T.to_string()); P.to_pickle("v6_cache/P_v6.pkl")
            U = P[P.year >= 2019]; print("2019-2025 at 0.3%:", v.stats(U, 0.3))
    pd.set_option("display.width", 250); print(pd.DataFrame(rows).to_string(index=False))

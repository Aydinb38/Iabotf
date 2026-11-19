import v6lib as v, numpy as np, pandas as pd, sys
src = sys.argv[1] if len(sys.argv) > 1 else "2026"
X, m1 = v.build_features(src)
tb = X.time.values + 300; tod = (tb % 86400) // 60
def M(h0, h1, rs=65, vr=1.1, mon=True, fomc=False, me=False, eur=-99):
    wk = ((X.dow >= (1 if mon else 2)) & (X.dow <= 5)).values
    m = wk & (X.spread.values <= 20) & (tod >= h0 * 60) & (tod < h1 * 60) & (X.rsi3.values > rs) & (X.prev_rng.values >= 6) & (X.volr.values <= vr) & (X.s_EUR_day.values > eur)
    if fomc: m &= X.day_fomc.values == 0
    if me: m &= X.month_end.values == 0
    return m
E5 = dict(); E6 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=4.0)
per = (lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)) if src == "MT5" else (lambda t: np.ones(len(t), int))
rows = []
for lab, mk, ex, mp, gap in [
    ("v5", M(11, 14), E5, 2, 3600),
    ("v5 + exit4ATR", M(11, 14), E6, 2, 3600),
    ("v5 + 10pos/15", M(11, 14), E5, 10, 900),
    ("v5 + 8-15", M(8, 15), E5, 2, 3600),
    ("v5 + noMon", M(11, 14, mon=False), E5, 2, 3600),
    ("v5 + noFOMC/ME", M(11, 14, fomc=True, me=True), E5, 2, 3600),
    ("v5 + EUR>-0.5", M(11, 14, eur=-0.5), E5, 2, 3600),
    ("11-14 all filters 10pos exit4", M(11, 14, mon=False, fomc=True, me=True, eur=-0.5), E6, 10, 900),
    ("8-11 all filters 10pos exit4", M(8, 11, mon=False, fomc=True, me=True, eur=-0.5), E6, 10, 900),
    ("v6", M(8, 15, mon=False, fomc=True, me=True, eur=-0.5), E6, 10, 900)]:
    P = v.portfolio(v.run(X, m1, mk, -1, **ex), mp, mp, gap); s = v.stats(P, 0.5); p = per(P.time.values)
    rows.append(dict(label=lab, n=s["n"], win=s["win"], PF=s["PF"], exp=s["exp"], sumR=s["sumR"], **{f"R{k}": round(P.R[p == k].sum(), 1) for k in sorted(set(p))}))
pd.set_option("display.width", 250); print(pd.DataFrame(rows).to_string(index=False))

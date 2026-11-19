"""Effet des fixings (Krohn et al.) : le dollar monte avant le fixing BCE (15h15 serveur) et Londres (18h serveur), puis se retourne."""
import v6lib as v, numpy as np, pandas as pd
X, m1 = v.build_features("MT5")
tb = X.time.values + 300; tod = (tb % 86400) // 60
wk = ((X.dow >= 1) & (X.dow <= 5)).values & (X.spread.values <= 20) & np.isfinite(X.atr.values)
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
rows = []
def test(lab, d, e0, e1, x, cond=None, slk=4.0):
    m = wk & (tod >= e0) & (tod < e1)
    if cond is not None: m &= cond
    T = v.run(X, m1, m, d, tpR=5.0, be_t=99, be_l=0, t1=x, t2=x, minp=99, slk=slk)
    P = v.portfolio(T, 1, 1, 86400)   # 1 trade par jour : la première occasion
    p = per(P.time.values); y = P.groupby("year").R.sum()
    rows.append(dict(test=lab, n=len(P), win=round((P.R > 0).mean() * 100, 1), exp=round(P.R.mean(), 4),
                     e1=round(P.R[p == 1].mean(), 4), e2=round(P.R[p == 2].mean(), 4), e3=round(P.R[p == 3].mean(), 4), yrs_pos=int((y > 0).sum())))
for slk in [1.0, 4.0]:
    test(f"vente 17:00 -> 18:00 (avant fix Londres) SL{slk}", -1, 1020, 1025, 1080, slk=slk)
    test(f"vente 17:30 -> 18:00 SL{slk}", -1, 1050, 1055, 1080, slk=slk)
    test(f"achat 18:00 -> 19:00 (après fix Londres) SL{slk}", 1, 1080, 1085, 1140, slk=slk)
    test(f"achat 18:00 -> 20:00 SL{slk}", 1, 1080, 1085, 1200, slk=slk)
    test(f"vente 14:15 -> 15:15 (avant fix BCE) SL{slk}", -1, 855, 860, 915, slk=slk)
    test(f"achat 15:15 -> 16:15 (après fix BCE) SL{slk}", 1, 915, 920, 975, slk=slk)
    test(f"vente 02:00 -> 02:55 (avant fix Tokyo) SL{slk}", -1, 120, 125, 175, slk=slk)
    test(f"achat 03:00 -> 04:00 (après fix Tokyo) SL{slk}", 1, 180, 185, 240, slk=slk)
pd.set_option("display.width", 250); print(pd.DataFrame(rows).to_string(index=False))

"""Jours écartés par la v7 (lundi, FOMC, fin de mois) : l'autre sens (achat) est-il rentable ? Et la vente ces jours-là ?"""
import v6lib as v, numpy as np, pandas as pd
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
X, m1 = v.build_features("MT5"); tod = ((X.time.values + 300) % 86400) // 60
base = (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) & (X.prev_rng.values >= 6) & (X.volr.values <= 1.0) & (tod >= 480) & (tod < 900)
sell = (X.rsi3.values > 65) & (X.bb.values > 1.5); buy = (X.rsi3.values < 35) & (X.bb.values < -1.5)
days = {"lundi": X.dow.values == 1, "FOMC": X.day_fomc.values == 1, "fin de mois": X.month_end.values == 1,
        "mar-ven normal": (X.dow.values >= 2) & (X.day_fomc.values == 0) & (X.month_end.values == 0)}
rows = []
for dn, dm in days.items():
    for sens, d, sg in [("VENTE", -1, sell), ("ACHAT", 1, buy)]:
        for t2 in (17, 20):
            T = v.run(X, m1, base & dm & sg, d, tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0, t1=900, t2=t2 * 60)
            P = v.portfolio(T, 10, 10, 900); p = per(P.time.values); y = P.groupby("year").R.sum()
            rows.append(dict(jours=dn, sens=sens, t2=t2, n=len(P), win=round((P.R > 0).mean() * 100, 1), exp=round(P.R.mean(), 3),
                             e1=round(P.R[p == 1].mean(), 3), e2=round(P.R[p == 2].mean(), 3), e3=round(P.R[p == 3].mean(), 3), ans_pos=f"{(y > 0).sum()}/{len(y)}"))
pd.set_option("display.width", 220); print(pd.DataFrame(rows).to_string(index=False))

"""v8 : point de départ = v7 (réglages par défaut). Régularité par mois / semaine / jour."""
import v6lib as v, numpy as np, pandas as pd
from v7_final import mask
X, m1 = v.build_features("MT5"); tb = X.time.values + 300; tod = (tb % 86400) // 60
W = {8: 1.5, 9: 1.5, 10: 1.5, 11: 1.0, 12: 1.0, 13: 0.5, 14: 0.5}
T = v.run(X, m1, mask(X, tod), -1, tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0)
P = v.portfolio(T, 10, 10, 900); P["w"] = [W[int(h)] for h in tod[P.i] // 60]; P["Rw"] = P.R * P.w
dt = pd.to_datetime(P.time, unit="s")
for lab, key in [("jour", dt.dt.date), ("semaine", dt.dt.to_period("W")), ("mois", dt.dt.to_period("M")), ("trimestre", dt.dt.to_period("Q"))]:
    g = P.groupby(key).Rw.sum()
    print(f"{lab:10s}: {len(g)} périodes avec trades, positives {100 * (g > 0).mean():.1f} %, pire {g.min():.1f} R, médiane {g.median():.2f} R")
print("trades:", len(P), "win", round((P.R > 0).mean() * 100, 1), "jours tradés/an", round(dt.dt.date.nunique() / 19, 1))
print("pertes : R<-0.9:", round((P.R < -0.9).mean() * 100, 1), "% ; -0.9..0:", round(((P.R >= -0.9) & (P.R <= 0)).mean() * 100, 1), "%")
print(P.R.describe(percentiles=[.05, .25, .5, .75, .95]).round(3).to_dict())

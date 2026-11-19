import v6lib as v, numpy as np, pandas as pd
T = pd.read_pickle("v6_cache/T_base.pkl")
P = v.portfolio(T, 6, 6, 1800)

for lab, m in [("Monday", P.f_dow == 1), ("FOMC", P.f_day_fomc == 1), ("month-end", P.f_month_end == 1), ("EURday<-0.5", P.f_s_EUR_day <= -0.5), ("others", (P.f_dow != 1) & (P.f_day_fomc == 0) & (P.f_month_end == 0) & (P.f_s_EUR_day > -0.5))]:
    y = P[m].groupby("year").R.agg(["sum", "mean"])
    print(f"{lab:12s} n={m.sum():5d} mean={P[m].R.mean():+.3f} years<0: {(y['sum'] < 0).sum()}/19 ", " ".join(f"{int(a)}" for a in y["sum"].round().values))

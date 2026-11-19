import v6lib as v, numpy as np, pandas as pd
from v6_final import mask, EX
X, m1 = v.build_features("MT5"); tb = X.time.values + 300; tod = (tb % 86400) // 60
m = mask(X, tod) & (X.cal_ok.values == 1)
T = v.run(X, m1, m, -1, **EX); i = T.i.values
nn = X.news_next.values[i] + 0.0; np_ = X.news_prev.values[i]
# minutes from entry to 15:00 server
to15 = 900 - tod[i]
cal = v.calendar(); hi = cal[(cal.impact == 3) & cal.Currency.isin(["USD", "EUR"])]
et = np.sort(hi.time.values.astype(np.int64))
# any event between entry and exit of the trade
j1 = np.searchsorted(et, T.entry_t.values); j2 = np.searchsorted(et, T.exit_t.values)
during = j2 > j1
rows = []
for lab, keep in [("no news filter", np.ones(len(T), bool)), ("+-30 min (EA)", ~((nn < 30) | (np_ < 30))), ("+-60 min", ~((nn < 60) | (np_ < 60))),
                  ("no event before 15h", ~(nn < to15)), ("+-30 & no event before 15h", ~((nn < 30) | (np_ < 30) | (nn < to15)))]:
    P = v.portfolio(T[keep], 10, 10, 900); s = v.stats(P, 0.3); r = v.norm(P, 20.0)
    rows.append(dict(label=lab, n=s["n"], win=s["win"], PF=s["PF"], exp=s["exp"], sumR=s["sumR"], ret19y=r["ret19y"]))
P = v.portfolio(T, 10, 10, 900); P["during"] = during[np.searchsorted(T.entry_t.values, P.entry_t.values)] if False else None
T["during"] = during; T["nn"] = nn; T["np"] = np_
P = v.portfolio(T, 10, 10, 900)
print(P.groupby("during").R.agg(["size", "mean"]))
P["near"] = (P.nn < 30) | (P.np < 30); print(P.groupby("near").R.agg(["size", "mean"]))
pd.set_option("display.width", 250); print(pd.DataFrame(rows).to_string(index=False))

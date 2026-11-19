import v6lib as v, numpy as np, pandas as pd
rows = []
E5 = dict(); E6 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=4.0)
for src in ["MT5", "2026"]:
    X, m1 = v.build_features(src); tb = X.time.values + 300; tod = (tb % 86400) // 60
    base = ((X.dow >= 1) & (X.dow <= 5)).values & (X.spread.values <= 20) & (tod >= 480) & (tod < 900) & (X.rsi3.values > 65) & (X.prev_rng.values >= 6) & (X.volr.values <= 1.1)
    mon = X.dow.values == 1; fm = (X.day_fomc.values == 1) | (X.month_end.values == 1); eurw = X.s_EUR_day.values <= -0.5
    for exn, ex in [("v5exit", E5), ("exit4", E6)]:
        T = v.run(X, m1, base, -1, **ex)
        i = T.i.values
        for lab, w in [("A nofilter", np.ones(len(T))),
                       ("B hard all", np.where(mon[i] | fm[i] | eurw[i], 0.0, 1.0)),
                       ("C soft mon/eur 0.5, skip fomc/me", np.where(fm[i], 0.0, np.where(mon[i] | eurw[i], 0.5, 1.0))),
                       ("D soft all 0.5", np.where(mon[i] | fm[i] | eurw[i], 0.5, 1.0)),
                       ("E soft all 0.5, two bad = 0.25", np.where(fm[i], 0.5, 1.0) * np.where(mon[i], 0.5, 1.0) * np.where(eurw[i], 0.5, 1.0))]:
            S = T[w > 0].copy(); S["R"] = S.R * w[w > 0]
            P = v.portfolio(S, 10, 10, 900)
            if src == "MT5":
                r = v.norm(P, 20.0); s = v.stats(P, 0.3); y = P.groupby("year").R.sum()
                rows.append(dict(exit=exn, label=lab, n=len(P), win=s["win"], PF=s["PF"], risk=r["risk"], ret19y=r["ret19y"], ret2019=r["ret2019"], neg=int((y < 0).sum()),
                                 R2019=round(P.R[P.year >= 2019].sum()), R2025=round(P.R[P.year == 2025].sum(), 1)))
            else:
                s = v.stats(P, 0.3); rows[-10 + len([1 for x in rows if False])]  # placeholder
                key = [k for k, x in enumerate(rows) if x["exit"] == exn and x["label"] == lab][0]
                rows[key].update(n2026=s["n"], win2026=s["win"], PF2026=s["PF"], R2026=s["sumR"])
pd.set_option("display.width", 250); print(pd.DataFrame(rows).to_string(index=False))

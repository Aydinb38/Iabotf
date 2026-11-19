import v6lib as v, numpy as np, pandas as pd
from v7_final import mask, per
W = {8: 1.5, 9: 1.5, 10: 1.5, 11: 1.0, 12: 1.0, 13: 0.5, 14: 0.5}
for src in ["MT5", "2026"]:
    X, m1 = v.build_features(src); tb = X.time.values + 300; tod = (tb % 86400) // 60
    for lab, ex, wt in [("SL4 TP2 uniforme", dict(tpR=2.0, be_t=0.7, slk=4.0), False), ("SL3 TP2 uniforme", dict(tpR=2.0, be_t=0.7, slk=3.0), False),
                        ("SL3 TP2 pondéré", dict(tpR=2.0, be_t=0.7, slk=3.0), True), ("SL4 TP2 pondéré", dict(tpR=2.0, be_t=0.7, slk=4.0), True)]:
        T = v.run(X, m1, mask(X, tod), -1, be_l=0.1, minp=0.05, **ex); P = v.portfolio(T, 10, 10, 900)
        if wt: P["R"] = P.R * (tod[P.i] // 60).astype(int).__array__().tolist().__class__([W.get(int(h), 1.0) for h in tod[P.i] // 60])
        if src == "MT5":
            r = v.norm(P, 15.0); y = P.groupby("year").R.sum()
            print(src, lab, "n", len(P), "win", round((P.R > 0).mean() * 100, 1), "PF", v.stats(P)["PF"], "risk@DD15", r["risk"], "ret19y", r["ret19y"], "ret2019", r["ret2019"], "neg years", int((y < 0).sum()))
        else:
            print(src, lab, v.stats(P, 0.2))

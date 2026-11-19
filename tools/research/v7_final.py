import v6lib as v, numpy as np, pandas as pd, itertools, sys
def mask(X, tod, h0=8, h1=15, rs=65, bbt=1.5, vr=1.0):
    wk = ((X.dow >= 2) & (X.dow <= 5)).values
    return (wk & (X.day_fomc.values == 0) & (X.month_end.values == 0) & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values)
            & (tod >= h0 * 60) & (tod < h1 * 60) & (X.rsi3.values > rs) & (X.bb.values > bbt) & (X.prev_rng.values >= 6) & (X.volr.values <= vr))
EX = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=4.0)
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
if __name__ == "__main__":
    X, m1 = v.build_features("MT5"); tb = X.time.values + 300; tod = (tb % 86400) // 60
    rows = []
    # 1) sorties
    for slk, tp, be, t2 in itertools.product([3.0, 4.0, 5.0], [2.0, 3.0], [0.7, 1.0], [17, 18]):
        P = v.portfolio(v.run(X, m1, mask(X, tod), -1, tpR=tp, be_t=be, be_l=0.1, minp=0.05, slk=slk, t2=t2 * 60), 10, 10, 900)
        p = per(P.time.values); y = P.groupby("year").R.sum(); r = v.norm(P, 15.0); s = v.stats(P, 0.2)
        rows.append(dict(slk=slk, tp=tp, be=be, t2=t2, n=len(P), win=s["win"], PF=s["PF"], risk=r["risk"], ret19y=r["ret19y"], ret2019=r["ret2019"],
                         R1=round(P.R[p == 1].sum()), R2=round(P.R[p == 2].sum()), R3=round(P.R[p == 3].sum()), neg=int((y < 0).sum())))
    pd.set_option("display.width", 250); print(pd.DataFrame(rows).sort_values("ret19y", ascending=False).to_string(index=False))
    # 2) pondération du risque par heure
    T = v.run(X, m1, mask(X, tod), -1, **EX); T["h"] = tod[T.i] // 60
    P = v.portfolio(T, 10, 10, 900)
    for lab, w in [("uniforme", {}), ("8-10h x1.25, 13-14h x0.75", {8: 1.25, 9: 1.25, 10: 1.25, 13: 0.75, 14: 0.75}),
                   ("8-10h x1.5, 11-12 x1, 13-14h x0.5", {8: 1.5, 9: 1.5, 10: 1.5, 13: 0.5, 14: 0.5})]:
        Q = P.copy(); Q["R"] = Q.R * Q.h.map(lambda h: w.get(h, 1.0)); p = per(Q.time.values)
        r = v.norm(Q, 15.0)
        print(lab, "ret19y", r["ret19y"], "ret2019", r["ret2019"], "R par période", [round(Q.R[p == k].sum()) for k in (1, 2, 3)])
    print(P.groupby("h").R.agg(["size", "mean"]).round(3).T.to_string())

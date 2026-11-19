import v6lib as v, numpy as np, pandas as pd
X, m1 = v.build_features()
tb = X.time.values + 300; tod = (tb % 86400) // 60
wk = ((X.dow >= 1) & (X.dow <= 5)).values
def M(h0, h1, rs=65, pv=6, vr=99):
    return wk & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) & (tod >= h0 * 60) & (tod < h1 * 60) & (X.rsi3.values > rs) & (X.prev_rng.values >= pv) & (X.volr.values <= vr)
out = []
cfgs = [("v5 (11-14, 2pos, vol1.1)", 11, 14, 65, 6, 1.1, 2, 60), ("v4 (10-14, 3pos)", 10, 14, 65, 6, 99, 3, 60),
        ("8-14 3pos gap60", 8, 14, 65, 6, 1.1, 3, 60), ("8-14 4pos gap60", 8, 14, 65, 6, 1.1, 4, 60),
        ("8-14 4pos gap30", 8, 14, 65, 6, 1.1, 4, 30), ("8-14 6pos gap30", 8, 14, 65, 6, 1.1, 6, 30),
        ("8-14 6pos gap30 vol1.3", 8, 14, 65, 6, 1.3, 6, 30), ("9-14 6pos gap30", 9, 14, 65, 6, 1.1, 6, 30),
        ("10-14 6pos gap30", 10, 14, 65, 6, 1.1, 6, 30), ("8-14 8pos gap20", 8, 14, 65, 6, 1.1, 8, 20),
        ("7-14 6pos gap30", 7, 14, 65, 6, 1.1, 6, 30)]
for lab, h0, h1, rs, pv, vr, mp, gap in cfgs:
    T = v.run(X, m1, M(h0, h1, rs, pv, vr), -1)
    P = v.portfolio(T, mp, mp, gap * 60)
    r = v.norm(P, 20.0, lab); s = v.stats(P, 0.5)
    r.update(dd_at05=s["dd"], ret_at05=s["ret"], sumR=s["sumR"]); out.append(r)
    y = P.groupby("year").R.sum().round(0)
    print(lab, "yearly R:", y.astype(int).to_dict(), flush=True)
pd.set_option("display.width", 250); print(pd.DataFrame(out).to_string(index=False))

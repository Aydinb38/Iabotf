"""European-session EURUSD strategy on the never-used 2005-2013 history (plus 2014-2018), per year."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
f = prep("EURUSD", "ALL")
tod = f["m5"]["time"] % 86400; wk = (f["dow"] >= 1) & (f["dow"] <= 5)
S = wk & (tod >= 10 * 3600 - 300) & (tod < 13 * 3600 - 300) & (f["rsi3"] > 70)
sl = 3 * f["h1_atr"]
for name, tp, be in [("taux de réussite (TP1R BE0.5)", 1.0, 0.5), ("rendement (TP3R BE1)", 3.0, 1.0)]:
    r, e = run(f, np.zeros_like(S), S, sl, tp * sl, be_r=be, be_lock=0.1, exit_tod=15 * 60)
    yrs = pd.to_datetime(f["m1"]["time"][e], unit="s").year
    df = pd.DataFrame({"r": r, "y": yrs})
    g = df.groupby("y").r.agg(n="size", win=lambda x: (x > 0).mean() * 100, pf=lambda x: x[x > 0].sum() / -x[x < 0].sum(), sumR="sum")
    print(f"== {name}")
    print(g.round(2).T.to_string())
    a = df[df.y <= 2013]; b = df[df.y >= 2014]
    for lab, x in (("2005-2013 (jamais vu)", a), ("2014-2018", b)):
        print(f"   {lab}: n={len(x)} win={(x.r>0).mean()*100:.1f}% pf={x.r[x.r>0].sum()/-x.r[x.r<0].sum():.2f} e={x.r.mean():+.3f}R, années positives {int((x.groupby('y').r.sum()>0).sum())}/{x.y.nunique()}")

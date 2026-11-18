import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eu_lib import *
H = os.path.dirname(os.path.abspath(__file__))
D = pd.read_pickle(os.path.join(H, "eu_cand_MT5.pkl")).replace([np.inf, -np.inf], np.nan)
D["hour"] = (D.time % 86400) // 3600
D = D[(D.hour >= 11) & (D.hour < 14) & (D.rsi3_sig > 65)]
D["per"] = pd.cut(D.year, [2006, 2012, 2018, 2025], labels=["07-12", "13-18", "19-25"])
FE = ["prev_rng", "volr", "asia_size", "r24h", "w_open", "d_open", "d_high", "h1_trend", "h1_d200", "prev_ret", "r4h", "rsi14", "m5vol", "asia_pos"]
rows = []
for f in FE:
    x = D[[f, "E7_be1_hold17", "per", "year"]].dropna()
    x["q"] = pd.qcut(x[f], 5, labels=False, duplicates="drop")
    r = {"feature": f}
    for p in ["07-12", "13-18", "19-25"]:
        g = x[x.per == p].groupby("q").E7_be1_hold17.mean()
        r[p] = " ".join(f"{v:+.3f}" for v in g.values)
    yy = x.groupby(["year", "q"]).E7_be1_hold17.mean().unstack()
    r["yrs top>bot"] = f"{int((yy[yy.columns.max()] > yy[yy.columns.min()]).sum())}/{len(yy)}"
    rows.append(r)
pd.set_option("display.width", 250)
print(pd.DataFrame(rows).to_string(index=False))
print("prev_rng quantiles:", D.prev_rng.quantile([.2, .4, .6, .8]).round(2).to_dict())

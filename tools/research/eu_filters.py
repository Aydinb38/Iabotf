import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from eu_lib import *
D = load("ALL")
FE = ["rsi3_sig", "rsi14", "h1rsi14", "r5m", "r15m", "r1h", "r4h", "r24h", "d_ema20", "d_ema100", "h1_trend", "h1_d200", "volr", "m5vol",
      "d_open", "d_high", "d_low", "asia_pos", "asia_size", "prev_ret", "prev_rng", "prev_close_pos", "w_open", "hour", "dow"]
D = D.replace([np.inf, -np.inf], np.nan)
rows = []
for f in FE:
    x = D[[f, "E0_return", "E1_winrate", "year"]].dropna()
    if f in ("hour", "dow"): x["bin"] = x[f]
    else: x["bin"] = pd.qcut(x[f], 5, labels=False, duplicates="drop")
    g = x.groupby("bin").E0_return.mean()
    py = x.groupby(["year", "bin"]).E0_return.mean().unstack()
    lo, hi = py.columns.min(), py.columns.max()
    cons = int((py[hi] > py[lo]).sum())
    rows.append(dict(feature=f, bins=" ".join(f"{v:+.3f}" for v in g.values), top_minus_bottom=round(g.iloc[-1] - g.iloc[0], 3),
                     years_top_gt_bottom=f"{cons}/{len(py)}", win_bins=" ".join(f"{v*100:.0f}" for v in x.groupby("bin").E1_winrate.apply(lambda s: (s > 0).mean()).values)))
R = pd.DataFrame(rows)
R["absdiff"] = R.top_minus_bottom.abs()
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
print(R.sort_values("absdiff", ascending=False).drop(columns="absdiff").to_string(index=False))

"""Broad scan of Forex-specific ideas on IS 2014-2017 (all pairs)."""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
t0 = time.time()
F = {s: prep(s, "IS") for s in FX}
print("prep", round(time.time() - t0), "s")

def asian_mr(f, w0, w1, dev, rsix, rsin="rsi14"):
    c = f["m5"]["close"]; h = f["hour"]
    win = (h >= w0) & (h < w1) if w0 < w1 else ((h >= w0) | (h < w1))
    up = f["mid"] + dev * f["sd"]; lo = f["mid"] - dev * f["sd"]
    L = win & (c < lo) & (f[rsin] < rsix); S = win & (c > up) & (f[rsin] > 100 - rsix)
    return L, S

rows = []
for (w0, w1) in [(2, 8), (3, 9), (21, 23), (19, 23)]:
    for dev in [2.0, 2.5]:
        for (rsin, rsix) in [("rsi14", 30), ("rsi3", 10)]:
            for (slm, tpm) in [(1.5, 0.75), (3.0, 1.0), (3.0, 0.5)]:
                res = {}; allr = []
                for s, f in F.items():
                    L, S = asian_mr(f, w0, w1, dev, rsix, rsin)
                    r, e = run(f, L, S, slm * f["atr"], tpm * f["atr"], exit_tod=(9 if w0 < 9 else 1) * 60, max_bars=600)
                    res[s] = r.mean() if len(r) else np.nan; allr += list(r)
                st = stats(allr); pos = sum(1 for v in res.values() if v > 0)
                rows.append(dict(win=f"{w0}-{w1}", dev=dev, rsi=f"{rsin}<{rsix}", sl=slm, tp=tpm, n=st["n"], win_pct=st["win"], pf=st["pf"], e=st["expR"], pairs_pos=pos,
                                 best=", ".join(f"{k}:{v:+.2f}" for k, v in sorted(res.items(), key=lambda x: -np.nan_to_num(x[1]))[:5])))
df = pd.DataFrame(rows).sort_values("e", ascending=False)
pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 120)
print(df.head(25).to_string(index=False))

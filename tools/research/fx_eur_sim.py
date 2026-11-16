"""Tradeable version of the European-session EUR/CHF weakness with SL/TP/BE, M5 timing. IS then OOS."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
PAIRS = {"EURUSD": -1, "EURJPY": -1, "EURCAD": -1, "USDCHF": +1, "GBPUSD": -1, "EURGBP": -1}
TAGS = ["IS", "OOS2018", "OOS2026"]
F = {}
for s in PAIRS:
    for t in TAGS:
        try: F[(s, t)] = prep(s, t)
        except FileNotFoundError: pass

def sig(f, d, mode, a=11, last=13):
    tod = f["m5"]["time"] % 86400; dow = f["dow"]; wk = (dow >= 1) & (dow <= 5)
    if mode == "time":
        x = wk & (tod == a * 3600 - 300)
    else:  # pullback: RSI(3) against the expected direction, between a and last
        win = wk & (tod >= a * 3600 - 300) & (tod < last * 3600)
        x = win & ((f["rsi3"] > 70) if d < 0 else (f["rsi3"] < 30))
    return (x, np.zeros_like(x)) if d > 0 else (np.zeros_like(x), x)

pd.set_option("display.width", 250)
rows = []
for mode, a in [("time", 10), ("time", 11), ("time", 12), ("pullback", 10), ("pullback", 11)]:
    for slm in [1.0, 2.0, 3.0]:
        for (tpm, be) in [(10.0, 99.0), (1.5, 99.0), (1.5, 0.8), (3.0, 1.0)]:
            row = dict(mode=mode, start=a, sl=slm, tp=tpm, be=be)
            for t in TAGS:
                allr = []
                for s, d in PAIRS.items():
                    if (s, t) not in F or s in ("GBPUSD", "EURGBP"): continue
                    f = F[(s, t)]; L, S = sig(f, d, mode, a)
                    sl = slm * f["h1_atr"]
                    r, e = run(f, L, S, sl, sl * tpm, be_r=be, be_lock=0.1, exit_tod=15 * 60)
                    allr += list(r)
                st = stats(allr); row[t] = f"n={st['n']} w={st['win']}% pf={st['pf']} e={st['expR']:+.3f}"
                row["e_" + t] = st["expR"]
            rows.append(row)
df = pd.DataFrame(rows).sort_values("e_IS", ascending=False)
print(df[["mode", "start", "sl", "tp", "be", "IS", "OOS2018", "OOS2026"]].head(30).to_string(index=False))

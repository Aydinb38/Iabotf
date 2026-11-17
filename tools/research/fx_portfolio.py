"""European-session system, trade level: several pairs, several entries per day (one position at a time per pair)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
PAIRS = ["EURUSD", "GBPUSD", "EURJPY", "EURCAD", "GBPCHF", "EURCHF", "GBPJPY", "EURGBP"]
TAGS = ["IS", "OOS2018", "OOS2026"]
F = {(s, t): prep(s, t) for s in PAIRS for t in TAGS if os.path.exists(f"{DATA}/{s}_{t}.csv")}
def sig(f, a=10, last=13, rx=70):
    tod = f["m5"]["time"] % 86400; dow = f["dow"]; wk = (dow >= 1) & (dow <= 5)
    x = wk & (tod >= a * 3600 - 300) & (tod < last * 3600 - 300) & (f["rsi3"] > rx)
    return np.zeros_like(x), x
pd.set_option("display.width", 250)
for (a, last, ex) in [(10, 13, 15), (9, 14, 15), (10, 14, 16)]:
    print(f"== window {a}-{last}h exit {ex}h, SL 3xATR H1, TP 3R, BE 1R, re-entries allowed")
    for s in PAIRS:
        out = []
        for t in TAGS:
            if (s, t) not in F: continue
            f = F[(s, t)]; L, S = sig(f, a, last); sl = 3 * f["h1_atr"]
            r, e = run(f, L, S, sl, 3 * sl, be_r=1.0, be_lock=0.1, exit_tod=ex * 60)
            st = stats(r); days = len(np.unique(f["m1"]["time"][e] // 86400))
            out.append(f"{t}: n={st['n']} ({st['n']/max(days,1):.2f}/j) w={st['win']}% pf={st['pf']} e={st['expR']:+.3f}")
        print(f"  {s}: " + " | ".join(out))

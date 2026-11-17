import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
PAIRS = ["EURUSD", "GBPUSD"]; TAGS = ["IS", "OOS2018", "OOS2026"]
F = {(s, t): prep(s, t) for s in PAIRS for t in TAGS}
rows = []
for slm in [2.0, 3.0, 4.0]:
    for tpm in [0.3, 0.5, 0.75, 1.0, 1.5, 3.0]:
        for be in [99.0, 0.5, 1.0]:
            if be >= tpm and be < 99: continue
            row = dict(sl=slm, tp=tpm, be=be)
            for t in TAGS:
                allr = []
                for s in PAIRS:
                    f = F[(s, t)]; tod = f["m5"]["time"] % 86400; wk = (f["dow"] >= 1) & (f["dow"] <= 5)
                    S = wk & (tod >= 10 * 3600 - 300) & (tod < 13 * 3600 - 300) & (f["rsi3"] > 70)
                    sl = slm * f["h1_atr"]
                    r, e = run(f, np.zeros_like(S), S, sl, tpm * sl, be_r=be, be_lock=0.1, exit_tod=15 * 60)
                    allr += list(r)
                st = stats(allr); row[t] = f"w={st['win']}% pf={st['pf']} e={st['expR']:+.3f}"; row["w_" + t] = st["win"]; row["e_" + t] = st["expR"]
            rows.append(row)
df = pd.DataFrame(rows).sort_values("w_IS", ascending=False)
pd.set_option("display.width", 220)
print(df[["sl", "tp", "be", "IS", "OOS2018", "OOS2026"]].to_string(index=False))

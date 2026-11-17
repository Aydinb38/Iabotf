import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
TAGS = ["IS", "OOS2018", "OOS2026"]
F = {t: prep("EURJPY", t) for t in TAGS}
for (a, last, ex, mode) in [(12, 12, 15, "time"), (13, 13, 19, "time"), (12, 12, 18, "time"), (12, 14, 15, "pb"), (12, 15, 18, "pb"), (13, 16, 19, "pb")]:
    for slm, tpm, be in [(3, 1.0, 0.5), (3, 3, 1.0), (4, 10, 99)]:
        out = []
        for t in TAGS:
            f = F[t]; tod = f["m5"]["time"] % 86400; wk = (f["dow"] >= 1) & (f["dow"] <= 5)
            if mode == "time": S = wk & (tod == a * 3600 - 300)
            else: S = wk & (tod >= a * 3600 - 300) & (tod < last * 3600 - 300) & (f["rsi3"] > 70)
            sl = slm * f["h1_atr"]
            r, e = run(f, np.zeros_like(S), S, sl, tpm * sl, be_r=be, be_lock=0.1, exit_tod=ex * 60)
            st = stats(r); out.append(f"{t}: n={st['n']} w={st['win']}% pf={st['pf']} e={st['expR']:+.3f}")
        print(f"{mode} {a}-{last}->{ex} sl{slm} tp{tpm} be{be}: " + " | ".join(out))

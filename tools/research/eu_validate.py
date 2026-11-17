import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from eu_lib import *
D = load("ALL").replace([np.inf, -np.inf], np.nan); D26 = load("OOS2026").replace([np.inf, -np.inf], np.nan)
pd.set_option("display.width", 220)
rows = []
for thr in [0, 5.0, 6.0, 7.0, 8.0]:
    for ex in ["E0_return", "E7_be1_hold17", "E3_be05_hold17"]:
        for lab, dd in [("2005-2011", D[D.year <= 2011]), ("2012-2018", D[D.year >= 2012]), ("2026", D26)]:
            m = (dd.rsi3_sig > 65) & ((dd.prev_rng >= thr) if thr > 0 else True)
            x = select(dd, m); s = stats(x, ex)
            rows.append(dict(thr=thr, exit=ex, period=lab, n=s["n"], win=s["win"], pf=s["pf"], e=s["e"], sumR=s["sumR"], ddR=s["ddR"], yp=f"{s['years_pos']}/{s['n_years']}"))
R = pd.DataFrame(rows)
print(R.pivot_table(index=["exit", "thr"], columns="period", values=["win", "pf", "sumR"], aggfunc="first").round(3).to_string())
print(R[R.period == "2026"].to_string(index=False))

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eu_lib import *
H = os.path.dirname(os.path.abspath(__file__))
D = pd.read_pickle(os.path.join(H, "eu_cand_MT5.pkl")).replace([np.inf, -np.inf], np.nan)
D26 = pd.read_pickle(os.path.join(H, "eu_cand_OOS2026.pkl")).replace([np.inf, -np.inf], np.nan)
for x in (D, D26): x["hour"] = (x.time % 86400) // 3600
print("volr quantiles:", D.volr.quantile([.2, .4, .5, .6, .8]).round(2).to_dict())
rows = []
for pr in (0, 5, 6, 7):
    for vr in (9.0, 1.3, 1.1, 1.0, 0.9):
        def m(x): return (x.hour >= 11) & (x.hour < 14) & (x.rsi3_sig > 65) & ((x.prev_rng >= pr) if pr else True) & (x.volr <= vr)
        s_all = select(D, m(D)); s26 = select(D26, m(D26))
        r = dict(prev_rng=pr, volr_max=vr)
        st = stats(s_all, "E7_be1_hold17"); r.update(n=st["n"], win=st["win"], pf=st["pf"], yrs=f"{st['years_pos']}/{st['n_years']}", ddR=st["ddR"])
        for lab, mm in (("07-12", s_all.year <= 2012), ("13-18", (s_all.year >= 2013) & (s_all.year <= 2018)), ("19-25", s_all.year >= 2019)):
            sp = stats(s_all[mm], "E7_be1_hold17"); r[lab] = f"{sp['pf']:.2f} ({sp['years_pos']}/{sp['n_years']})"
        r["2026"] = stats(s26, "E7_be1_hold17").get("pf", 0)
        rows.append(r)
pd.set_option("display.width", 220)
print(pd.DataFrame(rows).to_string(index=False))

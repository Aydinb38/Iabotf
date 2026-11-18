"""SELL strategy with the EA's time-of-day exits on real MT5 data: windows, exits, filters, by period."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eu_lib import *
H = os.path.dirname(os.path.abspath(__file__))
D = pd.read_pickle(os.path.join(H, "eu_cand_MT5.pkl")).replace([np.inf, -np.inf], np.nan)
D26 = pd.read_pickle(os.path.join(H, "eu_cand_OOS2026.pkl")).replace([np.inf, -np.inf], np.nan)
D["hour"] = (D.time % 86400) // 3600; D26["hour"] = (D26.time % 86400) // 3600
EX = ["E0_return", "E7_be1_hold17"]
pd.set_option("display.width", 250)
def per(x, col):
    out = {}
    for lab, m in (("07-12", x.year <= 2012), ("13-18", (x.year >= 2013) & (x.year <= 2018)), ("19-25", x.year >= 2019)):
        s = stats(x[m], col); out[lab] = f"pf={s.get('pf',0):.2f} e={s.get('e',0):+.3f} y+={s.get('years_pos',0)}/{s.get('n_years',0)}"
    return out
rows = []
for (a, b) in [(8, 12), (9, 13), (10, 13), (10, 14), (11, 14), (12, 15), (9, 14)]:
    for rsix in (65, 70):
        for filt in (0, 6):
            m = (D.hour >= a) & (D.hour < b) & (D.rsi3_sig > rsix) & ((D.prev_rng >= filt) if filt else True)
            x = select(D, m)
            m26 = (D26.hour >= a) & (D26.hour < b) & (D26.rsi3_sig > rsix) & ((D26.prev_rng >= filt) if filt else True)
            x26 = select(D26, m26)
            for ex in EX:
                s = stats(x, ex); p = per(x, ex); s26 = stats(x26, ex)
                rows.append(dict(win=f"{a}-{b}", rsi=rsix, filt=filt, exit=ex[:3], n=s["n"], winp=s["win"], pf=s["pf"], yrs=f"{s['years_pos']}/{s['n_years']}",
                                 p0712=p["07-12"], p1318=p["13-18"], p1925=p["19-25"], y2026=f"pf={s26.get('pf',0):.2f}"))
R = pd.DataFrame(rows)
print(R.sort_values("pf", ascending=False).head(30).to_string(index=False))

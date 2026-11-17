"""Fine grid of the high win-rate exit (BE trigger, conditional hold end) with the prev-range filter."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from eu_lib import *
from eu_cand import short_trade
from fxlib import prep, PIPS
rows = []
for tag in ("ALL", "OOS2026"):
    f = prep("EURUSD", tag); m1 = f["m1"]; m5 = f["m5"]
    D = load(tag).replace([np.inf, -np.inf], np.nan)
    D = D[(D.rsi3_sig > 65) & (D.prev_rng >= 6.0)]
    t2i = {t: i for i, t in enumerate(m5["time"])}
    ent = np.array([m5["m1_start"][t2i[t] + 1] for t in D.time.values])
    for be in (0.5, 0.75, 1.0):
        for hold_end in (15, 16, 17, 18):
            col = f"be{be}_h{hold_end}"
            out = np.empty(len(D))
            for k in range(len(D)):
                out[k], _ = short_trade(m1["open"], m1["high"], m1["low"], m1["time"], ent[k], PIPS["EURUSD"] * 1e-4, D.R_price.values[k],
                                        3.0, be, 0.1, 99.0, 0.0, 900, hold_end * 60, 0 if hold_end == 15 else 1)
            D[col] = out
            x = select(D, D.index == D.index)
            for lab, xx in ([("2005-2018", x), ("2005-2011", x[x.year <= 2011]), ("2012-2018", x[x.year >= 2012])] if tag == "ALL" else [("2026", x)]):
                s = stats(xx, col); rows.append(dict(be=be, hold_end=hold_end, period=lab, win=s["win"], pf=s["pf"], sumR=s["sumR"], ddR=s["ddR"], yp=f"{s['years_pos']}/{s['n_years']}"))
R = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(R.pivot_table(index=["be", "hold_end"], columns="period", values=["win", "pf", "sumR"], aggfunc="first").to_string())
print(R[R.period == "2005-2018"][["be", "hold_end", "ddR", "yp"]].to_string(index=False))

"""Entrée après confirmation : le signal v10 doit être suivi d'une bougie M5 baissière (ou d'un RSI(3) qui repasse sous 65)."""
import v6lib as v, numpy as np, pandas as pd
from v9lib import *
HWB = {8: 1.5, 9: 1.0, 10: 0.9, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.2}
E7 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0)
rows = []
for mode in ["immédiate (v10)", "bougie suivante baissière", "RSI(3) repasse sous 65", "clôture sous le bas du signal"]:
    out = {}
    for src in ("MT5", "2026"):
        X, m1 = v.build_features(src); tod = ((X.time.values + 300) % 86400) // 60
        X["asia8"] = asia8(X)
        wk = ((X.dow >= 2) & (X.dow <= 5)).values
        sig = (wk & (X.day_fomc.values == 0) & (X.month_end.values == 0) & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values)
               & (tod >= 480) & (tod < 900) & (X.rsi3.values > 65) & (X.bb.values > 1.5) & (X.prev_rng.values >= 6) & (X.volr.values <= 1.0))
        if mode.startswith("immédiate"):
            m = sig
        else:
            prev = np.r_[False, sig[:-1]]                       # le signal était sur la bougie précédente
            o5 = X.close.values - 0  # clôture
            c = X.close.values; cprev = np.r_[np.nan, c[:-1]]
            m5 = v.resample(m1, 300); lo = m5["low"]; lop = np.r_[np.nan, lo[:-1]]; op = m5["open"]
            if mode.startswith("bougie"): conf = c < op
            elif mode.startswith("RSI"): conf = X.rsi3.values < 65
            else: conf = c < lop
            m = prev & conf & (tod >= 485) & (tod < 905)
        T = v.run(X, m1, m, -1, **E7)
        T["h"] = (((T.entry_t % 86400) // 60 - 5) // 60).astype(int).clip(8, 14)
        P = v.portfolio(T, 10, 10, 900); P["w"] = P.h.map(HWB); out[src] = P
    e = evaluate(out["MT5"], mode); P = out["MT5"]
    e.update(Rtrain=round((P[P.year <= 2018].R * P[P.year <= 2018].w).sum()), Rtest=round((P[P.year >= 2019].R * P[P.year >= 2019].w).sum()), R26w=round((out["2026"].R * out["2026"].w).sum(), 1))
    rows.append(e)
R = pd.DataFrame(rows); pd.set_option("display.width", 260)
print(R[["label", "n", "win", "PFw", "sumRw", "Rtrain", "Rtest", "sharpe", "mois_pos", "neg_y", "risk_dd", "ret19y", "ret2019", "R26w"]].to_string(index=False))

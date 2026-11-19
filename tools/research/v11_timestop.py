"""Sortie anticipée : après `xm` minutes, si le trade perd plus de `y` R, fermeture au marché. + arrêt des entrées après k stops pleins dans la journée."""
import v6lib as v, numpy as np, pandas as pd
from numba import njit
from v9lib import *

@njit(cache=True)
def trade_ts(o, h, l, sp, tm, e, R, tpR, be_t, be_l, t1, t2, minp, pt, xm, y):
    n = len(o); entry = o[e]; sl = entry + R; tp = entry - tpR * R; best = 0.0; j = e; late = False
    while j < n - 1:
        s = sp[j] * pt
        if j > e:
            if tm[j] - tm[j - 1] > 4 * 3600: return (entry - (o[j] + s)) / R, j
            tod = (tm[j] % 86400) // 60
            if tod >= t1: late = True
            cur = (entry - (o[j] + s)) / R
            if late and (cur >= minp or tod >= t2): return cur, j
            if xm > 0 and tm[j] - tm[e] >= xm * 60 and cur <= -y and best < be_t: return cur, j
        if h[j] + s >= sl: return (entry - (max(sl, o[j] + s) if j > e else sl)) / R, j
        if l[j] + s <= tp: return (entry - tp) / R, j
        fav = (entry - (l[j] + s)) / R
        if late and fav >= minp: return minp, j
        if fav > best: best = fav
        if best >= be_t:
            nsl = entry - be_l * R
            if nsl < sl: sl = nsl
        j += 1
    return 0.0, j

@njit(cache=True)
def trades_ts(o, h, l, sp, tm, ents, Rs, tpR, be_t, be_l, t1, t2, minp, pt, xm, y):
    n = len(ents); r = np.empty(n); x = np.empty(n, np.int64)
    for k in range(n): r[k], x[k] = trade_ts(o, h, l, sp, tm, ents[k], Rs[k], tpR, be_t, be_l, t1, t2, minp, pt, xm, y)
    return r, x

HWB = {8: 1.5, 9: 1.0, 10: 0.9, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.2}
E7 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0)
base = {src: broad(src, E7, rsi=65, bb=1.5, prev=6, volr=1.0) for src in ("MT5", "2026")}
feat = {src: v.build_features(src) for src in ("MT5", "2026")}
rows = []
for xm, y in [(0, 0), (60, 0.5), (60, 0.7), (120, 0.4), (120, 0.6), (180, 0.5), (240, 0.5), (240, 0.3)]:
    out = {}
    for src in ("MT5", "2026"):
        X, m1 = feat[src]; T = base[src].copy()
        ents = X.m1_next.values[T.i]; Rs = 3.0 * X.atr.values[T.i]
        r, x = trades_ts(m1["open"], m1["high"], m1["low"], m1["spread"], m1["time"], ents, Rs, 2.0, 0.7, 0.1, 900, 1020, 0.05, 1e-5, xm, y)
        T["R"] = r; T["exit_t"] = m1["time"][x]
        P = v.portfolio(T, 10, 10, 900); P["w"] = P.h.map(HWB); out[src] = P
    e = evaluate(out["MT5"], f"sortie si < -{y}R après {xm} min" if xm else "v10 (sans sortie anticipée)")
    P = out["MT5"]; e.update(Rtrain=round((P[P.year <= 2018].R * P[P.year <= 2018].w).sum()), Rtest=round((P[P.year >= 2019].R * P[P.year >= 2019].w).sum()),
                             R26w=round((out["2026"].R * out["2026"].w).sum(), 1), avg_loss=round(P.R[P.R < 0].mean(), 3))
    rows.append(e)
R = pd.DataFrame(rows); pd.set_option("display.width", 260)
print(R[["label", "n", "win", "PFw", "sumRw", "Rtrain", "Rtest", "avg_loss", "sharpe", "mois_pos", "neg_y", "risk_dd", "ret19y", "ret2019", "R26w"]].to_string(index=False))

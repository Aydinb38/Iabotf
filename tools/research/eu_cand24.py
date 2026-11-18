"""24h candidate trades on EURUSD (2005-2018 + 2026): every M5 RSI(3) pullback, BUY (rsi3<35) and SELL (rsi3>65),
at any hour Monday-Friday. Outcomes with relative time exits: plain exit after H minutes, and conditional exit
(after H minutes close only if >= +0.05R, otherwise keep until back in profit or H+Hext)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
from numba import njit

@njit(cache=True)
def trade(o, h, l, t, e, d, cost, R, tpR, beT, beL, hold, ext, cond, minR):
    if d > 0: entry = o[e] + cost; sl = entry - R; tp = entry + tpR * R
    else:     entry = o[e];        sl = entry + R; tp = entry - tpR * R
    best = 0.0; j = e; n = len(o); t0 = t[e]
    while j < n - 1:
        if d > 0:
            if l[j] <= sl: return ((min(sl, o[j]) if j > e else sl) - entry) / R, j
            if h[j] >= tp: return (tp - entry) / R, j
            fav = (h[j] - entry) / R
        else:
            hi = h[j] + cost; lo = l[j] + cost
            if hi >= sl: return (entry - (max(sl, o[j] + cost) if j > e else sl)) / R, j
            if lo <= tp: return (entry - tp) / R, j
            fav = (entry - lo) / R
        if fav > best: best = fav
        if best >= beT:
            nsl = entry + d * beL * R
            if (d > 0 and nsl > sl) or (d < 0 and nsl < sl): sl = nsl
        j += 1
        if t[j] - t[j - 1] > 4 * 3600:
            px = o[j]; return ((px - entry) if d > 0 else (entry - px - cost)) / R, j
        el = t[j] - t0
        if el >= hold * 60:
            cur = ((o[j] - entry) if d > 0 else (entry - o[j] - cost)) / R
            if cond == 0 or cur >= minR or el >= (hold + ext) * 60:
                return cur, j
    return 0.0, j

def build(tag, hold=180, ext=120):
    f = prep("EURUSD", tag); m5 = f["m5"]; m1 = f["m1"]
    wk = (f["dow"] >= 1) & (f["dow"] <= 5)
    sig = np.zeros(len(m5["time"]), np.int64)
    sig[wk & (f["rsi3"] > 65)] = -1; sig[wk & (f["rsi3"] < 35)] = 1
    idx = np.flatnonzero(sig != 0); idx = idx[idx + 1 < len(m5["time"])]
    idx = idx[(m5["time"][idx + 1] - m5["time"][idx]) <= 600]
    R = 3 * f["h1_atr"][idx]; ok = np.isfinite(R) & (R > 0); idx = idx[ok]; R = R[ok]
    ent = m5["m1_start"][idx + 1]; d = sig[idx]
    hour_e = f["hour"][idx + 1]
    cost = PIPS["EURUSD"] * 1e-4 * HOUR_MULT[hour_e]
    outA = np.empty(len(idx)); outB = np.empty(len(idx)); xB = np.empty(len(idx), np.int64)
    for k in range(len(idx)):
        outA[k], _ = trade(m1["open"], m1["high"], m1["low"], m1["time"], ent[k], d[k], cost[k], R[k], 3.0, 1.0, 0.1, hold, 0, 0, 0.05)
        outB[k], xB[k] = trade(m1["open"], m1["high"], m1["low"], m1["time"], ent[k], d[k], cost[k], R[k], 3.0, 1.0, 0.1, hold, ext, 1, 0.05)
    D = pd.DataFrame({"time": m5["time"][idx], "dir": d, "R_price": R, "rsi3_sig": f["rsi3"][idx], "entry_hour": hour_e,
                      "A": outA, "B": outB, "exitB": m1["time"][xB]})
    feats = pd.read_pickle(os.path.join(os.path.dirname(__file__), "eurusd_feat.pkl" if tag == "ALL" else "eurusd_feat_2026.pkl"))
    D = D.merge(feats.drop(columns=["close", "m1_next", "next_gap", "y1h", "y2h", "y4h"]), on="time", how="left")
    D["year"] = pd.to_datetime(D.time, unit="s").dt.year; D["day"] = D.time // 86400
    return D

if __name__ == "__main__":
    for tag in ("ALL", "OOS2026"):
        D = build(tag); D.to_pickle(os.path.join(os.path.dirname(__file__), f"eu_c24_{tag}.pkl")); print(tag, len(D))

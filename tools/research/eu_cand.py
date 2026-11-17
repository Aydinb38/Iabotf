"""Candidate trades (EURUSD sells, 2005-2018 + 2026): every M5 pullback signal in the 10h-13h window,
26 features at entry, and the outcome (R) of each trade under several exit rules (independent simulation)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
from numba import njit

@njit(cache=True)
def short_trade(o, h, l, t, e, entry_cost, R, tpR, be1t, be1l, be2t, be2l, t1, t2, cond):
    """short from m1 open[e]; returns (R result, exit index). t1/t2 = minutes of day; cond=1: at t1 exit only if in profit."""
    entry = o[e]; sl = entry + R; tp = entry - tpR * R
    best = 0.0; j = e; n = len(o)
    while j < n - 1:
        hi = h[j] + entry_cost; lo = l[j] + entry_cost
        if hi >= sl:
            px = max(sl, o[j] + entry_cost) if j > e else sl
            return (entry - px) / R, j
        if lo <= tp:
            return (entry - tp) / R, j
        fav = (entry - lo) / R
        if fav > best: best = fav
        if best >= be1t and entry - be1l * R < sl: sl = entry - be1l * R
        if best >= be2t and entry - be2l * R < sl: sl = entry - be2l * R
        j += 1
        tod = (t[j] % 86400) // 60
        if t[j] - t[j - 1] > 4 * 3600:
            return (entry - (o[j] + entry_cost)) / R, j
        if tod >= t1 and tod < t1 + 600:
            cur = (entry - (o[j] + entry_cost)) / R
            if cond == 0 or cur >= 0 or tod >= t2:
                if cond == 0 or cur >= 0:
                    return cur, j
            if tod >= t2:
                return cur, j
    return 0.0, j

EXITS = {
    "E0_return":      (3.0, 1.0, 0.1, 99.0, 0.0, 900, 900, 0),
    "E1_winrate":     (3.0, 0.5, 0.1, 99.0, 0.0, 900, 900, 0),
    "E2_be03":        (3.0, 0.3, 0.05, 99.0, 0.0, 900, 900, 0),
    "E3_be05_hold17": (3.0, 0.5, 0.1, 99.0, 0.0, 900, 1020, 1),
    "E4_be05_hold19": (3.0, 0.5, 0.1, 99.0, 0.0, 900, 1140, 1),
    "E5_be03_lock1":  (3.0, 0.3, 0.05, 1.0, 0.5, 900, 900, 0),
    "E6_tp1_be05":    (1.0, 0.5, 0.1, 99.0, 0.0, 900, 900, 0),
    "E7_be1_hold17":  (3.0, 1.0, 0.1, 99.0, 0.0, 900, 1020, 1),
}

def build(tag):
    f = prep("EURUSD", tag); m5 = f["m5"]; m1 = f["m1"]
    tod = m5["time"] % 86400; wk = (f["dow"] >= 1) & (f["dow"] <= 5)
    S = wk & (tod >= 10 * 3600 - 300) & (tod < 13 * 3600 - 300) & (f["rsi3"] > 60)
    idx = np.flatnonzero(S); idx = idx[idx + 1 < len(m5["time"])]
    idx = idx[(m5["time"][idx + 1] - m5["time"][idx]) <= 600]
    ent = m5["m1_start"][idx + 1]; R = 3 * f["h1_atr"][idx]
    ok = np.isfinite(R) & (R > 0); idx, ent, R = idx[ok], ent[ok], R[ok]
    cost = PIPS["EURUSD"] * 0.0001
    D = pd.DataFrame({"time": m5["time"][idx], "R_price": R, "rsi3_sig": f["rsi3"][idx]})
    for name, (tpR, b1t, b1l, b2t, b2l, t1, t2, cond) in EXITS.items():
        out = np.empty(len(idx)); xi = np.empty(len(idx), np.int64)
        for k in range(len(idx)):
            out[k], xi[k] = short_trade(m1["open"], m1["high"], m1["low"], m1["time"], ent[k], cost, R[k], tpR, b1t, b1l, b2t, b2l, t1, t2, cond)
        D[name] = out; D[name + "_exit"] = m1["time"][xi]
    feats = pd.read_pickle(os.path.join(os.path.dirname(__file__), "eurusd_feat.pkl" if tag == "ALL" else "eurusd_feat_2026.pkl"))
    D = D.merge(feats.drop(columns=["close", "m1_next", "next_gap", "y1h", "y2h", "y4h"]), on="time", how="left")
    D["year"] = pd.to_datetime(D.time, unit="s").dt.year; D["day"] = D.time // 86400
    return D

if __name__ == "__main__":
    for tag in ("ALL", "OOS2026"):
        D = build(tag); D.to_pickle(os.path.join(os.path.dirname(__file__), f"eu_cand_{tag}.pkl"))
        print(tag, len(D), "candidates")

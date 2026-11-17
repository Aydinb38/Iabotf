"""EURUSD adaptive AI research: features at every M5 close, walk-forward training (3y -> next year).
Usage: python3 eurusd_ai.py   (writes eurusd_features.parquet cache)"""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
from numba import njit

CACHE = os.path.join(os.path.dirname(__file__), "eurusd_feat.pkl")

def build(path):
    m1 = load_m1(path); m5 = resample(m1, 300); h1 = resample(m1, 3600)
    t = m5["time"]; o, h, l, c = m5["open"], m5["high"], m5["low"], m5["close"]
    hi = htf_index(t, 300, h1["time"], 3600); ok = hi >= 0; hi2 = np.where(ok, hi, 0)
    h1atr = np.where(ok, atr(h1["high"], h1["low"], h1["close"], 14)[hi2], np.nan)
    h1atr_l = np.where(ok, atr(h1["high"], h1["low"], h1["close"], 240)[hi2], np.nan)
    h1c = h1["close"]
    f = {}
    f["hour"] = ((t % 86400) // 3600).astype(float); f["minute"] = ((t % 3600) // 60).astype(float)
    f["dow"] = (((t // 86400) + 4) % 7).astype(float)
    A = h1atr
    def lag(k): return np.r_[np.full(k, np.nan), c[:-k]]
    for k, name in [(1, "r5m"), (3, "r15m"), (12, "r1h"), (48, "r4h"), (288, "r24h")]:
        f[name] = (c - lag(k)) / A
    f["rsi3"] = rsi(c, 3); f["rsi14"] = rsi(c, 14)
    f["h1rsi14"] = np.where(ok, rsi(h1c, 14)[hi2], np.nan)
    f["d_ema20"] = (c - ema(c, 20)) / A; f["d_ema100"] = (c - ema(c, 100)) / A
    f["h1_trend"] = np.where(ok, (ema(h1c, 50) - ema(h1c, 200))[hi2], np.nan) / A
    f["h1_d200"] = np.where(ok, (h1c - ema(h1c, 200))[hi2], np.nan) / A
    f["volr"] = A / h1atr_l; f["m5vol"] = atr(h, l, c, 14) / A
    day = t // 86400; s = pd.DataFrame({"day": day, "o": o, "h": h, "l": l, "c": c, "tod": t % 86400})
    dopen = s.groupby("day").o.transform("first").values
    dhigh = s.groupby("day").h.cummax().values; dlow = s.groupby("day").l.cummin().values
    f["d_open"] = (c - dopen) / A; f["d_high"] = (c - dhigh) / A; f["d_low"] = (c - dlow) / A
    asia = s[(s.tod >= 3600) & (s.tod < 9 * 3600)].groupby("day").agg(ah=("h", "max"), al=("l", "min"))
    ah = pd.Series(day).map(asia.ah).values; al = pd.Series(day).map(asia.al).values
    after9 = (t % 86400) >= 9 * 3600
    f["asia_pos"] = np.where(after9, (c - al) / np.maximum(ah - al, 1e-9), np.nan)
    f["asia_size"] = np.where(after9, (ah - al) / A, np.nan)
    dd = s.groupby("day").agg(o=("o", "first"), c=("c", "last"), h=("h", "max"), l=("l", "min"))
    prev = dd.shift(1)
    f["prev_ret"] = pd.Series(day).map(prev.c - prev.o).values / A
    f["prev_rng"] = pd.Series(day).map(prev.h - prev.l).values / A
    f["prev_close_pos"] = (c - pd.Series(day).map(prev.c).values) / A
    wk = (t + 4 * 86400) // 604800
    wopen = pd.Series(o).groupby(wk).transform("first").values
    f["w_open"] = (c - wopen) / A
    X = pd.DataFrame(f)
    X["atr_h1"] = A
    X["time"] = t; X["close"] = c; X["m1_next"] = np.r_[m5["m1_start"][1:], len(m1["open"]) - 1]
    X["next_gap"] = np.r_[t[1:] - t[:-1], 99999]
    # labels: future move over horizons (from next bar open), in ATR units
    nxt_open = np.r_[o[1:], np.nan]
    for k, name in [(12, "y1h"), (24, "y2h"), (48, "y4h")]:
        fut = np.r_[c[k:], np.full(k, np.nan)]
        X[name] = (fut - nxt_open) / A
    return X, m1

if __name__ == "__main__":
    t0 = time.time()
    X, m1 = build(f"{DATA}/EURUSD_ALL.csv")
    X.to_pickle(CACHE)
    X26, _ = build(f"{DATA}/EURUSD_OOS2026.csv"); X26.to_pickle(CACHE.replace(".pkl", "_2026.pkl"))
    print("features built", X.shape, X26.shape, round(time.time() - t0), "s")
    print(X.describe().T[["mean", "std", "min", "max"]].round(3).to_string())

import os, sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, "/home/user/Iabotf/tools/research")
from rlib import *

DATA = os.environ.get("IABOT_DATA", os.path.join(os.path.dirname(__file__), "..", "..", "data", "m1"))

def prep(sym, tag):
    m1 = load_m1(f"{DATA}/{sym}_{tag}.csv")
    m5 = resample(m1, 300); h1 = resample(m1, 3600)
    o, h, l, c = m5["open"], m5["high"], m5["low"], m5["close"]
    f = dict(m1=m1, m5=m5, h1=h1)
    f["atr"] = atr(h, l, c, 14)
    f["ema_f"] = ema(c, 21); f["ema_s"] = ema(c, 50)
    f["rsi"] = rsi(c, 14); f["rsi2"] = rsi(c, 3)
    f["adx"], f["pdi"], f["ndi"] = adx(h, l, c, 14)
    f["bb_mid"] = sma(c, 20)
    sd = pd.Series(c).rolling(20).std(ddof=0).values
    f["bb_sd"] = sd
    hi = htf_index(m5["time"], 300, h1["time"], 3600)
    hc = h1["close"]; he50 = ema(hc, 50); he200 = ema(hc, 200)
    hadx, _, _ = adx(h1["high"], h1["low"], hc, 14)
    ok = hi >= 0; hi2 = np.where(ok, hi, 0)
    f["h_c"] = np.where(ok, hc[hi2], np.nan); f["h_e50"] = np.where(ok, he50[hi2], np.nan)
    f["h_e200"] = np.where(ok, he200[hi2], np.nan); f["h_adx"] = np.where(ok, hadx[hi2], np.nan)
    f["hour"] = (m5["time"] % 86400) // 3600
    f["atr_avg"] = sma(np.nan_to_num(f["atr"]), 100)
    return f

def run(f, sym, longs, shorts, sl, tp, be_r=99., be_lock=0.0, tr_s=99., tr_d=0., max_bars=10**9,
        close_hour=0, partial_r=99., partial_frac=0.0):
    m5 = f["m5"]; m1 = f["m1"]
    idx = np.flatnonzero(longs | shorts); idx = idx[idx + 1 < len(m5["time"])]
    d = np.where(longs[idx], 1, -1)
    ent = m5["m1_start"][idx + 1]
    # only allow entry if next M5 bar starts within 10 minutes (no gaps / weekend)
    okg = (m5["time"][idx + 1] - m5["time"][idx]) <= 600
    idx, d, ent = idx[okg], d[okg], ent[okg]
    s_sl = sl[idx]; s_tp = tp[idx]; good = np.isfinite(s_sl) & (s_sl > 0) & np.isfinite(s_tp)
    e, dd, r, x = simulate(m1["open"], m1["high"], m1["low"], m1["close"], m1["time"],
                           ent[good], d[good], s_sl[good], s_tp[good], COST[sym],
                           be_r, be_lock, tr_s, tr_d, max_bars, close_hour * 3600, 0, partial_r, partial_frac)
    return e, dd, r

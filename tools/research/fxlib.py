"""Forex research helpers: per-pair costs (pips, round trip, ECN incl. commission) with
hour-of-day spread widening, and a vectorised preparation of M5 features."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from rlib import load_m1, resample, ema, sma, atr, rsi, adx, htf_index, stats
from numba import njit

DATA = os.environ.get("IABOT_DATA", os.path.join(os.path.dirname(__file__), "..", "..", "data", "m1"))
PIPS = {"EURUSD": 1.0, "GBPUSD": 1.4, "AUDUSD": 1.2, "USDCAD": 1.4, "USDJPY": 1.2, "EURGBP": 1.3, "EURCHF": 1.6,
        "AUDNZD": 2.2, "AUDCAD": 1.8, "NZDCAD": 2.4, "EURCAD": 2.0, "GBPCAD": 2.8, "GBPCHF": 2.4, "USDCHF": 1.4,
        "EURJPY": 1.6, "NZDUSD": 1.5, "CADCHF": 2.2, "GBPJPY": 2.4}
FX = list(PIPS)
def pip(sym): return 0.01 if sym.endswith("JPY") else 0.0001
# spread widening by server hour (rollover 23-01 is the worst)
HOUR_MULT = np.array([4.0, 2.5, 1.6, 1.3, 1.3, 1.3, 1.3, 1.3, 1.2] + [1.0] * 13 + [1.3, 3.0])

def prep(sym, tag):
    m1 = load_m1(f"{DATA}/{sym}_{tag}.csv")
    m5 = resample(m1, 300); h1 = resample(m1, 3600)
    o, h, l, c = m5["open"], m5["high"], m5["low"], m5["close"]
    f = dict(m1=m1, m5=m5, h1=h1, sym=sym)
    f["atr"] = atr(h, l, c, 14)
    f["rsi14"] = rsi(c, 14); f["rsi3"] = rsi(c, 3); f["rsi7"] = rsi(c, 7)
    f["mid"] = sma(c, 20); f["sd"] = pd.Series(c).rolling(20).std(ddof=0).values
    f["hour"] = (m5["time"] % 86400) // 3600
    f["dow"] = ((m5["time"] // 86400) + 4) % 7   # 0 = Sunday
    hi = htf_index(m5["time"], 300, h1["time"], 3600); ok = hi >= 0; hi2 = np.where(ok, hi, 0)
    hc = h1["close"]
    for n in (50, 200):
        f[f"h1_e{n}"] = np.where(ok, ema(hc, n)[hi2], np.nan)
    f["h1_c"] = np.where(ok, hc[hi2], np.nan)
    f["h1_atr"] = np.where(ok, atr(h1["high"], h1["low"], hc, 14)[hi2], np.nan)
    hx, _, _ = adx(h1["high"], h1["low"], hc, 14); f["h1_adx"] = np.where(ok, hx[hi2], np.nan)
    f["cost"] = PIPS[sym] * pip(sym) * HOUR_MULT[f["hour"]]
    return f

@njit(cache=True)
def sim(m1o, m1h, m1l, m1t, ent, d, slv, tpv, costv, be_r, be_lock, tr_s, tr_d, exit_tod, max_bars):
    """one position at a time; exit at first M1 bar whose server time-of-day == exit_tod (if >=0)."""
    n = len(ent); out_r = np.empty(n); out_e = np.empty(n, np.int64); k = 0; busy = -1
    for s in range(n):
        e = ent[s]
        if e <= busy or e >= len(m1o) - 1: continue
        R = slv[s]; cost = costv[s]; dd = d[s]
        entry = m1o[e] + (cost if dd > 0 else 0.0)
        sl = entry - dd * R; tp = entry + dd * tpv[s]
        best = 0.0; j = e; res = 0.0
        while True:
            if dd > 0:
                lo = m1l[j]; hi = m1h[j]
                if lo <= sl: res = ((min(sl, m1o[j]) if j > e else sl) - entry) / R; break
                if hi >= tp: res = (tp - entry) / R; break
                fav = (hi - entry) / R
            else:
                lo = m1l[j] + cost; hi = m1h[j] + cost
                if hi >= sl: res = (entry - (max(sl, m1o[j] + cost) if j > e else sl)) / R; break
                if lo <= tp: res = (entry - tp) / R; break
                fav = (entry - lo) / R
            if fav > best: best = fav
            if best >= be_r:
                nsl = entry + dd * be_lock * R
                if (dd > 0 and nsl > sl) or (dd < 0 and nsl < sl): sl = nsl
            if tr_d > 0 and best >= tr_s:
                nsl = entry + dd * (best - tr_d) * R
                if (dd > 0 and nsl > sl) or (dd < 0 and nsl < sl): sl = nsl
            j += 1
            if j >= len(m1o) - 1 or (j - e) >= max_bars or (exit_tod >= 0 and (m1t[j] % 86400) // 60 == exit_tod) or (m1t[j] - m1t[j - 1]) > 4 * 3600:
                px = m1o[j]
                res = (px - entry) / R if dd > 0 else (entry - (px + cost)) / R
                break
        out_r[k] = res; out_e[k] = e; k += 1; busy = j
    return out_r[:k], out_e[:k]

def run(f, L, S, sl, tp, be_r=99., be_lock=0., tr_s=99., tr_d=0., exit_tod=-1, max_bars=10**9, cost_mult=1.0):
    m5 = f["m5"]; m1 = f["m1"]
    L = np.nan_to_num(L).astype(bool); S = np.nan_to_num(S).astype(bool)
    idx = np.flatnonzero(L | S); idx = idx[idx + 1 < len(m5["time"])]
    okg = (m5["time"][idx + 1] - m5["time"][idx]) <= 600; idx = idx[okg]
    d = np.where(L[idx], 1, -1); ent = m5["m1_start"][idx + 1]
    s_sl = sl[idx]; s_tp = tp[idx]; good = np.isfinite(s_sl) & (s_sl > 0) & np.isfinite(s_tp) & (s_tp > 0)
    hour_next = f["hour"][np.minimum(idx + 1, len(f["hour"]) - 1)]
    cost = PIPS[f["sym"]] * pip(f["sym"]) * HOUR_MULT[hour_next] * cost_mult
    r, e = sim(m1["open"], m1["high"], m1["low"], m1["time"], ent[good], d[good].astype(np.int64), s_sl[good], s_tp[good],
               cost[good], be_r, be_lock, tr_s, tr_d, exit_tod, max_bars)
    return r, e

"""Fast research library (numba) used to pre-screen strategy ideas on M1 data.

Signals are computed on CLOSED M5 bars, entries happen at the open of the next
M5 bar and exits are simulated minute by minute (pessimistic: if SL and TP are
both inside the same M1 bar the SL is assumed to be hit first).
All costs (spread + commission) are charged in price units.
"""
import numpy as np
import pandas as pd
from numba import njit

COST = {"EURUSD": 0.00010, "GBPUSD": 0.00014, "AUDUSD": 0.00012, "USDCAD": 0.00014,
        "USDJPY": 0.012, "XAUUSD": 0.30}


def load_m1(path):
    d = pd.read_csv(path)
    return {k: d[k].values.astype(np.float64) if k != "time" else d[k].values.astype(np.int64)
            for k in ["time", "open", "high", "low", "close"]}


def resample(m1, sec):
    key = m1["time"] // sec
    brk = np.flatnonzero(np.diff(key)) + 1
    starts = np.r_[0, brk]
    ends = np.r_[brk, len(key)]
    out = {
        "time": key[starts] * sec,
        "open": m1["open"][starts],
        "high": np.maximum.reduceat(m1["high"], starts),
        "low": np.minimum.reduceat(m1["low"], starts),
        "close": m1["close"][ends - 1],
        "m1_start": starts, "m1_end": ends,
    }
    return out


@njit(cache=True)
def ema(x, n):
    out = np.empty_like(x); a = 2.0 / (n + 1.0); out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = x[i] * a + out[i - 1] * (1 - a)
    return out


@njit(cache=True)
def sma(x, n):
    out = np.full_like(x, np.nan); s = 0.0
    for i in range(len(x)):
        s += x[i]
        if i >= n: s -= x[i - n]
        if i >= n - 1: out[i] = s / n
    return out


@njit(cache=True)
def atr(h, l, c, n):  # MT5 iATR = SMA of true range
    tr = np.empty_like(c); tr[0] = h[0] - l[0]
    for i in range(1, len(c)):
        tr[i] = max(h[i], c[i - 1]) - min(l[i], c[i - 1])
    return sma(tr, n)


@njit(cache=True)
def rsi(c, n):  # MT5 iRSI (Wilder smoothing)
    out = np.full_like(c, np.nan); up = 0.0; dn = 0.0
    for i in range(1, len(c)):
        d = c[i] - c[i - 1]; u = d if d > 0 else 0.0; v = -d if d < 0 else 0.0
        if i <= n:
            up += u / n; dn += v / n
        else:
            up = (up * (n - 1) + u) / n; dn = (dn * (n - 1) + v) / n
        if i >= n:
            out[i] = (50.0 if up == 0 else 100.0) if dn == 0 else 100.0 - 100.0 / (1 + up / dn)
    return out


@njit(cache=True)
def adx(h, l, c, n):  # MT5 iADX (EMA smoothing of +DM/TR, -DM/TR)
    m = len(c); pdi = np.zeros(m); ndi = np.zeros(m); ax = np.zeros(m); a = 2.0 / (n + 1)
    for i in range(1, m):
        p = h[i] - h[i - 1]; q = l[i - 1] - l[i]
        if p < 0: p = 0.0
        if q < 0: q = 0.0
        if p > q: q = 0.0
        elif p < q: p = 0.0
        else: p = 0.0; q = 0.0
        tr = max(abs(h[i] - l[i]), abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        pd_ = 100 * p / tr if tr != 0 else 0.0; nd_ = 100 * q / tr if tr != 0 else 0.0
        pdi[i] = pd_ * a + pdi[i - 1] * (1 - a); ndi[i] = nd_ * a + ndi[i - 1] * (1 - a)
        s = pdi[i] + ndi[i]; t = 100 * abs((pdi[i] - ndi[i]) / s) if s != 0 else 0.0
        ax[i] = t * a + ax[i - 1] * (1 - a)
    return ax, pdi, ndi


def htf_index(ltf_time, ltf_sec, htf_time, htf_sec):
    """index of the last HTF bar fully CLOSED at the close of each LTF bar (-1 if none)."""
    close_t = ltf_time + ltf_sec
    idx = np.searchsorted(htf_time + htf_sec, close_t, side="right") - 1
    return idx


@njit(cache=True)
def simulate(m1o, m1h, m1l, m1c, m1t, sig_m1, sig_dir, sig_sl, sig_tp, cost,
             be_r, be_lock_r, trail_start_r, trail_dist_r, max_bars, close_hour_sec, day_sec_off,
             partial_r, partial_frac):
    """Sequential one-position simulation. Returns arrays (entry_idx, dir, R result, exit_idx)."""
    n = len(sig_m1)
    res_e = np.empty(n, np.int64); res_d = np.empty(n, np.int64)
    res_r = np.empty(n); res_x = np.empty(n, np.int64)
    k = 0; busy_until = -1
    for s in range(n):
        e = sig_m1[s]
        if e <= busy_until or e >= len(m1o): continue
        d = sig_dir[s]; R = sig_sl[s]
        if d > 0:
            entry = m1o[e] + cost; sl = entry - R; tp = entry + sig_tp[s]
        else:
            entry = m1o[e]; sl = entry + R; tp = entry - sig_tp[s]
        best = 0.0; be_done = False; part_done = False; realized = 0.0; rem = 1.0
        j = e; exit_r = 0.0
        while True:
            # adverse first (pessimistic)
            if d > 0:
                lo = m1l[j] if j > e else min(m1l[j], m1o[j])
                hi = m1h[j]
                if lo <= sl:
                    px = min(sl, m1o[j]) if j > e else sl
                    exit_r = realized + rem * (px - entry) / R; break
                if hi >= tp:
                    exit_r = realized + rem * (tp - entry) / R; break
                fav = (hi - entry) / R
            else:
                hi = m1h[j] + cost; lo = m1l[j] + cost
                if hi >= sl:
                    px = max(sl, m1o[j] + cost) if j > e else sl
                    exit_r = realized + rem * (entry - px) / R; break
                if lo <= tp:
                    exit_r = realized + rem * (entry - tp) / R; break
                fav = (entry - lo) / R
            if fav > best: best = fav
            if partial_frac > 0 and not part_done and best >= partial_r:
                realized += partial_frac * partial_r; rem -= partial_frac; part_done = True
            if not be_done and best >= be_r:
                be_done = True
                nsl = entry + d * be_lock_r * R
                if d > 0 and nsl > sl: sl = nsl
                if d < 0 and nsl < sl: sl = nsl
            if trail_dist_r > 0 and best >= trail_start_r:
                nsl = entry + d * (best - trail_dist_r) * R
                if d > 0 and nsl > sl: sl = nsl
                if d < 0 and nsl < sl: sl = nsl
            j += 1
            timeout = (j - e) >= max_bars
            tod = (m1t[j] + day_sec_off) % 86400 if j < len(m1t) else 0
            end_day = close_hour_sec > 0 and tod >= close_hour_sec
            if j >= len(m1o) - 1 or timeout or end_day or (m1t[j] - m1t[j-1]) > 6 * 3600:
                px = m1o[j] if j < len(m1o) else m1c[j - 1]
                if d > 0: exit_r = realized + rem * (px - entry) / R
                else: exit_r = realized + rem * (entry - (px + cost)) / R
                break
        res_e[k] = e; res_d[k] = d; res_r[k] = exit_r; res_x[k] = j; k += 1
        busy_until = j
    return res_e[:k], res_d[:k], res_r[:k], res_x[:k]


def stats(r):
    r = np.asarray(r)
    if len(r) == 0: return dict(n=0)
    w = r[r > 0].sum(); l = -r[r < 0].sum()
    eq = np.cumsum(r); dd = (np.maximum.accumulate(eq) - eq).max()
    return dict(n=len(r), win=round((r > 0).mean() * 100, 1), pf=round(w / l, 2) if l > 0 else np.inf,
                expR=round(r.mean(), 3), totR=round(r.sum(), 1), maxddR=round(dd, 1))

"""v6 research library: real MT5 data (EURUSD + EURJPY/GBPJPY/CHFJPY, broker server time, real per-minute spread),
currency-strength meter, ForexFactory calendar (server time), M5 features and trade simulation for both directions."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from rlib import resample, ema, sma, atr, rsi, adx, htf_index
from numba import njit

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DATA = os.path.join(ROOT, "data", "m1")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "v6_cache")
os.makedirs(CACHE, exist_ok=True)

def load(sym):
    p = os.path.join(CACHE, f"{sym}_m1.npz")
    if os.path.exists(p):
        z = np.load(p); return {k: z[k] for k in z.files}
    d = pd.read_csv(os.path.join(DATA, f"{sym}_MT5c.csv"))
    m = {k: d[k].values.astype(np.int64 if k == "time" else np.float64) for k in ["time", "open", "high", "low", "close", "spread"]}
    np.savez(p, **m); return m

def align(ref_t, m):
    """close of another symbol at (or before) each reference M1 time"""
    i = np.searchsorted(m["time"], ref_t, side="right") - 1
    return np.where(i >= 0, m["close"][np.maximum(i, 0)], np.nan)

def calendar():
    c = pd.read_csv(os.path.join(ROOT, "data", "calendar.csv"))
    return c[c.timed == 1]

FOMC_EXTRA = ["2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
              "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09"]

def load_oos(sym, spread_pts=8):
    d = pd.read_csv(os.path.join(DATA, f"{sym}_OOS2026.csv"))
    m = {k: d[k].values.astype(np.int64 if k == "time" else np.float64) for k in ["time", "open", "high", "low", "close"]}
    m["spread"] = np.full(len(d), float(spread_pts)); return m

def build_features(src="MT5"):
    p = os.path.join(CACHE, f"feat_{src}.pkl")
    if os.path.exists(p): return pd.read_pickle(p), (load("EURUSD") if src == "MT5" else load_oos("EURUSD"))
    m1 = load("EURUSD") if src == "MT5" else load_oos("EURUSD"); m5 = resample(m1, 300); h1 = resample(m1, 3600); d1 = resample(m1, 86400)
    t = m5["time"]; o, h, l, c = m5["open"], m5["high"], m5["low"], m5["close"]
    hi = htf_index(t, 300, h1["time"], 3600); ok = hi >= 0; hi2 = np.where(ok, hi, 0)
    H = lambda arr: np.where(ok, arr[hi2], np.nan)
    A = H(atr(h1["high"], h1["low"], h1["close"], 14)); A240 = H(atr(h1["high"], h1["low"], h1["close"], 240))
    f = {"time": t, "close": c, "atr": A, "volr": A / A240}
    f["hour"] = (t % 86400) // 3600; f["minute"] = (t % 3600) // 60; f["dow"] = ((t // 86400) + 4) % 7
    f["m1_next"] = np.r_[m5["m1_start"][1:], len(m1["open"]) - 1]; f["next_gap"] = np.r_[t[1:] - t[:-1], 99999]
    f["spread"] = m1["spread"][m5["m1_end"] - 1]
    f["rsi3"] = rsi(c, 3); f["rsi7"] = rsi(c, 7); f["rsi14"] = rsi(c, 14)
    sd = pd.Series(c).rolling(20).std(ddof=0).values; mid = sma(c, 20); f["bb"] = (c - mid) / np.where(sd > 0, sd, np.nan)
    def lag(k): return np.r_[np.full(k, np.nan), c[:-k]]
    for k, name in [(1, "r5m"), (3, "r15m"), (12, "r1h"), (48, "r4h"), (288, "r24h")]:
        f[name] = (c - lag(k)) / A
    f["d_ema20"] = (c - ema(c, 20)) / A; f["d_ema50"] = (c - ema(c, 50)) / A; f["d_ema200"] = (c - ema(c, 200)) / A
    h1c = h1["close"]
    f["h1_rsi"] = H(rsi(h1c, 14)); f["h1_trend"] = H(ema(h1c, 50) - ema(h1c, 200)) / A; f["h1_d50"] = H(h1c - ema(h1c, 50)) / A
    ax, pdi, ndi = adx(h1["high"], h1["low"], h1c, 14); f["h1_adx"] = H(ax); f["h1_di"] = H(pdi - ndi)
    # MACD H1 histogram
    mac = ema(h1c, 12) - ema(h1c, 26); f["h1_macd"] = H(mac - ema(mac, 9)) / A
    h4 = resample(m1, 14400); i4 = htf_index(t, 300, h4["time"], 14400); ok4 = i4 >= 0
    f["h4_d50"] = np.where(ok4, (h4["close"] - ema(h4["close"], 50))[np.maximum(i4, 0)], np.nan) / A
    idd = htf_index(t, 300, d1["time"], 86400); okd = idd >= 0
    f["d1_d20"] = np.where(okd, (d1["close"] - ema(d1["close"], 20))[np.maximum(idd, 0)], np.nan) / A
    f["d1_d50"] = np.where(okd, (d1["close"] - ema(d1["close"], 50))[np.maximum(idd, 0)], np.nan) / A
    day = t // 86400; s = pd.DataFrame({"day": day, "o": o, "h": h, "l": l, "c": c, "tod": t % 86400})
    dopen = s.groupby("day").o.transform("first").values
    f["d_open"] = (c - dopen) / A
    f["d_high"] = (c - s.groupby("day").h.cummax().values) / A; f["d_low"] = (c - s.groupby("day").l.cummin().values) / A
    rng = s.groupby("day").h.cummax().values - s.groupby("day").l.cummin().values
    f["d_pos"] = (c - s.groupby("day").l.cummin().values) / np.where(rng > 0, rng, np.nan)
    dd = s.groupby("day").agg(o=("o", "first"), c=("c", "last"), h=("h", "max"), l=("l", "min")); prev = dd.shift(1)
    mp = lambda ser: pd.Series(day).map(ser).values
    f["prev_rng"] = mp(prev.h - prev.l) / A; f["prev_ret"] = mp(prev.c - prev.o) / A
    f["prev_pos"] = mp((prev.c - prev.l) / (prev.h - prev.l))
    f["pdh"] = (c - mp(prev.h)) / A; f["pdl"] = (c - mp(prev.l)) / A
    asia = s[(s.tod >= 3600) & (s.tod < 9 * 3600)].groupby("day").agg(ah=("h", "max"), al=("l", "min"))
    after9 = (t % 86400) >= 9 * 3600
    f["asia_size"] = np.where(after9, (mp(asia.ah) - mp(asia.al)) / A, np.nan)
    f["asia_pos"] = np.where(after9, (c - mp(asia.al)) / np.maximum(mp(asia.ah) - mp(asia.al), 1e-9), np.nan)
    wk = (t + 4 * 86400) // 604800; f["w_open"] = (c - pd.Series(o).groupby(wk).transform("first").values) / A
    # month-end / start
    dt = pd.to_datetime(t, unit="s"); f["dom"] = dt.day.values; f["month"] = dt.month.values
    bd = pd.Series(day).map(pd.Series(np.arange(len(dd)), index=dd.index))  # trading-day number
    mon = pd.Series(pd.to_datetime(dd.index * 86400, unit="s").to_period("M"), index=dd.index)
    last = mon != mon.shift(-1); f["month_end"] = mp(last).astype(float)
    # ---- currency strength meter (vs JPY numeraire) at M5 close
    ref = m1["time"][m5["m1_end"] - 1]
    eu = m1["close"][m5["m1_end"] - 1]
    if src == "MT5":
        ej = align(ref, load("EURJPY")); gj = align(ref, load("GBPJPY")); cj = align(ref, load("CHFJPY"))
    else:  # same currency basket from the USD majors (triangular identities)
        uj = align(ref, load_oos("USDJPY")); gu = align(ref, load_oos("GBPUSD")); uc = align(ref, load_oos("USDCHF"))
        ej = eu * uj; gj = gu * uj; cj = uj / uc
    L = {"EUR": np.log(ej), "USD": np.log(ej / eu), "GBP": np.log(gj), "CHF": np.log(cj), "JPY": np.zeros(len(t))}
    mean = sum(L.values()) / 5.0
    S = {k: (v - mean) for k, v in L.items()}
    vol = A / c  # relative ATR
    for k in ("EUR", "USD", "GBP", "JPY"):
        sv = S[k]
        f[f"s_{k}_1h"] = (sv - np.r_[np.full(12, np.nan), sv[:-12]]) / vol
        f[f"s_{k}_4h"] = (sv - np.r_[np.full(48, np.nan), sv[:-48]]) / vol
        f[f"s_{k}_day"] = (sv - pd.Series(sv).groupby(day).transform("first").values) / vol
        f[f"s_{k}_24h"] = (sv - np.r_[np.full(288, np.nan), sv[:-288]]) / vol
    # EUR move that is EUR-specific vs USD-specific (decomposition of EURUSD move)
    # ---- news (high impact, EUR/USD), from the calendar
    cal = calendar(); hiev = cal[(cal.impact == 3) & cal.Currency.isin(["USD", "EUR"])]
    et = np.sort(hiev.time.values.astype(np.int64))
    j = np.searchsorted(et, t + 300, side="left")  # next event at/after bar close
    f["news_next"] = np.where(j < len(et), (et[np.minimum(j, len(et) - 1)] - (t + 300)) / 60.0, 1e6)
    f["news_prev"] = np.where(j > 0, ((t + 300) - et[np.maximum(j - 1, 0)]) / 60.0, 1e6)
    evday = pd.Series(1, index=np.unique(et // 86400))
    f["news_today"] = pd.Series(day).map(pd.Series(np.bincount((et // 86400 - day.min()).clip(0)), index=np.arange(day.min(), day.min() + len(np.bincount((et // 86400 - day.min()).clip(0)))))).fillna(0).values
    for nm, pat, cur in [("nfp", "^Non-Farm Employment Change", "USD"), ("fomc", "Federal Funds Rate", "USD"),
                         ("ecb", "Main Refinancing Rate", "EUR"), ("uscpi", "^CPI m/m", "USD")]:
        ev = cal[(cal.Currency == cur) & cal.Event.str.contains(pat)]
        days = ev.time.values // 86400
        if nm == "fomc":
            days = np.r_[days, (pd.to_datetime(FOMC_EXTRA) - pd.Timestamp("1970-01-01")) // pd.Timedelta(days=1)]
        f[f"day_{nm}"] = np.isin(day, days).astype(float)
    f["cal_ok"] = (t <= cal.time.max()).astype(float)
    X = pd.DataFrame(f); X.to_pickle(p)
    return X, m1

@njit(cache=True)
def trade(o, h, l, sp, tm, e, d, R, tpR, be_t, be_l, t1, t2, minp, pt, nct=0):
    """one trade from M1 open[e]; d=+1 long/-1 short; bid prices + per-minute spread (points * pt).
    From minute-of-day t1 the position is closed as soon as its profit reaches minp R (tick by tick, like the EA),
    otherwise at t2 at the latest. Returns (R, exit index)."""
    n = len(o)
    entry = o[e] + sp[e] * pt if d > 0 else o[e]
    sl = entry - d * R; tp = entry + d * tpR * R; best = 0.0; j = e; late = False
    while j < n - 1:
        s = sp[j] * pt
        if j > e:
            if tm[j] - tm[j - 1] > 4 * 3600:  # weekend / data gap: exit at the open
                px = o[j] if d > 0 else o[j] + s
                return d * (px - entry) / R, j
            tod = (tm[j] % 86400) // 60
            if tod >= t1: late = True
            if late:
                px = o[j] if d > 0 else o[j] + s
                cur = d * (px - entry) / R
                if cur >= minp or tod >= t2 or (nct > 0 and tm[j] >= nct): return cur, j
        if d > 0:
            if l[j] <= sl: return ((min(sl, o[j]) if j > e else sl) - entry) / R, j
            if h[j] >= tp: return (tp - entry) / R, j
            fav = (h[j] - entry) / R
        else:
            if h[j] + s >= sl: return (entry - (max(sl, o[j] + s) if j > e else sl)) / R, j
            if l[j] + s <= tp: return (entry - tp) / R, j
            fav = (entry - (l[j] + s)) / R
        if late and fav >= minp: return minp, j
        if fav > best: best = fav
        if best >= be_t:
            nsl = entry + d * be_l * R
            if (d > 0 and nsl > sl) or (d < 0 and nsl < sl): sl = nsl
        j += 1
    return 0.0, j

@njit(cache=True)
def trades(o, h, l, sp, tm, ents, ds, Rs, tpR, be_t, be_l, t1s, t2s, minp, pt, ncts):
    n = len(ents); r = np.empty(n); x = np.empty(n, np.int64)
    for k in range(n):
        r[k], x[k] = trade(o, h, l, sp, tm, ents[k], ds[k], Rs[k], tpR, be_t, be_l, t1s[k], t2s[k], minp, pt, ncts[k])
    return r, x

@njit(cache=True)
def select(st, xt, day, maxpos, maxday, gap):
    """EA-like acceptance of signals in time order: positions open < maxpos, trades per day < maxday, min gap (s)."""
    n = len(st); acc = np.zeros(n, np.bool_); open_x = np.full(64, -1, np.int64); last = -10**12; cday = -1; cnt = 0
    for k in range(n):
        if day[k] != cday: cday = day[k]; cnt = 0
        if cnt >= maxday or st[k] - last < gap: continue
        nopen = 0
        for q in range(64):
            if open_x[q] > st[k]: nopen += 1
        if nopen >= maxpos: continue
        for q in range(64):
            if open_x[q] <= st[k]:
                open_x[q] = xt[k]; break
        acc[k] = True; last = st[k]; cnt += 1
    return acc

def run(X, m1, mask, d, tpR=3.0, be_t=1.0, be_l=0.1, t1=15 * 60, t2=17 * 60, minp=0.05, slk=3.0, extra_pts=0.0, news_close=False):
    """simulate all signals in mask (direction d scalar or array) -> DataFrame of independent trades"""
    idx = np.flatnonzero(mask & (X.next_gap.values <= 600) & np.isfinite(X.atr.values))
    ents = X.m1_next.values[idx]; R = slk * X.atr.values[idx]
    ds = np.full(len(idx), d, np.int64) if np.isscalar(d) else np.asarray(d)[idx].astype(np.int64)
    t1s = np.full(len(idx), t1, np.int64) if np.isscalar(t1) else np.asarray(t1)[idx].astype(np.int64)
    t2s = np.full(len(idx), t2, np.int64) if np.isscalar(t2) else np.asarray(t2)[idx].astype(np.int64)
    sp = m1["spread"] + extra_pts
    ncts = np.zeros(len(idx), np.int64)
    if news_close:  # held (losing) positions are closed 10 min before the first high-impact EUR/USD event after t1
        cal = calendar(); et = np.sort(cal[(cal.impact == 3) & cal.Currency.isin(["USD", "EUR"])].time.values.astype(np.int64))
        tstart = (X.time.values[idx] // 86400) * 86400 + t1s * 60
        j = np.searchsorted(et, tstart)
        nxt = np.where(j < len(et), et[np.minimum(j, len(et) - 1)], 0)
        ok = (nxt > 0) & (nxt < (X.time.values[idx] // 86400) * 86400 + t2s * 60)
        ncts = np.where(ok, nxt - 600, 0).astype(np.int64)
    r, x = trades(m1["open"], m1["high"], m1["low"], sp, m1["time"], ents, ds, R, tpR, be_t, be_l, t1s, t2s, minp, 1e-5, ncts)
    T = pd.DataFrame({"i": idx, "time": X.time.values[idx], "entry_t": m1["time"][ents], "exit_t": m1["time"][x], "d": ds, "R": r})
    T["day"] = T.time // 86400; T["year"] = pd.to_datetime(T.time, unit="s").dt.year
    return T

def portfolio(T, maxpos=2, maxday=2, gap=3600):
    T = T.sort_values("entry_t").reset_index(drop=True)
    acc = select(T.entry_t.values, T.exit_t.values, T.day.values, maxpos, maxday, gap)
    return T[acc].reset_index(drop=True)

def stats(T, risk=0.5, label=""):
    """compounded equity with fixed % risk per trade (trades sized at entry, P&L booked at exit order)"""
    if len(T) == 0: return dict(label=label, n=0)
    r = T.sort_values("exit_t").R.values
    eq = np.cumprod(1 + r * risk / 100.0); peak = np.maximum.accumulate(np.r_[1.0, eq])[1:]
    dd = (1 - eq / peak).max() * 100
    w = r[r > 0].sum(); ls = -r[r < 0].sum()
    return dict(label=label, n=len(r), win=round((r > 0).mean() * 100, 1), exp=round(r.mean(), 4), PF=round(w / ls if ls > 0 else 99, 2),
                ret=round((eq[-1] - 1) * 100, 1), dd=round(dd, 1), sumR=round(r.sum(), 1))

def yearly(T):
    g = T.groupby("year").R
    return pd.DataFrame({"n": g.size(), "win": (g.apply(lambda s: (s > 0).mean() * 100)).round(0), "sumR": g.sum().round(1)})

def equity(T, risk):
    r = T.sort_values("exit_t").R.values
    eq = np.cumprod(1 + r * risk / 100.0); peak = np.maximum.accumulate(np.r_[1.0, eq])[1:]
    return eq, (1 - eq / peak).max() * 100

def risk_for_dd(T, target=20.0):
    lo, hi = 0.01, 5.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if equity(T, mid)[1] > target: hi = mid
        else: lo = mid
    return lo

def norm(T, target=20.0, label=""):
    """risk per trade giving a max drawdown of `target` %, and the resulting return (19y and 2019-2025)"""
    r = risk_for_dd(T, target); eq, dd = equity(T, r)
    U = T[T.year >= 2019]; equ, ddu = equity(U, r)
    s = stats(T, r)
    return dict(label=label, n=len(T), win=s["win"], PF=s["PF"], risk=round(r, 3), ret19y=round((eq[-1] - 1) * 100), ret2019=round((equ[-1] - 1) * 100), dd2019=round(ddu, 1))

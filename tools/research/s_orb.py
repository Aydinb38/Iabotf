import sys; sys.path.insert(0, "/home/user/Iabotf/tools/research")
from explore import *
syms = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]
F = {s: prep(s, "IS") for s in syms}

def orb(f, ra=2, rb=9, last_entry=13, sl_mode="mid", buf_atr=0.0, min_rng_atr=0, max_rng_atr=99):
    m5 = f["m5"]; t = m5["time"]; c = m5["close"]; h = m5["high"]; l = m5["low"]; a = f["atr"]
    day = t // 86400; hr = f["hour"]
    n = len(t); L = np.zeros(n, bool); S = np.zeros(n, bool); sl = np.full(n, np.nan); rng_arr = np.full(n, np.nan)
    df = pd.DataFrame({"day": day, "hr": hr, "h": h, "l": l})
    inr = (hr >= ra) & (hr < rb)
    g = df[inr].groupby("day").agg(rh=("h", "max"), rl=("l", "min"), cnt=("h", "size"))
    rh = pd.Series(day).map(g["rh"]).values; rl = pd.Series(day).map(g["rl"]).values
    cnt = pd.Series(day).map(g["cnt"]).values
    rng = rh - rl
    win = (hr >= rb) & (hr < last_entry) & (cnt >= (rb - ra) * 10)
    okr = (rng >= min_rng_atr * a * 12 ** 0.5) & (rng <= max_rng_atr * a * 12 ** 0.5)
    brk_l = win & okr & (c > rh + buf_atr * a); brk_s = win & okr & (c < rl - buf_atr * a)
    # first breakout of the day only
    seen = {}
    for i in np.flatnonzero(brk_l | brk_s):
        if day[i] in seen: continue
        seen[day[i]] = 1
        if brk_l[i]: L[i] = True; sl[i] = c[i] - (rl[i] if sl_mode == "opp" else (rh[i] + rl[i]) / 2)
        else: S[i] = True; sl[i] = (rh[i] if sl_mode == "opp" else (rh[i] + rl[i]) / 2) - c[i]
        rng_arr[i] = rng[i]
    return L, S, sl, rng_arr

for cfg in [dict(), dict(sl_mode="opp"), dict(ra=1, rb=9), dict(ra=3, rb=10, last_entry=14), dict(min_rng_atr=0.5, max_rng_atr=2.0)]:
    for tpm in [1.0, 2.0]:
        allr = []; line = []
        for s in syms:
            L, S, sl, rng = orb(F[s], **cfg)
            e, d, r = run(F[s], s, L, S, sl, sl * tpm, max_bars=10**9, close_hour=22)
            st = stats(r); allr += list(r); line.append(f"{s}:{st['n']}/{st['win']}%/pf{st['pf']}/e{st['expR']}")
        print(cfg, "TPxSL", tpm, stats(allr), "|", " ".join(line))

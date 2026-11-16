import sys; sys.path.insert(0, "/home/user/Iabotf/tools/research")
from explore import *
syms = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]
F = {s: prep(s, "IS") for s in syms}

def trend_signals(f, look=6, adx_min=20, rsi_lo=50, rsi_hi=70, h0=9, h1_=19, slb=0.3, minsl=1.0, maxsl=3.0):
    m5 = f["m5"]; o, h, l, c = m5["open"], m5["high"], m5["low"], m5["close"]; a = f["atr"]
    ef, es = f["ema_f"], f["ema_s"]
    up = (f["h_c"] > f["h_e200"]) & (f["h_e50"] > f["h_e200"]) & (ef > es) & (c > es)
    dn = (f["h_c"] < f["h_e200"]) & (f["h_e50"] < f["h_e200"]) & (ef < es) & (c < es)
    ll = pd.Series(l).rolling(look).min().values; hh = pd.Series(h).rolling(look).max().values
    touch_l = ll <= ef + 0.1 * a; touch_s = hh >= ef - 0.1 * a
    trig_l = (c > o) & (c > np.roll(h, 1)) & (c > ef)
    trig_s = (c < o) & (c < np.roll(l, 1)) & (c < ef)
    sess = (f["hour"] >= h0) & (f["hour"] < h1_)
    mom_l = (f["rsi"] > rsi_lo) & (f["rsi"] < rsi_hi); mom_s = (f["rsi"] < 100 - rsi_lo) & (f["rsi"] > 100 - rsi_hi)
    st = f["adx"] > adx_min
    L = up & touch_l & trig_l & sess & mom_l & st
    S = dn & touch_s & trig_s & sess & mom_s & st
    sl_l = c - (ll - slb * a); sl_s = (hh + slb * a) - c
    sl = np.where(L, sl_l, sl_s)
    sl = np.clip(sl, minsl * a, maxsl * a)
    return np.nan_to_num(L), np.nan_to_num(S), sl

print("== trend pullback, varying exits")
for rr, be, part in [(1.0, 99, 0), (1.5, 99, 0), (2.0, 99, 0), (1.5, 1.0, 0), (2.0, 1.0, 0), (2.0, 1.0, 0.5), (3.0, 1.0, 0.5), (1.0, 0.6, 0)]:
    allr = []
    line = []
    for s in syms:
        L, S, sl = trend_signals(F[s])
        e, d, r = run(F[s], s, L.astype(bool), S.astype(bool), sl, sl * rr, be_r=be, be_lock=0.1,
                      max_bars=240, close_hour=23, partial_r=1.0, partial_frac=part)
        st = stats(r); allr += list(r); line.append(f"{s}:{st['n']}/{st['win']}%/pf{st['pf']}")
    print(f"RR{rr} BE{be} P{part}", stats(allr), " | ".join(line))

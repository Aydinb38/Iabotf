import sys; sys.path.insert(0, "/home/user/Iabotf/tools/research")
from explore import *
import rlib
syms = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]
F = {s: prep(s, "IS") for s in syms}
for s in syms:
    f = F[s]; h1 = f["h1"]
    ha = atr(h1["high"], h1["low"], h1["close"], 14)
    hi = htf_index(f["m5"]["time"], 300, h1["time"], 3600); hi2 = np.where(hi >= 0, hi, 0)
    f["h_atr"] = np.where(hi >= 0, ha[hi2], np.nan)
    # previous-day high/low (server day)
    m5 = f["m5"]; day = m5["time"] // 86400
    d = pd.DataFrame({"day": day, "h": m5["high"], "l": m5["low"], "c": m5["close"]}).groupby("day").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    prev = d.shift(1)
    f["pdh"] = pd.Series(day).map(prev["h"]).values; f["pdl"] = pd.Series(day).map(prev["l"]).values

def report(name, fn, rr_list=(1.0, 2.0), **kw):
    for rr in rr_list:
        for gross in (True, False):
            allr = []; line = []
            for s in syms:
                save = rlib.COST[s]
                if gross: rlib.COST[s] = 0.0
                L, S, sl = fn(F[s])
                e, d, r = run(F[s], s, L, S, sl, sl * rr, **kw)
                rlib.COST[s] = save
                st = stats(r); allr += list(r); line.append(f"{s[:3]}:{st['n']}/{st['win']}/e{st['expR']}")
            st = stats(allr)
            print(f"{name:28s} RR{rr} {'GROSS' if gross else 'NET  '} n={st['n']} win={st['win']} pf={st['pf']} e={st['expR']} |", " ".join(line))

def trend_big(f, h0=9, h1_=19):
    m5 = f["m5"]; o, h, l, c = m5["open"], m5["high"], m5["low"], m5["close"]; a = f["atr"]; ef, es = f["ema_f"], f["ema_s"]
    up = (f["h_c"] > f["h_e200"]) & (f["h_e50"] > f["h_e200"]) & (ef > es)
    dn = (f["h_c"] < f["h_e200"]) & (f["h_e50"] < f["h_e200"]) & (ef < es)
    ll = pd.Series(l).rolling(6).min().values; hh = pd.Series(h).rolling(6).max().values
    trig_l = (c > o) & (c > np.roll(h, 1)) & (c > ef) & (ll <= ef + 0.1 * a)
    trig_s = (c < o) & (c < np.roll(l, 1)) & (c < ef) & (hh >= ef - 0.1 * a)
    sess = (f["hour"] >= h0) & (f["hour"] < h1_)
    return up & trig_l & sess, dn & trig_s & sess, 1.5 * f["h_atr"]

def pdhl_break(f):
    m5 = f["m5"]; c = m5["close"]; pc = np.roll(c, 1); sess = (f["hour"] >= 9) & (f["hour"] < 20)
    L = (c > f["pdh"]) & (pc <= f["pdh"]) & sess; S = (c < f["pdl"]) & (pc >= f["pdl"]) & sess
    return L, S, 1.0 * f["h_atr"]

def pdhl_fade(f):
    m5 = f["m5"]; c = m5["close"]; pc = np.roll(c, 1); sess = (f["hour"] >= 9) & (f["hour"] < 20)
    S = (c > f["pdh"]) & (pc <= f["pdh"]) & sess; L = (c < f["pdl"]) & (pc >= f["pdl"]) & sess
    return L, S, 1.0 * f["h_atr"]

def rsi2_h1_mr(f):
    # M5 RSI(3) extreme in direction of H1 trend (buy dips in uptrend)
    up = (f["h_c"] > f["h_e200"]) & (f["h_e50"] > f["h_e200"]); dn = (f["h_c"] < f["h_e200"]) & (f["h_e50"] < f["h_e200"])
    sess = (f["hour"] >= 9) & (f["hour"] < 20)
    return up & (f["rsi2"] < 10) & sess, dn & (f["rsi2"] > 90) & sess, 1.0 * f["h_atr"]

def momentum_impulse(f):
    m5 = f["m5"]; o, c = m5["open"], m5["close"]; a = f["atr"]
    body = c - o; sess = (f["hour"] >= 9) & (f["hour"] < 20)
    return (body > 2.0 * a) & sess, (body < -2.0 * a) & sess, 1.0 * f["h_atr"]

def impulse_fade(f):
    L, S, sl = momentum_impulse(f); return S, L, sl

report("trend_pullback_H1ATR", trend_big, max_bars=288, close_hour=23)
report("pdh/pdl breakout", pdhl_break, max_bars=288, close_hour=23)
report("pdh/pdl fade", pdhl_fade, max_bars=288, close_hour=23)
report("rsi3 dip in H1 trend", rsi2_h1_mr, max_bars=288, close_hour=23)
report("impulse follow", momentum_impulse, max_bars=288, close_hour=23)
report("impulse fade", impulse_fade, max_bars=288, close_hour=23)

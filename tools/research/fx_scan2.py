"""Larger-scale Forex ideas (costs become small vs targets), M5 entry timing. IS 2014-2017."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
F = {s: prep(s, "IS") for s in FX}
for s, f in F.items():
    m1 = f["m1"]; t5 = f["m5"]["time"]
    for name, sec in [("h4", 14400), ("d1", 86400)]:
        b = resample(m1, sec); hi = htf_index(t5, 300, b["time"], sec); ok = hi >= 0; hi2 = np.where(ok, hi, 0)
        c = b["close"]
        f[f"{name}_c"] = np.where(ok, c[hi2], np.nan)
        for n in (20, 50, 200): f[f"{name}_e{n}"] = np.where(ok, ema(c, n)[hi2], np.nan)
        f[f"{name}_atr"] = np.where(ok, atr(b["high"], b["low"], c, 14)[hi2], np.nan)
        mid = sma(c, 20); sd = pd.Series(c).rolling(20).std(ddof=0).values
        f[f"{name}_mid"] = np.where(ok, mid[hi2], np.nan); f[f"{name}_sd"] = np.where(ok, sd[hi2], np.nan)
        f[f"{name}_rsi2"] = np.where(ok, rsi(c, 2)[hi2], np.nan)
        ax, _, _ = adx(b["high"], b["low"], c, 14); f[f"{name}_adx"] = np.where(ok, ax[hi2], np.nan)
        dh = pd.Series(b["high"]).rolling(20).max().values; dl = pd.Series(b["low"]).rolling(20).min().values
        f[f"{name}_dh"] = np.where(ok, dh[hi2], np.nan); f[f"{name}_dl"] = np.where(ok, dl[hi2], np.nan)

def sess(f, a=9, b=20): return (f["hour"] >= a) & (f["hour"] < b) & (f["dow"] >= 1) & (f["dow"] <= 5)

IDEAS = {}
def idea(name):
    def d(fn): IDEAS[name] = fn; return fn
    return d

@idea("H1 trend + M5 RSI3 dip (gold logic)")
def _(f):
    u = (f["h1_c"] > f["h1_e200"]) & (f["h1_e50"] > f["h1_e200"]); d = (f["h1_c"] < f["h1_e200"]) & (f["h1_e50"] < f["h1_e200"])
    return u & sess(f) & (f["rsi3"] < 10), d & sess(f) & (f["rsi3"] > 90), 3 * f["h1_atr"], 4.0, dict(be_r=0.8, be_lock=0.1, tr_s=2, tr_d=1.5)
@idea("H4 trend + M5 RSI3 dip")
def _(f):
    u = (f["h4_c"] > f["h4_e200"]) & (f["h4_e50"] > f["h4_e200"]); d = (f["h4_c"] < f["h4_e200"]) & (f["h4_e50"] < f["h4_e200"])
    return u & sess(f) & (f["rsi3"] < 10), d & sess(f) & (f["rsi3"] > 90), 1.5 * f["h4_atr"], 4.0, dict(be_r=0.8, be_lock=0.1, tr_s=2, tr_d=1.5)
@idea("D1 trend + H4 RSI2 pullback, M5 entry")
def _(f):
    u = (f["d1_c"] > f["d1_e200"]) & (f["d1_e50"] > f["d1_e200"]); d = (f["d1_c"] < f["d1_e200"]) & (f["d1_e50"] < f["d1_e200"])
    return u & sess(f) & (f["h4_rsi2"] < 10) & (f["rsi3"] < 20), d & sess(f) & (f["h4_rsi2"] > 90) & (f["rsi3"] > 80), 1.0 * f["d1_atr"], 3.0, dict(be_r=1.0, be_lock=0.1, tr_s=2, tr_d=1.5)
@idea("D1 Donchian-20 breakout (trend following)")
def _(f):
    c = f["m5"]["close"]
    return sess(f) & (c > f["d1_dh"]), sess(f) & (c < f["d1_dl"]), 2.0 * f["d1_atr"], 4.0, dict(be_r=1.0, be_lock=0.1, tr_s=1.5, tr_d=1.5)
@idea("H4 Bollinger 2.5 fade, ranging (ADX H4<20)")
def _(f):
    c = f["m5"]["close"]; rng = f["h4_adx"] < 20
    up = f["h4_mid"] + 2.5 * f["h4_sd"]; lo = f["h4_mid"] - 2.5 * f["h4_sd"]
    return sess(f, 3, 21) & rng & (c < lo), sess(f, 3, 21) & rng & (c > up), 1.5 * f["h4_atr"], 1.5, dict()
@idea("D1 RSI2 mean reversion fade (crosses)")
def _(f):
    return sess(f) & (f["d1_rsi2"] < 5) & (f["rsi3"] > 50), sess(f) & (f["d1_rsi2"] > 95) & (f["rsi3"] < 50), 1.0 * f["d1_atr"], 1.0, dict()

pd.set_option("display.width", 250)
for name, fn in IDEAS.items():
    res = {}; allr = []; yrs = {}
    for s, f in F.items():
        L, S, sl, rr, kw = fn(f)
        r, e = run(f, L, S, sl, sl * rr, max_bars=1440 * 5, **kw)
        res[s] = (len(r), r.mean() if len(r) else np.nan); allr += list(r)
        y = pd.to_datetime(f["m1"]["time"][e], unit="s").year
        for yy, v in pd.Series(r).groupby(y).sum().items(): yrs[yy] = yrs.get(yy, 0) + v
    st = stats(allr); pos = [k for k, v in res.items() if v[1] > 0.05 and v[0] >= 40]
    print(f"== {name}: n={st['n']} win={st['win']} pf={st['pf']} e={st['expR']} | pairs>+0.05R: {len(pos)} {pos} | totR by year {{{', '.join(f'{k}:{v:+.0f}' for k, v in sorted(yrs.items()))}}}")
    print("   ", " ".join(f"{k}:{v[0]}/{v[1]:+.2f}" for k, v in res.items()))

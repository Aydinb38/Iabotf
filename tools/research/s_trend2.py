import sys; sys.path.insert(0, "/home/user/Iabotf/tools/research")
from explore import *
import rlib
syms = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]
F = {s: prep(s, "IS") for s in syms}
for s in syms:
    f = F[s]; m1 = f["m1"]; t5 = f["m5"]["time"]
    for name, sec in [("h1", 3600), ("h4", 14400), ("d1", 86400)]:
        b = resample(m1, sec) if name != "h1" else f["h1"]
        hi = htf_index(t5, 300, b["time"], sec); ok = hi >= 0; hi2 = np.where(ok, hi, 0)
        c = b["close"]
        for n in (20, 50, 200):
            f[f"{name}_e{n}"] = np.where(ok, ema(c, n)[hi2], np.nan)
        f[f"{name}_c"] = np.where(ok, c[hi2], np.nan)
        f[f"{name}_atr"] = np.where(ok, atr(b["high"], b["low"], c, 14)[hi2], np.nan)
        ax, _, _ = adx(b["high"], b["low"], c, 14); f[f"{name}_adx"] = np.where(ok, ax[hi2], np.nan)

def trend(f, mode):
    if mode == "h1":   u = (f["h1_c"] > f["h1_e200"]) & (f["h1_e50"] > f["h1_e200"]); d = (f["h1_c"] < f["h1_e200"]) & (f["h1_e50"] < f["h1_e200"])
    elif mode == "h4": u = (f["h4_c"] > f["h4_e200"]) & (f["h4_e50"] > f["h4_e200"]); d = (f["h4_c"] < f["h4_e200"]) & (f["h4_e50"] < f["h4_e200"])
    elif mode == "h1h4":
        u1, d1 = trend(f, "h1"); u2, d2 = trend(f, "h4"); u = u1 & u2; d = d1 & d2
    elif mode == "h1d1":
        u1, d1 = trend(f, "h1"); u = u1 & (f["d1_c"] > f["d1_e50"]) & (f["d1_e20"] > f["d1_e50"]); d = d1 & (f["d1_c"] < f["d1_e50"]) & (f["d1_e20"] < f["d1_e50"])
    elif mode == "all":
        u1, d1 = trend(f, "h1h4"); u = u1 & (f["d1_c"] > f["d1_e50"]) & (f["d1_e20"] > f["d1_e50"]); d = d1 & (f["d1_c"] < f["d1_e50"]) & (f["d1_e20"] < f["d1_e50"])
    return u, d

def dip(f, mode, entry="rsi", h0=9, h1_=20, adxmin=0, slm=1.5):
    u, d = trend(f, mode)
    if adxmin: u = u & (f["h1_adx"] > adxmin); d = d & (f["h1_adx"] > adxmin)
    sess = (f["hour"] >= h0) & (f["hour"] < h1_)
    if entry == "rsi":
        L = u & (f["rsi2"] < 10) & sess; S = d & (f["rsi2"] > 90) & sess
    else:
        m5 = f["m5"]; o, h, l, c = m5["open"], m5["high"], m5["low"], m5["close"]; a = f["atr"]; ef = f["ema_f"]
        ll = pd.Series(l).rolling(6).min().values; hh = pd.Series(h).rolling(6).max().values
        L = u & sess & (c > o) & (c > np.roll(h, 1)) & (c > ef) & (ll <= ef + 0.1 * a)
        S = d & sess & (c < o) & (c < np.roll(l, 1)) & (c < ef) & (hh >= ef - 0.1 * a)
    return L, S, slm * f["h1_atr"]

rows = []
for mode in ["h1", "h4", "h1h4", "h1d1", "all"]:
    for entry in ["rsi", "pb"]:
        for slm in [1.5, 2.5]:
            for rr in [1.0, 2.0, 3.0]:
                for be in [99.0, 1.0]:
                    res = {}
                    allr = []
                    for s in syms:
                        L, S, sl = dip(F[s], mode, entry, slm=slm)
                        e, d, r = run(F[s], s, L, S, sl, sl * rr, be_r=be, be_lock=0.05, max_bars=1440 * 2, close_hour=0)
                        res[s] = stats(r)["expR"]; allr += list(r)
                    st = stats(allr)
                    rows.append(dict(mode=mode, entry=entry, slm=slm, rr=rr, be=be, n=st["n"], win=st["win"], pf=st["pf"], e=st["expR"], minsym=min(res.values()), **{k[:3]: v for k, v in res.items()}))
df = pd.DataFrame(rows).sort_values("e", ascending=False)
pd.set_option("display.width", 250)
print(df.head(40).to_string(index=False))
df.to_csv("trend2_grid.csv", index=False)

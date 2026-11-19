"""Stratégies complémentaires EURUSD : (1) cassure du range asiatique (1h-8h) entre 8h et 12h, (2) suivi de tendance journalier.
Corrélation avec la v9 au jour le jour."""
import v6lib as v, numpy as np, pandas as pd
from v10lib import *
from numba import njit
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
rows = []
def summarize(P, lab, extra=None):
    p = per(P.time.values) if len(P) else []
    y = P.groupby("year").R.sum()
    r = dict(test=lab, n=len(P), win=round((P.R > 0).mean() * 100, 1), exp=round(P.R.mean(), 3),
             e1=round(P.R[p == 1].mean(), 3), e2=round(P.R[p == 2].mean(), 3), e3=round(P.R[p == 3].mean(), 3), ans_pos=f"{(y > 0).sum()}/{len(y)}")
    if extra: r.update(extra)
    rows.append(r)
# v9 de référence (P&L journalier)
E7 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0); HWB = {8: 1.5, 9: 1.0, 10: 0.9, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.2}
T9 = broad("MT5", E7, rsi=65, bb=1.5, prev=6, volr=1.0); P9 = v.portfolio(T9, 10, 10, 900); P9["w"] = P9.h.map(HWB)
d9 = (P9.R * P9.w).groupby(P9.day).sum()
X, m1 = v.build_features("MT5"); t = X.time.values; tod = ((t + 300) % 86400) // 60; day = t // 86400
# (1) cassure du range asiatique : niveaux = plus haut / plus bas des clôtures M5 1h-8h
sub = pd.DataFrame({"day": day, "c": X.close.values})[((t % 86400) >= 3600) & ((t % 86400) < 8 * 3600)].groupby("day").c.agg(["max", "min"])
ah = pd.Series(day).map(sub["max"]).values; al = pd.Series(day).map(sub["min"]).values
prevc = np.r_[np.nan, X.close.values[:-1]]
wk = ((X.dow >= 1) & (X.dow <= 5)).values & (X.spread.values <= 20)
for d, cond in [(1, (X.close.values > ah) & (prevc <= ah)), (-1, (X.close.values < al) & (prevc >= al))]:
    for slk in (1.5, 3.0):
        for t2 in (17, 21):
            m = wk & cond & (tod >= 480) & (tod < 720)
            T = v.run(X, m1, m, d, tpR=3.0, be_t=1.0, be_l=0.1, minp=-99, slk=slk, t1=t2 * 60, t2=t2 * 60)
            P = v.portfolio(T, 1, 1, 86400)
            dd = P.R.groupby(P.day).sum(); j = pd.concat([d9, dd], axis=1).fillna(0)
            summarize(P, f"cassure Asie {'ACHAT' if d > 0 else 'VENTE'} SL{slk} sortie {t2}h", dict(corr_v9=round(j.corr().iloc[0, 1], 2)))
# (2) tendance journalière : cassure du plus haut / bas 20 jours (clôture D1), stop 3 ATR(D1 approx 5 x ATR H1), sortie opposée 10 jours
d1 = v.resample(m1, 86400); c = pd.Series(d1["close"]); hi20 = c.rolling(20).max().shift(1); lo20 = c.rolling(20).min().shift(1)
hi10 = c.rolling(10).max().shift(1); lo10 = c.rolling(10).min().shift(1)
pos = 0; ent = 0.0; res = []; days = []
atr_d = pd.Series(d1["high"] - d1["low"]).rolling(20).mean().values
for i in range(25, len(c)):
    px = c.iloc[i]
    if pos != 0:
        stop = ent - pos * 3 * atr_d[i - 1]
        hit = (pos > 0 and d1["low"][i] <= stop) or (pos < 0 and d1["high"][i] >= stop)
        ex = (pos > 0 and px < lo10.iloc[i]) or (pos < 0 and px > hi10.iloc[i])
        if hit or ex:
            xp = stop if hit else px
            res.append(pos * (xp - ent) / (3 * atr_d[i - 1]) - 1.5e-4 / (3 * atr_d[i - 1])); days.append(d1["time"][i]); pos = 0
    if pos == 0:
        if px > hi20.iloc[i]: pos, ent = 1, px
        elif px < lo20.iloc[i]: pos, ent = -1, px
P = pd.DataFrame({"time": days, "R": res}); P["year"] = pd.to_datetime(P.time, unit="s").dt.year; P["day"] = P.time // 86400
summarize(P, "tendance D1 (Donchian 20/10, stop 3 ATR)")
pd.set_option("display.width", 220); print(pd.DataFrame(rows).to_string(index=False))

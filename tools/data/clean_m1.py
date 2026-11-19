#!/usr/bin/env python3
"""Removes feed artifacts from an MT5 M1 export: isolated spike bars (range > 8x the local median range and not
continuous with the next bar, mostly at hh:00 in 2018-2019) are rebuilt from their open and the next open, and spread spikes are capped at the local median
spread + 5 points (rollover hours keep their real, wider spread). usage: clean_m1.py <in.csv> <out.csv>"""
import sys, numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1])
rng = (d.high - d.low).values
med = pd.Series(rng).rolling(21, center=True, min_periods=5).median().values
med = np.maximum(med, 1e-5)
nxt = np.r_[d.open.values[1:], d.close.values[-1]]
o, cl, hi, lo = d.open.values, d.close.values, d.high.values, d.low.values
# a real news spike stays continuous with the next bar; a feed artifact jumps back or has two huge wicks
jump = np.abs(cl - nxt) > 4 * med
wicks = ((hi - np.maximum(o, cl)) > 3 * med) & ((np.minimum(o, cl) - lo) > 3 * med)
spike = (rng > 8 * med) & (jump | wicks)
gap = np.r_[d.time.values[1:] - d.time.values[:-1], 999999] > 120
c = np.where(gap, d.close.values, nxt)
o = d.open.values
d.loc[spike, "close"] = c[spike]
d.loc[spike, "high"] = (np.maximum(o, c) + med)[spike]
d.loc[spike, "low"] = (np.minimum(o, c) - med)[spike]
smed = pd.Series(d.spread.values).rolling(61, center=True, min_periods=10).median().values
cap = np.maximum(smed + 5, 3)
nsp = (d.spread.values > cap).sum()
d["spread"] = np.minimum(d.spread.values, np.round(cap)).astype(int)
for k in ["open", "high", "low", "close"]: d[k] = d[k].round(5)
d.to_csv(sys.argv[2], index=False, float_format="%.5f")
print(f"spike bars rebuilt: {spike.sum()}, spreads capped: {nsp}")

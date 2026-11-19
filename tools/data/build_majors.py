#!/usr/bin/env python3
"""Builds GBPUSD / USDJPY / USDCHF M1 series (same MT5 feed, server time) from EURUSD and the JPY crosses:
USDJPY = EURJPY / EURUSD, GBPUSD = GBPJPY / USDJPY, USDCHF = USDJPY / CHFJPY (aligned on EURUSD minutes).
Used by the v6 currency-strength filter in the emulator. usage: build_majors.py <data/m1 dir>"""
import os, sys, pandas as pd
D = sys.argv[1]
def load(s): return pd.read_csv(os.path.join(D, f"{s}_MT5c.csv"), usecols=["time", "open", "high", "low", "close"]).set_index("time")
eu = load("EURUSD")
ej, gj, cj = (load(s).reindex(eu.index, method="ffill") for s in ("EURJPY", "GBPJPY", "CHFJPY"))
uj = ej / eu; gu = gj / uj; uc = uj / cj
for name, d, dg in [("USDJPY", uj, 3), ("GBPUSD", gu, 5), ("USDCHF", uc, 5)]:
    d = d.dropna().copy()
    d["high"] = d[["open", "high", "low", "close"]].max(axis=1); d["low"] = d[["open", "high", "low", "close"]].min(axis=1)
    d.round(dg).reset_index().to_csv(os.path.join(D, f"{name}_MT5c.csv"), index=False, float_format=f"%.{dg}f")
    print(name, len(d))

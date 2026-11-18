#!/usr/bin/env python3
"""Converts MT5 EURUSD M1 parquet files (columns time_server, open, high, low, close, spread) into data/m1/EURUSD_MT5.csv
(time = broker server time, + real spread in points). usage: convert_mt5.py <parquet_dir> <out.csv>   (needs pyarrow)"""
import sys, glob, os, pandas as pd, numpy as np
src, out = sys.argv[1], sys.argv[2]
frames = [pd.read_parquet(p) for p in sorted(glob.glob(os.path.join(src, "*.parquet")))]
d = pd.concat(frames, ignore_index=True)
off = (d.time_server - d.time_utc).dt.total_seconds() / 3600
print("server offset hours:", off.value_counts().to_dict())
d = d[d.time_server.dt.dayofweek < 5]
d["time"] = (d.time_server - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)
d = d.drop_duplicates("time").sort_values("time")
for c in ["open", "high", "low", "close"]: d[c] = d[c].round(5)
d["high"] = d[["open", "high", "low", "close"]].max(axis=1); d["low"] = d[["open", "high", "low", "close"]].min(axis=1)
d[["time", "open", "high", "low", "close", "spread"]].to_csv(out, index=False, float_format="%.5f")
y = d.time_server.dt.year
print("rows per year:", y.value_counts().sort_index().to_dict())
print("spread (points) median by hour:", d.groupby(d.time_server.dt.hour).spread.median().astype(int).to_dict())

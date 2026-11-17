#!/usr/bin/env python3
"""Convert public M1 datasets into one unified CSV per instrument/period.

Output columns: time (broker *server* time as Unix seconds), open, high, low, close
Server time model = typical "New-York close" broker: UTC+2 in winter, UTC+3 while
US daylight saving time is active (most MT5 brokers use this).

Sources:
  * HistData M1 ASCII (EST, fixed UTC-5, no DST)  ->  2014..2018
  * getdata.finance M1 CSV samples (UTC)           ->  2026-03..2026-09
"""
import glob, io, os, sys, zipfile
import numpy as np
import pandas as pd


def us_dst_active(utc: pd.Series) -> np.ndarray:
    """True when US DST is active (2nd Sunday March 07:00 UTC -> 1st Sunday Nov 06:00 UTC)."""
    years = utc.dt.year.values
    out = np.zeros(len(utc), dtype=bool)
    for y in np.unique(years):
        march = pd.Timestamp(year=int(y), month=3, day=1, tz="UTC")
        first_sun_mar = march + pd.Timedelta(days=(6 - march.weekday()) % 7)
        start = first_sun_mar + pd.Timedelta(days=7, hours=7)
        nov = pd.Timestamp(year=int(y), month=11, day=1, tz="UTC")
        first_sun_nov = nov + pd.Timedelta(days=(6 - nov.weekday()) % 7)
        end = first_sun_nov + pd.Timedelta(hours=6)
        m = years == y
        t = utc[m]
        out[m] = ((t >= start) & (t < end)).values
    return out


def to_server_epoch(utc: pd.Series) -> np.ndarray:
    offs = np.where(us_dst_active(utc), 3 * 3600, 2 * 3600)
    epoch = pd.Timestamp("1970-01-01", tz="UTC")
    secs = ((utc - epoch) // pd.Timedelta(seconds=1)).astype("int64").values
    return secs + offs


def load_histdata(zip_paths):
    frames = []
    for zp in sorted(zip_paths):
        with zipfile.ZipFile(zp) as z:
            name = [n for n in z.namelist() if n.endswith(".csv")][0]
            df = pd.read_csv(io.BytesIO(z.read(name)), sep=";", header=None,
                             names=["dt", "open", "high", "low", "close", "vol"])
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    est = pd.to_datetime(df["dt"], format="%Y%m%d %H%M%S")
    utc = (est + pd.Timedelta(hours=5)).dt.tz_localize("UTC")
    df["time"] = to_server_epoch(utc)
    return df[["time", "open", "high", "low", "close"]]


def load_getdata(csv_path):
    df = pd.read_csv(csv_path)
    utc = pd.to_datetime(df["datetime"], utc=True)
    df["time"] = to_server_epoch(utc)
    return df[["time", "open", "high", "low", "close"]]


def clean(df, digits):
    df = df.drop_duplicates("time").sort_values("time")
    for c in ["open", "high", "low", "close"]:
        df[c] = df[c].round(digits)
    df["high"] = df[["open", "high", "low", "close"]].max(axis=1)
    df["low"] = df[["open", "high", "low", "close"]].min(axis=1)
    return df


DIGITS = {"EURUSD": 5, "GBPUSD": 5, "AUDUSD": 5, "USDCAD": 5, "USDJPY": 3, "XAUUSD": 2,
          "EURGBP": 5, "EURCHF": 5, "AUDNZD": 5, "AUDCAD": 5, "NZDCAD": 5, "EURCAD": 5, "GBPCAD": 5,
          "GBPCHF": 5, "USDCHF": 5, "EURJPY": 3, "NZDUSD": 5, "CADCHF": 5, "GBPJPY": 3}
ONLY = os.environ.get("ONLY_SYMBOLS")

if __name__ == "__main__":
    hist_root, recent_root, out_root = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out_root, exist_ok=True)
    for sym, dg in DIGITS.items():
        if ONLY and sym not in ONLY.split(","):
            continue
        zips = glob.glob(os.path.join(hist_root, sym.lower(), f"DAT_ASCII_{sym}_M1_*.zip"))
        if zips:
            df = clean(load_histdata(zips), dg)
            t = pd.to_datetime(df["time"], unit="s")
            for tag, m in {"IS": t.dt.year <= 2017, "OOS2018": t.dt.year == 2018}.items():
                part = df[m.values]
                if len(part):
                    part.to_csv(os.path.join(out_root, f"{sym}_{tag}.csv"), index=False,
                                float_format=f"%.{dg}f")
                    print(sym, tag, len(part))
        rp = os.path.join(recent_root, f"{sym}_1m.csv")
        if os.path.exists(rp):
            df = clean(load_getdata(rp), dg)
            df.to_csv(os.path.join(out_root, f"{sym}_OOS2026.csv"), index=False, float_format=f"%.{dg}f")
            print(sym, "OOS2026", len(df))

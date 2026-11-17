#!/usr/bin/env python3
"""Builds data/m1/EURUSD_ALL.csv (EURUSD M1 2005 -> 2018-08, broker server time) from the HistData zips."""
import glob, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from prepare_data import load_histdata, clean
root = sys.argv[1]; out = sys.argv[2]
zips = [z for z in glob.glob(os.path.join(root, "eurusd", "DAT_ASCII_EURUSD_M1_*.zip"))
        if not any(y in z for y in ("_2000", "_2001", "_2002", "_2003", "_2004", "201809", "201810"))]
clean(load_histdata(zips), 5).to_csv(out, index=False, float_format="%.5f")
print("written", out)

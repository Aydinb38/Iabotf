"""Rebuild features and 24h candidate trades on the real MT5 EURUSD history (2007-2025, true server time)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import eurusd_ai, eu_cand24
from fxlib import DATA
H = os.path.dirname(__file__)
X, _ = eurusd_ai.build(f"{DATA}/EURUSD_MT5.csv"); X.to_pickle(os.path.join(H, "mt5_feat.pkl"))
# candidates: reuse eu_cand24.build with the MT5 features
orig = eu_cand24.pd.read_pickle
def rp(path, *a, **k):
    if path.endswith("eurusd_feat.pkl"): path = os.path.join(H, "mt5_feat.pkl")
    return orig(path, *a, **k)
eu_cand24.pd.read_pickle = rp
D = eu_cand24.build("MT5"); D.to_pickle(os.path.join(H, "mt5_c24.pkl")); print("candidates", len(D))

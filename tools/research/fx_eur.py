"""Focus: EUR (and GBP) weakness during the European session. Gross pips per window, per year, IS & OOS."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
def piv(sym, tag):
    m1 = load_m1(f"{DATA}/{sym}_{tag}.csv"); t = pd.to_datetime(m1["time"], unit="s")
    o = pd.Series(m1["open"], index=t).resample("1h").first().dropna() / pip(sym)
    df = pd.DataFrame({"p": o}); df["date"] = df.index.date; df["hour"] = df.index.hour
    return df.pivot_table(index="date", columns="hour", values="p")
pairs = {"EURUSD": -1, "EURGBP": -1, "EURCHF": -1, "EURJPY": -1, "EURCAD": -1, "GBPUSD": -1, "GBPJPY": -1, "GBPCHF": -1, "GBPCAD": -1, "USDCHF": +1}
for (a, b) in [(9, 15), (10, 15), (11, 15), (12, 15)]:
    print(f"== window {a}h -> {b}h server, direction: short EUR/GBP (long USDCHF = short CHF... reference)")
    for sym, d in pairs.items():
        out = []
        for tag in ("IS", "OOS2018", "OOS2026"):
            try: P = piv(sym, tag)
            except FileNotFoundError: continue
            mv = ((P[b] - P[a]) * d).dropna(); yrs = pd.Series(pd.to_datetime(mv.index).year, index=mv.index)
            if tag == "IS": out.append("IS " + " ".join(f"{v:+.1f}" for v in mv.groupby(yrs).mean().values))
            else: out.append(f"{tag[3:]} {mv.mean():+.1f}")
        print(f"   {sym}: cost {PIPS[sym]:.1f} | " + " | ".join(out))

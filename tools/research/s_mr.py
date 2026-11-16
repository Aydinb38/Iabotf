import sys; sys.path.insert(0, "/home/user/Iabotf/tools/research")
from explore import *
syms = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]
F = {s: prep(s, "IS") for s in syms}

def mr(f, dev=2.0, rsi_n="rsi", rsi_x=30, slk=2.0, tpk=1.0):
    m5 = f["m5"]; c = m5["close"]; a = f["atr"]
    up = f["bb_mid"] + dev * f["bb_sd"]; lo = f["bb_mid"] - dev * f["bb_sd"]
    L = (c < lo) & (f[rsi_n] < rsi_x); S = (c > up) & (f[rsi_n] > 100 - rsi_x)
    return L, S, slk * a, tpk * a

print("== mean reversion by server hour (BB2, RSI14<30, SL2ATR TP1ATR, 2h max)")
rows = []
for s in syms:
    L, S, sl, tp = mr(F[s])
    for hh in range(24):
        hm = F[s]["hour"] == hh
        e, d, r = run(F[s], s, L & hm, S & hm, sl, tp, max_bars=120)
        st = stats(r); rows.append((s, hh, st.get("n", 0), st.get("win"), st.get("pf"), st.get("expR")))
df = pd.DataFrame(rows, columns=["sym", "hour", "n", "win", "pf", "expR"])
print(df.pivot(index="hour", columns="sym", values="expR").round(3).to_string())
print(df.pivot(index="hour", columns="sym", values="win").to_string())

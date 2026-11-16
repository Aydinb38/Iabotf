import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
F = {t: prep("EURUSD", t) for t in ["IS", "OOS2018", "OOS2026"]}
def sig(f, a, last, rx):
    tod = f["m5"]["time"] % 86400; dow = f["dow"]; wk = (dow >= 1) & (dow <= 5)
    x = wk & (tod >= a * 3600 - 300) & (tod < last * 3600 - 300) & (f["rsi3"] > rx)
    return np.zeros_like(x), x
rows = []
for a, last in [(9, 12), (10, 13), (11, 14), (10, 12)]:
    for ex in [14, 15, 16]:
        for slm in [2.0, 3.0, 4.0]:
            for tpm in [2.0, 3.0, 5.0]:
                for rx in [60, 70, 80]:
                    row = dict(win=f"{a}-{last}", exit=ex, sl=slm, tp=tpm, rsi=rx)
                    for t, f in F.items():
                        L, S = sig(f, a, last, rx); sl = slm * f["h1_atr"]
                        r, e = run(f, L, S, sl, sl * tpm, be_r=1.0, be_lock=0.1, exit_tod=ex * 60)
                        st = stats(r); row[t] = st["expR"]; row["pf_" + t] = st["pf"]
                    rows.append(row)
df = pd.DataFrame(rows)
print("IS configs:", len(df), "| share with IS PF>1.05:", round((df.pf_IS > 1.05).mean(), 2), "| median IS PF:", df.pf_IS.median(),
      "| median 2018 PF:", df.pf_OOS2018.median(), "| median 2026 PF:", df.pf_OOS2026.median())
for k in ["win", "exit", "sl", "tp", "rsi"]:
    print(f"  mean IS PF by {k}:", df.groupby(k).pf_IS.mean().round(3).to_dict())
c = df[(df.win == "10-13") & (df.exit == 15) & (df.sl == 3.0) & (df.tp == 3.0) & (df.rsi == 70)]
print("chosen:", c.to_dict("records"))
print("rank of chosen by IS PF:", int((df.pf_IS > c.pf_IS.values[0]).sum()) + 1, "/", len(df))

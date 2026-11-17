"""14-year robustness: exit-profile grid for the European-session strategy, AI module yearly R, combined portfolio,
and equity-curve based adaptive risk."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
f = prep("EURUSD", "ALL")
tod = f["m5"]["time"] % 86400; wk = (f["dow"] >= 1) & (f["dow"] <= 5)
S = wk & (tod >= 10 * 3600 - 300) & (tod < 13 * 3600 - 300) & (f["rsi3"] > 70)
rows = []
for slm in (2.0, 3.0, 4.0):
    for tpm in (0.75, 1.0, 1.5, 2.0, 3.0):
        for be in (0.5, 1.0, 99.0):
            if be < 99 and be >= tpm: continue
            sl = slm * f["h1_atr"]
            r, e = run(f, np.zeros_like(S), S, sl, tpm * sl, be_r=be, be_lock=0.1, exit_tod=15 * 60)
            y = pd.to_datetime(f["m1"]["time"][e], unit="s").year
            by = pd.Series(r).groupby(y).sum()
            rows.append(dict(sl=slm, tp=tpm, be=be, n=len(r), win=round(np.mean(r > 0) * 100, 1), pf=round(r[r > 0].sum() / -r[r < 0].sum(), 3),
                             e=round(r.mean(), 4), years_pos=int((by > 0).sum()), worst_year=round(by.min(), 1),
                             pf_0513=round(pd.Series(r)[y <= 2013][pd.Series(r)[y <= 2013] > 0].sum() / -pd.Series(r)[y <= 2013][pd.Series(r)[y <= 2013] < 0].sum(), 3)))
G = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print("Profils robustes (>= 12/14 années positives) triés par taux de réussite :")
print(G[G.years_pos >= 12].sort_values("win", ascending=False).head(15).to_string(index=False))
print("\nProfils à plus de 57 % de gagnants :")
print(G[G.win >= 57].sort_values("pf", ascending=False).head(10).to_string(index=False))
G.to_csv("eurusd_profiles_14y.csv", index=False)

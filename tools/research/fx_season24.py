"""24h session-edge scan: every server-hour window (1-6h) on every pair.
Keep windows: same sign 4/4 IS years, |IS mean| > hour-dependent cost, then check OOS 2018 / 2026 (net of cost)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *

def hourly_piv(sym, tag):
    m1 = load_m1(f"{DATA}/{sym}_{tag}.csv"); t = pd.to_datetime(m1["time"], unit="s")
    o = pd.Series(m1["open"], index=t).resample("1h").first().dropna() / pip(sym)
    df = pd.DataFrame({"p": o}); df["date"] = df.index.date; df["hour"] = df.index.hour
    df = df[pd.to_datetime(df.date).dt.dayofweek < 5]   # Monday-Friday server days
    return df.pivot_table(index="date", columns="hour", values="p")

rows = []
P = {}
for sym in FX:
    for tag in ("IS", "OOS2018", "OOS2026"):
        try: P[(sym, tag)] = hourly_piv(sym, tag)
        except FileNotFoundError: pass
for sym in FX:
    piv = P[(sym, "IS")]; years = pd.Series(pd.to_datetime(piv.index).year, index=piv.index)
    for a in range(0, 24):
        for L in (1, 2, 3, 4, 5, 6):
            b = a + L
            if b > 23 or a in (23, 0): continue          # no entry in rollover
            mv = (piv[b] - piv[a]).dropna()
            if len(mv) < 500: continue
            by = mv.groupby(years.loc[mv.index]).mean(); m = mv.mean()
            cost = PIPS[sym] * max(HOUR_MULT[a], HOUR_MULT[min(b, 23)])
            r = dict(sym=sym, a=a, b=b, dir=int(np.sign(m)), is_mean=m, t=m / mv.std() * np.sqrt(len(mv)), cost=cost,
                     is_net=abs(m) - cost, same=int((np.sign(by) == np.sign(m)).sum()))
            for tag in ("OOS2018", "OOS2026"):
                if (sym, tag) in P and a in P[(sym, tag)] and b in P[(sym, tag)]:
                    q = (P[(sym, tag)][b] - P[(sym, tag)][a]).dropna() * np.sign(m)
                    r[tag] = q.mean() - cost
                else: r[tag] = np.nan
            rows.append(r)
R = pd.DataFrame(rows)
R.to_csv("season24_all.csv", index=False)
c = R[(R.same == 4) & (R.is_net > 0)].copy()
c["oos_ok"] = (c.OOS2018 > 0) & ((c.OOS2026 > 0) | c.OOS2026.isna())
pd.set_option("display.width", 220)
print(f"windows tested: {len(R)} | IS-consistent & net>0: {len(c)} | also OOS-positive: {c.oos_ok.sum()}")
print(c[c.oos_ok].sort_values("t", key=abs, ascending=False).round(2).to_string(index=False))

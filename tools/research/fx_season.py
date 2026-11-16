"""Intraday seasonality: mean move (pips) of each pair over every server-hour window, per year (IS),
then the best windows are checked out-of-sample (2018, 2026)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *

def hourly(sym, tag):
    m1 = load_m1(f"{DATA}/{sym}_{tag}.csv")
    t = pd.to_datetime(m1["time"], unit="s"); s = pd.Series(m1["close"], index=t)
    o = pd.Series(m1["open"], index=t)
    h_open = o.resample("1h").first().dropna()
    return h_open / pip(sym)

rows = []
for sym in FX:
    ho = hourly(sym, "IS")
    df = pd.DataFrame({"p": ho}); df["date"] = df.index.date; df["hour"] = df.index.hour; df["year"] = df.index.year; df["dow"] = df.index.dayofweek
    piv = df.pivot_table(index="date", columns="hour", values="p")
    years = pd.Series(pd.to_datetime(piv.index).year, index=piv.index)
    for a in range(1, 23):
        for L in (1, 2, 3, 4, 6):
            b = a + L
            if b > 23: continue
            mv = (piv[b] - piv[a]).dropna()
            if len(mv) < 500: continue
            by = mv.groupby(years.loc[mv.index]).mean()
            m = mv.mean(); cost = PIPS[sym] * HOUR_MULT[a]
            rows.append(dict(sym=sym, a=a, b=b, mean=m, t=m / mv.std() * np.sqrt(len(mv)), net=abs(m) - cost,
                             same_sign=int((np.sign(by) == np.sign(m)).sum()), y=" ".join(f"{v:+.1f}" for v in by.values)))
R = pd.DataFrame(rows)
cand = R[(R.same_sign == 4) & (R.net > 0)].sort_values("t", key=abs, ascending=False)
pd.set_option("display.width", 200)
print(f"{len(R)} windows tested; {len(cand)} with 4/4 years same sign AND |mean| > cost")
print(cand.head(25).to_string(index=False))
cand.to_csv("season_candidates.csv", index=False)
# out-of-sample check of the top candidates
print("\n== OOS check (pips, direction fixed from IS)")
for _, r in cand.head(25).iterrows():
    out = []
    for tag in ("OOS2018", "OOS2026"):
        try: ho = hourly(r.sym, tag)
        except FileNotFoundError: out.append(f"{tag}: n/a"); continue
        df = pd.DataFrame({"p": ho}); df["date"] = df.index.date; df["hour"] = df.index.hour
        piv = df.pivot_table(index="date", columns="hour", values="p")
        if r.a not in piv or r.b not in piv: out.append(f"{tag}: n/a"); continue
        mv = (piv[int(r.b)] - piv[int(r.a)]).dropna() * np.sign(r["mean"])
        cost = PIPS[r.sym] * HOUR_MULT[int(r.a)]
        out.append(f"{tag}: gross {mv.mean():+.2f} net {mv.mean() - cost:+.2f} (n={len(mv)})")
    print(f"{r.sym} {int(r.a):02d}h->{int(r.b):02d}h IS {r['mean']:+.2f} pips  | " + " | ".join(out))

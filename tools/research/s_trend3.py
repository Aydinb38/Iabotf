import sys; sys.path.insert(0, "/home/user/Iabotf/tools/research")
exec(open("/home/user/Iabotf/tools/research/s_trend2.py").read().split("rows = []")[0])
pd.set_option("display.width", 250)
def by_year(f, e, r):
    yrs = pd.to_datetime(f["m1"]["time"][e], unit="s").year
    return pd.Series(r).groupby(yrs).mean().round(3).to_dict()
print("== exits comparison (mode h1, entry rsi/pb, slm 2.5)")
for entry in ["rsi", "pb"]:
    for (rr, be, ts, td, lab) in [(3.0, 99, 99, 0, "TP3"), (3.0, 1.0, 99, 0, "TP3 BE1"), (6.0, 1.0, 1.0, 1.0, "trail1/1"), (6.0, 99, 1.5, 1.0, "trail1.5/1"), (10.0, 1.0, 2.0, 1.5, "trail2/1.5"), (2.0, 1.0, 99, 0, "TP2 BE1")]:
        allr = []; out = []
        for s in syms:
            L, S, sl = dip(F[s], "h1", entry, slm=2.5)
            e, d, r = run(F[s], s, L, S, sl, sl * rr, be_r=be, be_lock=0.05, tr_s=ts, tr_d=td, max_bars=1440 * 2)
            allr += list(r); st = stats(r); out.append(f"{s[:3]} e{st['expR']} {by_year(F[s], e, r)}" if s == "XAUUSD" else f"{s[:3]} e{st['expR']}")
        st = stats(allr)
        print(entry, lab, f"n={st['n']} win={st['win']} pf={st['pf']} e={st['expR']}", " | ".join(out))

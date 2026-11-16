import sys; sys.path.insert(0, "/home/user/Iabotf/tools/research")
src = open("/home/user/Iabotf/tools/research/s_trend2.py").read().split("rows = []")[0]
src = src.replace('F = {s: prep(s, "IS") for s in syms}', 'F = {}\nfor tag in ["IS", "OOS2018", "OOS2026"]:\n    for s in syms:\n        try: F[(s, tag)] = prep(s, tag)\n        except FileNotFoundError: pass')
src = src.replace("for s in syms:\n    f = F[s]", "for s in list(F):\n    f = F[s]")
exec(src)
CFG = [("trail TP10", 10.0, 1.0, 2.0, 1.5), ("tp3 BE1", 3.0, 1.0, 99, 0), ("TP4 BE1 trail2/1.5", 4.0, 1.0, 2.0, 1.5)]
for (lab, rr, be, ts, td) in CFG:
    print("==", lab)
    for key, f in F.items():
        s, tag = key
        u, d = trend(f, "h1"); sess = (f["hour"] >= 9) & (f["hour"] < 20)
        L = u & (f["rsi2"] < 10) & sess; S = d & (f["rsi2"] > 90) & sess
        sl = 3.0 * f["h1_atr"]
        e, dd, r = run(f, s, L, S, sl, sl * rr, be_r=be, be_lock=0.05, tr_s=ts, tr_d=td, max_bars=1440 * 2)
        st = stats(r); print(f"  {s} {tag:8s} n={st['n']:4d} win={st['win']} pf={st['pf']} e={st['expR']} totR={st['totR']} ddR={st['maxddR']}")

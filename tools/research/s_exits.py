import sys; sys.path.insert(0, "/home/user/Iabotf/tools/research")
exec(open("/home/user/Iabotf/tools/research/s_oos.py").read().split("CFG = ")[0].replace('syms = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]', 'syms = ["XAUUSD"]'))
for (lab, rr, be, lock, ts, td, pr, pf_) in [
    ("TP4 BE1 trail2/1.5", 4.0, 1.0, 0.05, 2.0, 1.5, 99, 0.0),
    ("TP4 BE1 lock.2 trail2/1.5", 4.0, 1.0, 0.2, 2.0, 1.5, 99, 0.0),
    ("TP4 BE.8 trail2/1.5", 4.0, 0.8, 0.1, 2.0, 1.5, 99, 0.0),
    ("TP4 partial50@1R BE trail", 4.0, 1.0, 0.05, 2.0, 1.5, 1.0, 0.5),
    ("TP3 partial50@1R BE", 3.0, 1.0, 0.05, 99, 0, 1.0, 0.5),
    ("TP2 partial50@1R BE", 2.0, 1.0, 0.05, 99, 0, 1.0, 0.5),
    ("TP1.5 BE.75", 1.5, 0.75, 0.1, 99, 0, 99, 0.0),
    ("TP1 noBE", 1.0, 99, 0, 99, 0, 99, 0.0)]:
    out = []
    for key, f in F.items():
        s, tag = key
        u, d = trend(f, "h1"); sess = (f["hour"] >= 9) & (f["hour"] < 20)
        L = u & (f["rsi2"] < 10) & sess; S = d & (f["rsi2"] > 90) & sess
        sl = 3.0 * f["h1_atr"]
        e, dd, r = run(f, s, L, S, sl, sl * rr, be_r=be, be_lock=lock, tr_s=ts, tr_d=td, max_bars=1440 * 2, partial_r=pr, partial_frac=pf_)
        st = stats(r); out.append(f"{tag}: n={st['n']} win={st['win']}% pf={st['pf']} e={st['expR']} dd={st['maxddR']}")
    print(f"{lab:28s}", " | ".join(out))

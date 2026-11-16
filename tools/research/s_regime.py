import sys; sys.path.insert(0, "/home/user/Iabotf/tools/research")
exec(open("/home/user/Iabotf/tools/research/s_oos.py").read().split("CFG = ")[0])
for adxmin in [0, 20, 25, 30]:
  for sepmin in [0.0, 1.0]:
    print("== ADX(H1) >=", adxmin, " EMA50-200 separation >= ATR(H1) x", sepmin)
    for key, f in F.items():
        s, tag = key
        if s not in ("XAUUSD", "EURUSD", "GBPUSD"): continue
        u, d = trend(f, "h1"); sess = (f["hour"] >= 9) & (f["hour"] < 20)
        reg = (f["h1_adx"] >= adxmin) & (np.abs(f["h1_e50"] - f["h1_e200"]) >= sepmin * f["h1_atr"])
        L = u & reg & (f["rsi2"] < 10) & sess; S = d & reg & (f["rsi2"] > 90) & sess
        sl = 3.0 * f["h1_atr"]
        e, dd, r = run(f, s, L, S, sl, sl * 4.0, be_r=1.0, be_lock=0.05, tr_s=2.0, tr_d=1.5, max_bars=1440 * 2)
        st = stats(r); print(f"  {s} {tag:8s} n={st['n']:4d} win={st['win']} pf={st['pf']} e={st['expR']} ddR={st['maxddR']}")

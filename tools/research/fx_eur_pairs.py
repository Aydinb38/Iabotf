import sys, os
sys.path.insert(0, os.path.dirname(__file__))
exec(open(os.path.join(os.path.dirname(__file__), "fx_eur_sim.py")).read().split("pd.set_option")[0])
for cm in [0.7, 1.0, 1.3]:
    print(f"== pullback 10h-13h, exit 15h, SL 3xATR(H1), TP 3R, BE 1R | cost x{cm}")
    for s, d in PAIRS.items():
        out = []
        for t in TAGS:
            if (s, t) not in F: continue
            f = F[(s, t)]; L, S = sig(f, d, "pullback", 10)
            sl = 3.0 * f["h1_atr"]
            r, e = run(f, L, S, sl, sl * 3.0, be_r=1.0, be_lock=0.1, exit_tod=15 * 60, cost_mult=cm)
            st = stats(r); out.append(f"{t}: n={st['n']} w={st['win']}% pf={st['pf']} e={st['expR']:+.3f}")
        print(f"  {s}: " + " | ".join(out))

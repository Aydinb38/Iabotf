"""Mise modulée (sans refuser de trade) sur les signaux v10 : multiplicateurs appris sur 2007-2018, jugés sur 2019-2025 et 2026."""
import v6lib as v, numpy as np, pandas as pd
from v10lib import *
HWB = {8: 1.5, 9: 1.0, 10: 0.9, 11: 1.0, 12: 0.6, 13: 0.4, 14: 0.2}
E7 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0)
D = {}
for src in ("MT5", "2026"):
    X, m1 = v.build_features(src)
    T = prepare(src, E7, rsi=65, bb=1.5, prev=6, volr=1.0)
    T["dow"] = X.dow.values[T.i]
    P = portfolio_guard(T, 10, 10, 900, 0, 0.0)
    # état des positions ouvertes au moment de l'entrée (R latent moyen), pour info
    st = P.entry_t.values; xt = P.exit_t.values; ep = P.ep.values; rr = P.rr.values; cp = P.curp.values
    avg = np.full(len(P), np.nan)
    for k in range(len(P)):
        m = (st < st[k]) & (xt > st[k]) & (P.day.values == P.day.values[k])
        if m.any(): avg[k] = np.mean((ep[m] - cp[k]) / rr[m])
    P["open_avg"] = avg
    P["w0"] = P.h.map(HWB).astype(float)
    D[src] = P
H = D["MT5"]; tr = H[H.year <= 2018]
def tiers(P, name):
    if name == "volr": return np.select([P.volr <= 0.8, P.volr <= 0.9], [0, 1], 2)
    if name == "dow": return P.dow.values.astype(int)
    if name == "bb": return np.select([P.bb > 2.2, P.bb > 1.8], [2, 1], 0)
    if name == "prev": return np.select([P.prev_rng >= 9, P.prev_rng >= 7.5], [2, 1], 0)
    if name == "rsi": return np.select([P.rsi3 > 85, P.rsi3 > 75], [2, 1], 0)
    if name == "open": return np.select([np.isnan(P.open_avg), P.open_avg < -0.3, P.open_avg < 0.0], [0, 1, 2], 3)
def learn(name):
    t = tiers(tr, name); g = pd.Series(tr.R.values).groupby(t).agg(["mean", "size"])
    ref = (tr.R.values).mean()
    mult = (g["mean"] / ref).clip(0.3, 1.7)        # proportionnel au gain moyen du palier
    # normalisation : poids moyen = 1 (même exposition moyenne)
    mult = mult / (mult * g["size"]).sum() * g["size"].sum()
    return mult.round(2).to_dict(), g
rows = []
def run(lab, names):
    mults = {n: learn(n)[0] for n in names}
    out = {}
    for src, P in D.items():
        w = P.w0.values.copy()
        for n in names:
            t = tiers(P, n); w = w * np.array([mults[n].get(x, 1.0) for x in t])
        Q = P.copy(); Q["w"] = w; out[src] = Q
    e = evaluate(out["MT5"], lab); Q = out["MT5"]
    e.update(Rtrain=round((Q[Q.year <= 2018].R * Q[Q.year <= 2018].w).sum()), Rtest=round((Q[Q.year >= 2019].R * Q[Q.year >= 2019].w).sum()),
             R26w=round((out["2026"].R * out["2026"].w).sum(), 1), mult=str(mults))
    rows.append(e)
for n in ["volr", "dow", "bb", "prev", "rsi", "open"]:
    m, g = learn(n); print(n, "| 2007-2018 :", {k: (round(a, 3), int(b)) for k, a, b in zip(g.index, g["mean"], g["size"])}, "-> multiplicateurs", m)
    te = H[H.year >= 2019]; gt = pd.Series(te.R.values).groupby(tiers(te, n)).mean().round(3).to_dict(); print("     2019-2025 gain moyen par palier :", gt)
run("v10 (heures seules)", [])
for n in ["volr", "dow", "bb", "prev", "rsi", "open"]: run("+ " + n, [n])
run("+ volr + dow", ["volr", "dow"])
R = pd.DataFrame(rows); pd.set_option("display.width", 260); pd.set_option("display.max_colwidth", 80)
print(R[["label", "n", "PFw", "sumRw", "Rtrain", "Rtest", "sharpe", "mois_pos", "neg_y", "risk_dd", "ret19y", "ret2019", "R26w"]].to_string(index=False))

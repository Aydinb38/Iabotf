"""Mise pondérée par la qualité : poids appris sur 2007-2018 (gain moyen par palier), testés sur 2019-2025 et 2026."""
import v6lib as v, numpy as np, pandas as pd, sys
from v9lib import *
exname = sys.argv[1] if len(sys.argv) > 1 else "E7"
EX = dict(E7=dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0), E8=dict(tpR=2.0, be_t=0.5, be_l=0.1, minp=0.05, slk=3.5))[exname]
T = broad("MT5", EX); T26 = broad("2026", EX)
def tiers(D):
    return dict(h=D.h.values,
                bb=np.select([D.bb > 1.5, D.bb > 1.0], [2, 1], 0),
                vol=np.select([D.volr <= 0.9, D.volr <= 1.0], [2, 1], 0),
                asia=np.where(D.asia8 >= 1.4, 1, 0),
                prev=np.where(D.prev_rng >= 6, 1, 0),
                rsi=np.where(D.rsi3 > 65, 1, 0))
def learn(D):
    """multiplicateur de chaque palier = gain moyen du palier / gain moyen du meilleur palier (borné 0..1)"""
    tz = tiers(D); W = {}
    for k, val in tz.items():
        g = pd.Series(D.R.values).groupby(val).mean()
        ref = g.max()
        W[k] = {i: float(np.clip(g[i] / ref, 0, 1)) if ref > 0 else 0.0 for i in g.index}
    return W
def weight(D, W, use):
    tz = tiers(D); w = np.ones(len(D))
    for k in use:
        w *= np.array([W[k].get(x, 0.0) for x in tz[k]])
    return w
train = T[T.year <= 2018]
W = learn(train)
print("multiplicateurs appris sur 2007-2018 :"); [print(" ", k, {i: round(x, 2) for i, x in val.items()}) for k, val in W.items()]
rows = []
def run_cfg(lab, use, mp, gap, wmin=0.15):
    out = {}
    for name, D in [("hist", T), ("2026", T26)]:
        D = D.copy(); D["w"] = weight(D, W, use) * 1.5   # échelle : le meilleur palier horaire vaut 1,5
        D = D[D.w >= wmin * 1.5]
        P = v.portfolio(D, mp, mp, gap)
        out[name] = P
    e = evaluate(out["hist"], lab); p26 = out["2026"]
    e.update(mp=mp, gap=gap // 60, R26w=round((p26.R * p26.w).sum(), 1), n26=len(p26))
    rows.append(e)
# références (filtres stricts + poids horaires v7)
for lab, cond in [("v7 (filtres stricts)", (T.rsi3 > 65) & (T.bb > 1.5) & (T.prev_rng >= 6) & (T.volr <= 1.0)),
                  ("v8 (filtres stricts)", (T.rsi3 > 65) & (T.bb > 1.5) & (T.prev_rng >= 6) & (T.volr <= 0.9) & (T.asia8 >= 1.4))]:
    for name, D, c in [("hist", T, cond), ("2026", T26, None)]:
        pass
    D = T[cond].copy(); D["w"] = D.h.map(HW); P = v.portfolio(D, 10, 10, 900)
    c26 = (T26.rsi3 > 65) & (T26.bb > 1.5) & (T26.prev_rng >= 6) & (T26.volr <= (1.0 if "v7" in lab else 0.9)) & ((T26.asia8 >= 1.4) if "v8" in lab else True)
    D26 = T26[c26].copy(); D26["w"] = D26.h.map(HW); P26 = v.portfolio(D26, 10, 10, 900)
    e = evaluate(P, lab); e.update(mp=10, gap=15, R26w=round((P26.R * P26.w).sum(), 1), n26=len(P26)); rows.append(e)
for use in [["h", "bb", "vol"], ["h", "bb", "vol", "asia"], ["h", "bb", "vol", "asia", "prev"], ["h", "bb", "vol", "asia", "prev", "rsi"]]:
    for mp, gap in [(10, 900), (15, 600), (20, 300)]:
        run_cfg("poids " + "+".join(use), use, mp, gap)
R = pd.DataFrame(rows); pd.set_option("display.width", 260)
print(R.drop(columns=["label"]).assign(cfg=R.label).to_string(index=False))
R.to_csv(f"v6_cache/tiers_{exname}.csv", index=False)

import v6lib as v, numpy as np, pandas as pd
X, m1 = v.build_features()
tb = X.time.values + 300; tod = (tb % 86400) // 60
wk = ((X.dow >= 1) & (X.dow <= 5)).values
m = wk & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) & (tod >= 8 * 60) & (tod < 14 * 60) & (X.rsi3.values > 65) & (X.prev_rng.values >= 6) & (X.volr.values <= 1.3)
T = v.run(X, m1, m, -1); P = v.portfolio(T, 6, 6, 1800)
F = X.iloc[P.i.values].reset_index(drop=True)
P = pd.concat([P, F.drop(columns=["time"]).add_prefix("f_")], axis=1)
P["per"] = np.select([P.time < 1356998400, P.time < 1546300800], [1, 2], 3)
P.to_pickle("v6_cache/P_base.pkl")
feats = [c for c in P.columns if c.startswith("f_") and c not in ("f_close", "f_m1_next", "f_next_gap", "f_cal_ok", "f_minute")]
rows = []
for c in feats:
    x = P[c]
    if x.nunique() <= 2:
        q = x.fillna(-1)
    else:
        try: q = pd.qcut(x.rank(method="first"), 5, labels=False)
        except Exception: continue
    g = P.groupby([q, "per"]).R.mean().unstack()
    n = P.groupby(q).size()
    # consistency: correlation of bucket with R in each period
    cons = [np.corrcoef(g.index.values.astype(float), g[p].values)[0, 1] if len(g) > 2 else np.sign(g[p].iloc[-1] - g[p].iloc[0]) for p in (1, 2, 3)]
    spread_ = (g.iloc[-1] - g.iloc[0]).values
    rows.append(dict(feat=c[2:], c1=round(cons[0], 2), c2=round(cons[1], 2), c3=round(cons[2], 2), d1=round(spread_[0], 3), d2=round(spread_[1], 3), d3=round(spread_[2], 3),
                     lo=" ".join(f"{a:+.3f}" for a in g.mean(axis=1).values)))
R = pd.DataFrame(rows); R["minabs"] = R[["c1", "c2", "c3"]].apply(lambda r: min(r.abs()) * (1 if (np.sign(r) == np.sign(r.iloc[0])).all() else 0), axis=1)
pd.set_option("display.width", 250); print(len(P), "trades")
print(R.sort_values("minabs", ascending=False).to_string(index=False))

"""v7 : EURUSD seul. Base = v6 sans la force des devises ; quelles caractéristiques EURUSD remplacent ce filtre ?"""
import v6lib as v, numpy as np, pandas as pd
X, m1 = v.build_features("MT5")
tb = X.time.values + 300; tod = (tb % 86400) // 60
wk = ((X.dow >= 2) & (X.dow <= 5)).values
m = wk & (X.day_fomc.values == 0) & (X.month_end.values == 0) & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values) \
    & (tod >= 480) & (tod < 900) & (X.rsi3.values > 65) & (X.prev_rng.values >= 6) & (X.volr.values <= 1.1)
EX = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=4.0)
T = v.run(X, m1, m, -1, **EX)
F = X.iloc[T.i.values].reset_index(drop=True)
T = pd.concat([T.reset_index(drop=True), F.drop(columns=["time"]).add_prefix("f_")], axis=1)
T.to_pickle("v6_cache/T_v7base.pkl")
P = v.portfolio(T, 10, 10, 900)
P["per"] = np.select([P.time < 1356998400, P.time < 1546300800], [1, 2], 3)
print(len(P), v.stats(P, 0.2))
feats = [c for c in P.columns if c.startswith("f_") and not c.startswith("f_s_") and c not in ("f_close", "f_m1_next", "f_next_gap", "f_cal_ok", "f_minute", "f_news_next", "f_news_prev", "f_news_today")]
rows = []
for c in feats:
    x = P[c]
    if x.nunique() <= 2: continue
    q = pd.qcut(x.rank(method="first"), 5, labels=False)
    g = P.groupby([q, "per"]).R.mean().unstack()
    cons = [np.corrcoef(g.index.values.astype(float), g[p].values)[0, 1] for p in (1, 2, 3)]
    sgn = np.sign(cons)
    rows.append(dict(feat=c[2:], c1=round(cons[0], 2), c2=round(cons[1], 2), c3=round(cons[2], 2), q=" ".join(f"{a:+.3f}" for a in g.mean(axis=1).values),
                     minabs=round(min(abs(np.array(cons))), 2) if (sgn == sgn[0]).all() else 0))
R = pd.DataFrame(rows).sort_values("minabs", ascending=False)
pd.set_option("display.width", 220); print(R.head(25).to_string(index=False))

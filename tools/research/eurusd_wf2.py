"""Do confident predictions cover costs? Conditional future move (pips) of top-confidence decisions, per year,
and ablation: which feature groups carry the signal."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
exec(open(os.path.join(os.path.dirname(__file__), "eurusd_wf.py")).read().split("res = []")[0])
GROUPS = {"all": FEATS, "time_only": ["hour", "minute", "dow"],
          "no_shortterm": [f for f in FEATS if f not in ("r5m", "r15m", "rsi3", "d_ema20", "m5vol")],
          "shortterm_only": ["r5m", "r15m", "rsi3", "d_ema20", "m5vol"]}
H = "y1h"; out = []
for gname, feats in GROUPS.items():
    rows = []
    for test_y in range(2008, 2019):
        tr = X[(X.year >= test_y - 3) & (X.year < test_y)].dropna(subset=[H]).iloc[::3]
        te = X[X.year == test_y].dropna(subset=[H])
        g = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200, l2_regularization=1.0, min_samples_leaf=200)
        g.fit(tr[feats], (tr[H] > 0).astype(int)); p = g.predict_proba(te[feats])[:, 1]
        pips = te[H].values * te.atr_h1.values / 0.0001
        conf = np.abs(p - 0.5); d = np.sign(p - 0.5)
        r = dict(year=test_y, auc=roc_auc_score((te[H] > 0).astype(int), p))
        for q in (0.9, 0.97):
            m = conf >= np.quantile(conf, q)
            r[f"pips_top{round((1-q)*100)}"] = (d[m] * pips[m]).mean()
        rows.append(r)
    R = pd.DataFrame(rows)
    print(f"[{gname}] AUC mean {R.auc.mean():.3f} | gross pips/decision top10% by year {R.pips_top10.round(1).tolist()} mean {R.pips_top10.mean():.2f} | top3% mean {R.pips_top3.mean():.2f}")

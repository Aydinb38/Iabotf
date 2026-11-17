import sys, os
sys.path.insert(0, os.path.dirname(__file__))
exec(open("fx_ai.py").read().split("IS = D[D.tag")[0])
from sklearn.ensemble import HistGradientBoostingClassifier
IS = D[D.tag == "IS"]
for depth in (2, 3):
    aucs = []
    for y in sorted(IS.year.unique()):
        tr, te = IS[IS.year != y], IS[IS.year == y]
        m = HistGradientBoostingClassifier(max_depth=depth, learning_rate=0.05, max_iter=150, l2_regularization=1.0).fit(tr[FEATS], tr.win)
        aucs.append(roc_auc_score(te.win, m.predict_proba(te[FEATS])[:, 1]))
    m = HistGradientBoostingClassifier(max_depth=depth, learning_rate=0.05, max_iter=150, l2_regularization=1.0).fit(IS[FEATS], IS.win)
    oos = {t: round(roc_auc_score(D[D.tag == t].win, m.predict_proba(D[D.tag == t][FEATS])[:, 1]), 3) for t in ("OOS2018", "OOS2026")}
    print(f"GBM depth {depth}: IS leave-one-year-out AUC {[round(a,3) for a in aucs]} | OOS AUC {oos}")

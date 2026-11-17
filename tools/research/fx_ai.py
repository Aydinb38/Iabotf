"""AI trade-quality filter for the European-session system.
Builds one row per executed trade (features known at entry), trains a regularised logistic
regression on 2014-2017 only (with leave-one-year-out validation) and measures out-of-sample
(2018, 2026) whether filtering by score raises win rate and expectancy."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from fxlib import *
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
PAIRS = ["EURUSD", "GBPUSD"]; TAGS = ["IS", "OOS2018", "OOS2026"]

def features(f):
    m5 = f["m5"]; c = m5["close"]; o = m5["open"]; t = m5["time"]; day = t // 86400; tod = t % 86400
    m1 = f["m1"]; b = resample(m1, 86400); hi = htf_index(t, 300, b["time"], 86400); ok = hi >= 0; hi2 = np.where(ok, hi, 0)
    d1c = b["close"]; d1o = b["open"]
    d1_atr = np.where(ok, atr(b["high"], b["low"], d1c, 14)[hi2], np.nan)
    d1_e20 = np.where(ok, ema(d1c, 20)[hi2], np.nan)
    prev_ret = np.where(ok, (d1c - d1o)[hi2], np.nan)
    h1 = f["h1"]; hidx = htf_index(t, 300, h1["time"], 3600); okh = hidx >= 0; h2 = np.where(okh, hidx, 0)
    atr_long = np.where(okh, atr(h1["high"], h1["low"], h1["close"], 240)[h2], np.nan)
    s = pd.DataFrame({"day": day, "tod": tod, "o": o, "c": c, "h": m5["high"], "l": m5["low"]})
    day_open = s.groupby("day").o.transform("first").values
    p9 = s.o.where(s.tod == 9 * 3600).groupby(s.day).transform("max").values          # price at 09:00
    asia = s[(s.tod >= 3600) & (s.tod < 9 * 3600)].groupby("day").agg(ah=("h", "max"), al=("l", "min"))
    ah = pd.Series(day).map(asia.ah).values; al = pd.Series(day).map(asia.al).values
    X = dict(
        rsi3=f["rsi3"], rsi14=f["rsi14"],
        sess_move=(c - p9) / f["h1_atr"], day_move=(c - day_open) / f["h1_atr"],
        trend_h1=(f["h1_e50"] - f["h1_e200"]) / f["h1_atr"], trend_d1=(c - d1_e20) / d1_atr,
        vol_ratio=f["h1_atr"] / atr_long, prev_day=prev_ret / d1_atr,
        hour=(tod + 300) / 3600.0, dow=f["dow"].astype(float),
        asia_pos=(c - al) / np.maximum(ah - al, 1e-9), local_vol=f["atr"] / f["h1_atr"])
    return X

def trades(sym, tag):
    f = prep(sym, tag); X = features(f)
    tod = f["m5"]["time"] % 86400; wk = (f["dow"] >= 1) & (f["dow"] <= 5)
    S = wk & (tod >= 10 * 3600 - 300) & (tod < 13 * 3600 - 300) & (f["rsi3"] > 70); L = np.zeros_like(S)
    sl = 3 * f["h1_atr"]
    idx = np.flatnonzero(S); idx = idx[idx + 1 < len(f["m5"]["time"])]
    r, e = run(f, L, S, sl, 3 * sl, be_r=1.0, be_lock=0.1, exit_tod=15 * 60)
    ent_to_idx = {int(f["m5"]["m1_start"][i + 1]): i for i in idx}
    rows = []
    for rr, ee in zip(r, e):
        i = ent_to_idx[int(ee)]
        d = -1.0   # all trades are sells (EUR/GBP weakness)
        row = {k: v[i] for k, v in X.items()}
        for k in ("sess_move", "day_move", "trend_h1", "trend_d1", "prev_day"): row[k] *= d
        row["asia_pos"] = 1 - row["asia_pos"] if d < 0 else row["asia_pos"]
        row.update(sym=sym, tag=tag, year=pd.to_datetime(f["m1"]["time"][ee], unit="s").year, R=rr)
        rows.append(row)
    return pd.DataFrame(rows)

D = pd.concat([trades(s, t) for s in PAIRS for t in TAGS if os.path.exists(f"{DATA}/{s}_{t}.csv")], ignore_index=True)
FEATS = ["rsi3", "rsi14", "sess_move", "day_move", "trend_h1", "trend_d1", "vol_ratio", "prev_day", "hour", "dow", "asia_pos", "local_vol"]
D = D.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATS)
D["win"] = (D.R > 0).astype(int)
IS = D[D.tag == "IS"]
mu, sd = IS[FEATS].mean(), IS[FEATS].std()
Z = lambda df: ((df[FEATS] - mu) / sd).clip(-4, 4).values
# leave-one-year-out inside IS
aucs = []; cv_scores = pd.Series(index=IS.index, dtype=float)
for y in sorted(IS.year.unique()):
    tr, te = IS[IS.year != y], IS[IS.year == y]
    m = LogisticRegression(C=0.1, max_iter=2000).fit(Z(tr), tr.win)
    p = m.predict_proba(Z(te))[:, 1]; cv_scores.loc[te.index] = p; aucs.append(roc_auc_score(te.win, p))
print("IS leave-one-year-out AUC per year:", [round(a, 3) for a in aucs])
model = LogisticRegression(C=0.1, max_iter=2000).fit(Z(IS), IS.win)
print("coefficients:", dict(zip(FEATS, model.coef_[0].round(3))), "intercept", round(model.intercept_[0], 3))
D["p"] = model.predict_proba(Z(D))[:, 1]
D.loc[IS.index, "p"] = cv_scores           # honest IS scores (out-of-fold)
def summary(x):
    if len(x) == 0: return "n=0"
    w = x.R[x.R > 0].sum(); l = -x.R[x.R < 0].sum()
    return f"n={len(x)} win={x.win.mean()*100:.1f}% pf={w/l:.2f} e={x.R.mean():+.3f}"
for q in [0.0, 0.3, 0.5, 0.7]:
    thr = IS.assign(p=cv_scores).p.quantile(q)
    print(f"keep score >= IS quantile {q:.1f} (thr {thr:.3f})")
    for tag in TAGS:
        x = D[D.tag == tag]
        print(f"   {tag:8s} all: {summary(x)}  |  kept: {summary(x[x.p >= thr])}  | AUC {roc_auc_score(x.win, x.p):.3f}")
json.dump(dict(feats=FEATS, mu=mu.round(6).tolist(), sd=sd.round(6).tolist(), coef=model.coef_[0].round(6).tolist(),
               intercept=float(model.intercept_[0])), open("fx_ai_model.json", "w"), indent=1)

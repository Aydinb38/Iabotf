"""v9 : jeu de signaux large + caractéristiques, pour tester une mise pondérée par la qualité du signal."""
import v6lib as v, numpy as np, pandas as pd
HW = {8: 1.5, 9: 1.5, 10: 1.5, 11: 1.0, 12: 1.0, 13: 0.5, 14: 0.5}
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)

def asia8(X):
    t = X.time.values; day = t // 86400; tt = t % 86400
    sub = pd.DataFrame({"day": day, "c": X.close.values})[(tt >= 3600) & (tt < 8 * 3600)].groupby("day").c.agg(["max", "min"])
    return np.where(tt >= 8 * 3600 - 300, pd.Series(day).map(sub["max"] - sub["min"]).values / X.atr.values, np.nan)

def broad(src, ex, rsi=60, bb=0.5, prev=5.0, volr=1.2, h0=8, h1=15):
    X, m1 = v.build_features(src); tod = ((X.time.values + 300) % 86400) // 60
    X["asia8"] = asia8(X)
    wk = ((X.dow >= 2) & (X.dow <= 5)).values
    m = (wk & (X.day_fomc.values == 0) & (X.month_end.values == 0) & (X.spread.values <= 20) & (X.spread.values * 1e-5 <= 0.3 * X.atr.values)
         & (tod >= h0 * 60) & (tod < h1 * 60) & (X.rsi3.values > rsi) & (X.bb.values > bb) & (X.prev_rng.values >= prev) & (X.volr.values <= volr))
    T = v.run(X, m1, m, -1, **ex)
    for c in ["rsi3", "bb", "prev_rng", "volr", "asia8", "d_ema50"]: T[c] = X[c].values[T.i]
    T["h"] = tod[T.i] // 60
    return T

def equity_w(P, risk):
    """capitalisation : chaque trade risque risk% x poids"""
    Q = P.sort_values("exit_t"); r = Q.R.values * Q.w.values
    eq = np.cumprod(1 + r * risk / 100.0); peak = np.maximum.accumulate(np.r_[1.0, eq])[1:]
    return eq, (1 - eq / peak).max() * 100

def evaluate(P, label="", target_dd=15.0, risk=None):
    """P : trades retenus avec colonnes R (non pondéré) et w (poids). Gain à drawdown égal + régularité."""
    lo, hi = 0.01, 5.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if equity_w(P, mid)[1] > target_dd: hi = mid
        else: lo = mid
    eq, dd = equity_w(P, lo)
    U = P[P.year >= 2019]; equ, ddu = equity_w(U, lo)
    rw = P.R * P.w; p = per(P.time.values)
    daily = rw.groupby(P.day).sum(); mo = rw.groupby(pd.to_datetime(P.time, unit="s").dt.to_period("M")).sum()
    yrs = rw.groupby(P.year).sum()
    out = dict(label=label, n=len(P), win=round((P.R > 0).mean() * 100, 1), PFw=round(rw[rw > 0].sum() / -rw[rw < 0].sum(), 3),
               sumRw=round(rw.sum()), R1=round(rw[p == 1].sum()), R2=round(rw[p == 2].sum()), R3=round(rw[p == 3].sum()),
               sharpe=round(daily.mean() / daily.std() * np.sqrt(252), 2), mois_pos=round((mo > 0).mean() * 100, 1), neg_y=int((yrs < 0).sum()),
               risk_dd=round(lo, 3), ret19y=round((eq[-1] - 1) * 100), ret2019=round((equ[-1] - 1) * 100))
    if risk is not None:
        e2, d2 = equity_w(P, risk); out.update(ret_at=round((e2[-1] - 1) * 100), dd_at=round(d2, 1))
    return out

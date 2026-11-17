"""Trade-level walk-forward simulation of the logistic-regression AI on EURUSD.
Model retrained every month on the previous `train_months` months (as the EA will do), decisions on every
M5 close, trade when |p-0.5| >= threshold (threshold = quantile of in-sample confidence), one position at a time,
SL = k*ATR(H1), TP = m*ATR(H1) or time exit after `hold` minutes. Costs = 1.0 pip x hour multiplier."""
import os, sys, itertools
sys.path.insert(0, os.path.dirname(__file__))
exec(open(os.path.join(os.path.dirname(__file__), "eurusd_wf.py")).read().split("res = []")[0])
from fxlib import sim, HOUR_MULT
m1 = load_m1(f"{DATA}/EURUSD_ALL.csv")
X = X.reset_index(drop=True)
X["month"] = pd.to_datetime(X.time, unit="s").dt.to_period("M")
months = sorted(X.month.unique())
NUM = [f for f in FEATS if f != "hour"]
def design(d, mu, sd):
    z = ((d[NUM] - mu) / sd).fillna(0).clip(-5, 5).values
    oh = np.zeros((len(d), 24)); oh[np.arange(len(d)), d.hour.astype(int).values] = 1
    return np.hstack([z, oh])
def walk(H="y1h", train_months=36, C=0.05):
    P = np.full(len(X), np.nan); TH = np.full(len(X), np.nan)
    start = months.index(pd.Period("2008-01", "M"))
    for i in range(start, len(months)):
        tr = X[(X.month >= months[i - train_months]) & (X.month < months[i])].dropna(subset=[H]).iloc[::3]
        te_idx = X.index[X.month == months[i]]
        mu, sd = tr[NUM].mean(), tr[NUM].std()
        lr = LogisticRegression(C=C, max_iter=300).fit(design(tr, mu, sd), (tr[H] > 0).astype(int))
        p_tr = lr.predict_proba(design(tr, mu, sd))[:, 1]
        P[te_idx] = lr.predict_proba(design(X.loc[te_idx], mu, sd))[:, 1]
        TH[te_idx] = np.quantile(np.abs(p_tr - 0.5), 0.90)    # placeholder; real threshold chosen below via quantile q
        X.loc[te_idx, "conf_q90"] = np.quantile(np.abs(p_tr - 0.5), 0.90)
        X.loc[te_idx, "conf_q95"] = np.quantile(np.abs(p_tr - 0.5), 0.95)
        X.loc[te_idx, "conf_q80"] = np.quantile(np.abs(p_tr - 0.5), 0.80)
    X["p"] = P
    return X

def trade(Xp, q="conf_q90", hold=60, slk=1.5, tpk=99.0, be=99.0, cost_pips=1.0, years=None):
    d = Xp.dropna(subset=["p", q])
    if years is not None: d = d[d.year.isin(years)]
    conf = (d.p - 0.5).abs(); m = conf >= d[q]
    d = d[m & (d.hour >= 1) & (d.hour <= 22) & d.dow.between(1, 5)]
    dirs = np.where(d.p > 0.5, 1, -1).astype(np.int64)
    ent = d.m1_next.values.astype(np.int64)
    A = d.atr_h1.values
    cost = cost_pips * 0.0001 * HOUR_MULT[((d.hour.values + (d.minute.values + 5 >= 60)) % 24).astype(int)]
    r, e = sim(m1["open"], m1["high"], m1["low"], m1["time"], ent, dirs, slk * A, tpk * A, cost, be, 0.1, 99.0, 0.0, -1, hold)
    pips = r * slk * np.interp(e, ent, A) / 0.0001
    yrs = pd.to_datetime(m1["time"][e], unit="s").year
    return r, pips, yrs, e

if __name__ == "__main__":
    for tm in (12, 36):
        Xp = walk("y1h", train_months=tm)
        print(f"=== train window {tm} months (monthly retrain), horizon 1h")
        for q in ("conf_q80", "conf_q90", "conf_q95"):
            for slk, tpk, be in [(1.5, 99, 99), (1.5, 0.75, 99), (1.0, 0.5, 99), (2.0, 0.5, 99)]:
                r, pips, yrs, e = trade(Xp, q=q, hold=60, slk=slk, tpk=tpk, be=be)
                by = pd.Series(pips).groupby(yrs).sum()
                ndays = len(np.unique(m1["time"][e] // 86400))
                print(f" {q} SL{slk} TP{tpk}: n={len(r)} ({len(r)/ndays:.1f}/j) win={np.mean(r>0)*100:.1f}% pf={r[r>0].sum()/-r[r<0].sum():.2f} "
                      f"pips/trade={pips.mean():+.2f} | net pips/yr {by.round(0).astype(int).tolist()}")

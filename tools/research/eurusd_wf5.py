import os, sys
sys.path.insert(0, os.path.dirname(__file__))
src = open(os.path.join(os.path.dirname(__file__), "eurusd_wf3.py")).read().split('if __name__ == "__main__":')[0]
exec(src)
for tm in (12, 24, 36):
    Xp = walk("y2h", train_months=tm)
    d = Xp.copy(); d.loc[~d.hour.between(9, 18), "p"] = np.nan
    r, pips, yrs, e = trade(d, q="conf_q95", hold=120, slk=1.5, tpk=99, cost_pips=1.0)
    by = pd.Series(pips).groupby(yrs).sum()
    hrs = ((m1["time"][e] % 86400) // 3600)
    # direction of executed trades: recover from entry index
    ent_dir = dict(zip(d.dropna(subset=["p"]).m1_next.values.astype(int), np.where(d.dropna(subset=["p"]).p > 0.5, 1, -1)))
    dirs = np.array([ent_dir.get(int(x), 0) for x in e])
    outside = (hrs < 10) | (hrs >= 15)
    print(f"train {tm}m: n={len(r)} pf={r[r>0].sum()/-r[r<0].sum():.2f} pips/trade={pips.mean():+.2f} years+ {(by>0).sum()}/{len(by)} {by.round(0).astype(int).tolist()}")
    print(f"     longs {np.mean(dirs>0)*100:.0f}% | trades hors 10h-15h: n={outside.sum()} pips/trade={pips[outside].mean():+.2f} pf={r[outside][r[outside]>0].sum()/-r[outside][r[outside]<0].sum():.2f} | dans 10h-15h: pips/trade={pips[~outside].mean():+.2f}")

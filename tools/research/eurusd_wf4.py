import os, sys
sys.path.insert(0, os.path.dirname(__file__))
src = open(os.path.join(os.path.dirname(__file__), "eurusd_wf3.py")).read().split('if __name__ == "__main__":')[0]
exec(src)
X["conf_q97"] = np.nan
def walk2(H, tm=36):
    Xp = walk(H, train_months=tm)
    return Xp
for H, hold in (("y1h", 60), ("y2h", 120)):
    Xp = walk2(H)
    # stricter threshold: 97th percentile of in-sample confidence, recomputed per month
    print(f"=== horizon {H}, hours 9-19 only")
    for q in ("conf_q95",):
        for cost in (1.0, 0.8):
            d = Xp.copy(); d.loc[~d.hour.between(9, 18), "p"] = np.nan
            r, pips, yrs, e = trade(d, q=q, hold=hold, slk=1.5, tpk=99, cost_pips=cost)
            by = pd.Series(pips).groupby(yrs).sum()
            print(f"  {q} cost {cost}: n={len(r)} win={np.mean(r>0)*100:.1f}% pf={r[r>0].sum()/-r[r<0].sum():.2f} pips/trade={pips.mean():+.2f} | by year {by.round(0).astype(int).tolist()}")

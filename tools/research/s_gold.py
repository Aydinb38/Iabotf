import sys; sys.path.insert(0, "/home/user/Iabotf/tools/research")
exec(open("/home/user/Iabotf/tools/research/s_trend2.py").read().split("rows = []")[0].replace('syms = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]', 'syms = ["XAUUSD"]'))
pd.set_option("display.width", 250)
f = F["XAUUSD"]
def by_year(e, r):
    yrs = pd.to_datetime(f["m1"]["time"][e], unit="s").year
    return pd.Series(r).groupby(yrs).mean().round(3).to_dict()
rows = []
for mode in ["h1", "h1h4", "h1d1"]:
  for rsix in [5, 10, 20]:
    for (h0, h1_) in [(9, 20), (8, 22), (14, 20), (3, 22)]:
      for slm in [1.5, 2.0, 2.5, 3.0]:
        for (rr, be, ts, td) in [(10.0, 1.0, 2.0, 1.5), (3.0, 1.0, 99, 0)]:
            u, d = trend(f, mode); sess = (f["hour"] >= h0) & (f["hour"] < h1_)
            L = u & (f["rsi2"] < rsix) & sess; S = d & (f["rsi2"] > 100 - rsix) & sess
            sl = slm * f["h1_atr"]
            e, dd, r = run(f, "XAUUSD", L, S, sl, sl * rr, be_r=be, be_lock=0.05, tr_s=ts, tr_d=td, max_bars=1440 * 2)
            st = stats(r); y = by_year(e, r)
            rows.append(dict(mode=mode, rsix=rsix, sess=f"{h0}-{h1_}", slm=slm, exit="trail" if ts < 50 else "tp3", n=st["n"], win=st["win"], pf=st["pf"], e=st["expR"], ddR=st["maxddR"], ymin=min(y.values()), **{str(k): v for k, v in y.items()}))
df = pd.DataFrame(rows)
print("fraction of configs with positive expectancy:", (df.e > 0).mean().round(3), " all-years-positive:", (df.ymin > 0).mean().round(3))
print(df.groupby("mode").e.mean().round(3).to_dict(), df.groupby("rsix").e.mean().round(3).to_dict(), df.groupby("sess").e.mean().round(3).to_dict(), df.groupby("slm").e.mean().round(3).to_dict(), df.groupby("exit").e.mean().round(3).to_dict())
print(df.sort_values("e", ascending=False).head(25).to_string(index=False))
df.to_csv("gold_grid.csv", index=False)

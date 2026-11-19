import v6lib as v, numpy as np, pandas as pd
exec(open("v6_base.py").read().split("T = v.run")[0])
E = pd.read_csv("/tmp/claude-0/-home-user-Iabotf/7b3b2ecf-5bfa-5d65-b21b-3a2940c98cd5/scratchpad/runs_v5f/mt5.csv")
E["entry_t"] = (pd.to_datetime(E.open_time, format="%Y.%m.%d %H:%M:%S") - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)
E["year"] = E.open_time.str[:4].astype(int)
T = v.run(X, m1, v5mask(), -1); P = v.portfolio(T, 2, 2, 3600)
M = E.merge(P, on="entry_t", how="outer", suffixes=("_emu", "_sim"), indicator=True)
print(M._merge.value_counts())
B = M[M._merge == "both"].copy(); B["diff"] = B.R_sim - B.R_emu
print("both: emu sumR", B.R_emu.sum().round(1), "sim", B.R_sim.sum().round(1))
print(B.groupby("year_emu")[["R_emu", "R_sim"]].sum().round(1).T.to_string())
B["exit_emu"] = B.exit
print(B[B["diff"].abs() > 0.3][["open_time", "close_time", "exit", "R_emu", "R_sim", "exit_t"]].head(20).assign(exit_sim=lambda d: pd.to_datetime(d.exit_t, unit="s")).to_string())
print((B["diff"].abs() > 0.3).sum(), "big diffs of", len(B))
print(M[M._merge == "right_only"].year_sim.value_counts().sort_index().to_dict())
print(M[M._merge == "left_only"].year_emu.value_counts().sort_index().to_dict())

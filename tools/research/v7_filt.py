import v6lib as v, numpy as np, pandas as pd
T = pd.read_pickle("v6_cache/T_v7base.pkl")
per = lambda t: np.select([t < 1356998400, t < 1546300800], [1, 2], 3)
def ev(mask, lab, mp=10, gap=900):
    P = v.portfolio(T[mask], mp, mp, gap); p = per(P.time.values); y = P.groupby("year").R.sum()
    r = v.norm(P, 15.0, lab); s = v.stats(P, 0.2)
    r.update(exp=s["exp"], R1=round(P.R[p == 1].sum()), R2=round(P.R[p == 2].sum()), R3=round(P.R[p == 3].sum()), neg=int((y < 0).sum()), worst=round(y.min()))
    return r
one = np.ones(len(T), bool)
rows = [ev(one, "base (v6 sans force devises)")]
for th in [0.0, 0.5, 1.0, 1.5]: rows.append(ev(T.f_bb > th, f"bb>{th}"))
for th in [0.0, 0.25, 0.5, 0.75]: rows.append(ev(T.f_d_ema50 > th, f"d_ema50>{th}"))
for th in [55, 60, 65]: rows.append(ev(T.f_rsi7 > th, f"rsi7>{th}"))
for th in [1.0, 0.9]: rows.append(ev(T.f_volr <= th, f"volr<={th}"))
rows.append(ev((T.f_bb > 1.0) & (T.f_d_ema50 > 0.25), "bb>1 & ema50>0.25"))
rows.append(ev((T.f_bb > 0.5) & (T.f_d_ema50 > 0.25), "bb>0.5 & ema50>0.25"))
rows.append(ev((T.f_d_ema50 > 0.25) & (T.f_volr <= 1.0), "ema50>0.25 & volr<=1"))
rows.append(ev((T.f_bb > 1.0) & (T.f_volr <= 1.0), "bb>1 & volr<=1"))
pd.set_option("display.width", 250); print(pd.DataFrame(rows).to_string(index=False))

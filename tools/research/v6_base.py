import v6lib as v, numpy as np, pandas as pd
X, m1 = v.build_features()
tb = X.time.values + 300  # entry time (next bar open)
tod = (tb % 86400) // 60
wk = (X.dow >= 1) & (X.dow <= 5)
def v5mask(h0=11, h1=14, rsi=65, prev=6.0, volr=1.1):
    return (wk & (tod >= h0 * 60) & (tod < h1 * 60) & (X.rsi3 > rsi) & (X.prev_rng >= prev) & (X.volr <= volr)
            & (X.spread <= 20) & (X.spread * 1e-5 <= 0.1 * 3 * X.atr)).values
T = v.run(X, m1, v5mask(), -1)
P = v.portfolio(T, 2, 2, 3600)
print(v.stats(P, label="v5 replica"))
print(v.yearly(P).T.to_string())
P4 = v.portfolio(v.run(X, m1, v5mask(10, 14, prev=6.0, volr=99), -1), 3, 3, 3600)
print(v.stats(P4, label="v4-like 10-14 3pos no volr"))

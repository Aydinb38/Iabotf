"""Le simulateur reproduit-il l'émulateur ? v7 (0,25 %) et v8 (0,3 %) à risque fixe."""
import v6lib as v, numpy as np, pandas as pd
from v9lib import *
E7 = dict(tpR=2.0, be_t=0.7, be_l=0.1, minp=0.05, slk=3.0); E8 = dict(tpR=2.0, be_t=0.5, be_l=0.1, minp=0.05, slk=3.5)
T7 = broad("MT5", E7, rsi=65, bb=1.5, prev=6, volr=1.0); T7["w"] = T7.h.map(HW)
P7 = v.portfolio(T7, 10, 10, 900); P7["w"] = P7.h.map(HW) if "h" in P7 else 1
T8 = broad("MT5", E8, rsi=65, bb=1.5, prev=6, volr=0.9); T8 = T8[T8.asia8 >= 1.4]
P8 = v.portfolio(T8, 10, 10, 900); P8["w"] = P8.h.map(HW)
print(evaluate(P7, "v7", risk=0.25)); print(evaluate(P8, "v8", risk=0.30))

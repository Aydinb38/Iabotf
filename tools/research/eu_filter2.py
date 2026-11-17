import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from eu_lib import *
D = load("ALL").replace([np.inf, -np.inf], np.nan)
print("prev_rng quantiles:", D.prev_rng.quantile([0.2, 0.4, 0.5, 0.6, 0.8]).round(2).to_dict())
pd.set_option("display.width", 220)
rows = []
for thr in [0, 4.0, 5.0, 6.0, 7.0]:
    for rsix in [70, 65]:
        m = (D.rsi3_sig > rsix) & ((D.prev_rng >= thr) if thr > 0 else True)
        x = select(D, m)
        for ex in ["E0_return", "E1_winrate", "E7_be1_hold17", "E3_be05_hold17", "E2_be03"]:
            rows.append(dict(prev_rng_min=thr, rsi=rsix, exit=ex, **stats(x, ex)))
R = pd.DataFrame(rows)
print(R.sort_values(["exit", "prev_rng_min"]).to_string(index=False))

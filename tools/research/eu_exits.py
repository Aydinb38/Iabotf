import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from eu_lib import *
from eu_cand import EXITS
D = load("ALL")
base = select(D, D.rsi3_sig > 70)
pd.set_option("display.width", 200)
rows = [dict(exit=k, **stats(base, k)) for k in EXITS]
print(pd.DataFrame(rows).to_string(index=False))

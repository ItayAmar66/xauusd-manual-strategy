#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd
import numpy as np
P=Path(__file__).resolve().parent
s=json.loads((P/'summary.json').read_text())
ml=json.loads((P/'ml_summary.json').read_text())
f=pd.read_csv(P/'daily_1755_structural_fallback_trades.csv')
o=pd.read_csv(P/'hindsight_oracle_NOT_TRADABLE.csv')
p=pd.read_csv(P/'all_480_causal_policy_trials.csv')
c=pd.read_csv(P/'coverage_expectancy_frontier.csv')
m=pd.read_csv(P/'ml_period_results.csv')
mg=pd.read_csv(P/'ml_threshold_grid.csv')
assert len(f)==446 and f.day.nunique()==446
assert s['policy_count']==480 and len(p)==480
assert f.net_R.notna().all() and (f.stop_distance>0).all()
assert (f.duration_min<=120).all()
assert o.any_3R_candidate.all(), 'All full eligible days should have at least one ex-post 3R candidate in this dataset'
assert (p.filter(like='coverage_pct')>=99.999).all().all()
assert len(m)==16 and len(mg)==48
assert ml['n_training_trades']>5000
for strg in ['2025H2_ONLY_SELECTED','ALL_FIRST_SIGNAL_1_A_DAY','FALLBACK_ONLY_1755']:
    assert len(c[c.policy==strg])==4
assert c[(c.policy=='2025H2_ONLY_SELECTED') & (c.period=='2026Q2Q3_REUSED')].mean_R.iloc[0]<0
assert c[(c.policy=='2025H2_ONLY_SELECTED') & (c.period=='2026Q2Q3_REUSED')].coverage_pct.iloc[0]==100
assert m[(m.selection=='2025H2_selected')&(m.period=='2026Q2Q3_REUSED')].mean_R.max()<1
print('PASS: 446 active-price sessions, 480 policies, full-time-bounded rescue, two trained ML models; no verified +1R portfolio')
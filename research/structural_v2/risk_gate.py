#!/usr/bin/env python3
"""Stop DISTANCE viability gate, not fixed stop: every SL remains market-structure anchored.
2025-only gate selection, chronological 2026 check. Prevents cherry-picked late-period filters.
"""
from pathlib import Path
import portfolio_test as p
import pandas as pd,numpy as np,json
OUT=Path(__file__).resolve().parent
D=np.array(p.market.index,dtype='str')
periods=p.periods
reports=[]
for minrisk in (.65,1.,1.5,2.5,4.,6.,8.):
 for maxrisk in (15.,30.,150.):
  result=p.stream(p.all_.entry_m1.to_numpy(np.int64),p.all_.signal_m1.to_numpy(np.int64),p.all_.side.to_numpy(np.int8),p.all_.stop.to_numpy(float),p.all_.reference.to_numpy(float),p.all_['mode'].to_numpy(int),p.all_.rr.to_numpy(int),p.all_.mgmt.to_numpy(int),p.all_.priority.to_numpy(int),p.o,p.h,p.l,p.c,p.t,p.allowed,minrisk,maxrisk)
  if not len(result):continue
  entry_idx=result[:,1].astype(np.int64)
  dates=np.array(p.loc.date,dtype='str')[entry_idx]
  for label,lo,hi in periods:
   mask=(dates>=lo)&(dates<hi)
   out=result[mask]; v=out[:,9];n=len(out)
   market_days=int(np.sum((D>=lo)&(D<hi)))
   coverage=len(np.unique(dates[mask]))/max(1,market_days)*100
   reports.append(dict(min_structural_risk=minrisk,max_structural_risk=maxrisk,period=label,trades=n,covered_days=len(np.unique(dates[mask])),market_days=market_days,coverage_pct=coverage,avg_net_R=float(v.mean()) if n else np.nan,total_net_R=float(v.sum()),avg_R_stress_cost070=float((v-.35/out[:,8]).mean()) if n else np.nan))
 print('gate',minrisk,'done',flush=True)
r=pd.DataFrame(reports)
r.to_csv(OUT/'structural_stop_viability_gates.csv',index=False)
pv=r.pivot_table(index=['min_structural_risk','max_structural_risk'],columns='period',values=['avg_net_R','trades','coverage_pct'],aggfunc='first')
# Only 2025 may select best threshold; demand 2025 coverage >=90% BOTH halves and >=100 trades/half.
chosen=[]
for (mn,mx),a in r.groupby(['min_structural_risk','max_structural_risk']):
 a=a.set_index('period')
 if any(a.loc[k,'trades']<100 or a.loc[k,'coverage_pct']<90 for k in ['2025H1','2025H2']):continue
 score=min(a.loc['2025H1','avg_net_R'],a.loc['2025H2','avg_net_R'])
 chosen.append((score,mn,mx,a.loc['2026Q1','avg_net_R'],a.loc['2026Q2Q3_REUSED','avg_net_R'],a.loc['2026Q1','coverage_pct'],a.loc['2026Q2Q3_REUSED','coverage_pct']))
chosen.sort(reverse=True)
(OUT/'risk_gate_2025_selected.json').write_text(json.dumps([dict(train_min_half_R=v[0],min_structural_risk=v[1],max_structural_risk=v[2],review_2026Q1_R=v[3],review_2026Q2Q3_R=v[4],review_2026Q1_coverage=v[5],review_2026Q2Q3_coverage=v[6]) for v in chosen[:5]],indent=2),encoding='utf8')
print('TOP FIVE selected 2025, then 2026 (NOT used for selection):',chosen[:5]);print('total tested',len(chosen),'configs')
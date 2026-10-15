from pathlib import Path
import numpy as np,pandas as pd
B=Path(__file__).resolve().parent; R=B.parent/'reaction_confirmation_lab'
tr=pd.read_csv(R/'train_chosen_trade_log.csv')
src=Path('/mnt/data/full_rerun/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if src.exists():m=pd.read_csv(src)
else:
 from zipfile import ZipFile
 zpath=B.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
 with ZipFile(zpath) as z:
  member=next(n for n in z.namelist() if n.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
  m=pd.read_csv(z.open(member))
hi=m.high.to_numpy(); lo=m.low.to_numpy(); cl=m.close.to_numpy(); tim=m.timestamp.to_numpy()//60000
rows=[]
for _,x in tr.iterrows():
 s=int(x.fill_m1);e=int(x.exit_m1);d=int(x.side);p=x.entry_price;r=x.risk_price
 if e>=len(hi) or e<s:continue
 fav=np.maximum(0,hi[s:e+1]-p)/r if d==1 else np.maximum(0,p-lo[s:e+1])/r
 bad=np.maximum(0,p-lo[s:e+1])/r if d==1 else np.maximum(0,hi[s:e+1]-p)/r
 tups=[(k,int(np.flatnonzero(fav>=k)[0])+s if np.any(fav>=k) else -1) for k in (0.5,1.,1.5,2.,3.)]
 rows.append(dict(period=x.period,entry_m1=s,exit_m1=e,side=d,net_R=x.net_R,reason=int(x.exit_reason),initial_risk=r,duration=tim[e]-tim[s],max_favorable_R=float(fav.max()),max_adverse_R=float(bad.max()),**{f'first_{k}R_idx':n for k,n in tups}))
q=pd.DataFrame(rows);q.to_csv(B/'trade_path_metrics.csv',index=False)
tab=[]
for p,v in q.groupby('period'):
 z={'period':p,'n':len(v),'mean_net_R':v.net_R.mean(),'win_pct':(v.net_R>0).mean()*100,'stop_pct':(v.reason==-1).mean()*100,'tp_pct':(v.reason==1).mean()*100,'time_pct':(v.reason==0).mean()*100,'mean_risk_dollars':v.initial_risk.mean(),'median_risk_dollars':v.initial_risk.median(),'median_duration':v.duration.median(),'stop_after_seen_1R_pct':(v.loc[v.reason==-1,'max_favorable_R']>=1).mean()*100,'tp_reach_observed_MFE_pct':(v.max_favorable_R>=3).mean()*100}
 for a in [0.5,1,1.5,2,3]:z[f'MFE_ge_{a}R_pct']=(v.max_favorable_R>=a).mean()*100
 tab.append(z)
s=pd.DataFrame(tab);s.to_csv(B/'period_diagnostics.csv',index=False)
print(s.round(3).to_string(index=False))
print('fee_r price median per period')
print(q.groupby('period').initial_risk.median())
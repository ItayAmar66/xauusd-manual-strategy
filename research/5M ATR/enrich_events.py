#!/usr/bin/env python3
"""Per-event descriptive context, not causal attribution. Requires pandas/numpy."""
from pathlib import Path
from zipfile import ZipFile
import pandas as pd,numpy as np,json
P=Path(__file__).resolve().parent
Z=P.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
E=pd.read_csv(P/'XAUUSD_Reversal_Legs_4ATR_M5.csv');E['ts']=pd.to_datetime(E.origin_datetime_utc,utc=True)
with ZipFile(Z) as z:
 def read(part):return pd.read_csv(z.open(next(n for n in z.namelist() if n.endswith('/'+part))))
 M=read('xauusd-m1-bid-2025-01-01-2026-09-25.csv')
 F=read('XAUUSD_FVG_Lifecycle_CloseInvalidation.csv')
M.index=pd.to_datetime(M.timestamp,unit='ms',utc=True)
T=E.ts.dt.tz_convert(None).to_numpy(dtype='datetime64[ns]')
ids=M.index.searchsorted(E.ts)
assert (M.index[ids]==E.ts).all()
O=M.open.to_numpy();H=M.high.to_numpy();L=M.low.to_numpy();C=M.close.to_numpy()
P0=E.origin_price.to_numpy();up=E.direction.eq('LONG').to_numpy();N=len(E)
E['origin_M1_high_low_range']=H[ids]-L[ids]
E['origin_at_M1_extreme']=np.where(up,np.isclose(P0,L[ids]),np.isclose(P0,H[ids]))
E['origin_M1_body_pct']=np.divide(abs(C[ids]-O[ids]),H[ids]-L[ids],out=np.zeros(N),where=(H[ids]>L[ids]))
for w in (5,15,60):
 E[f'prior_M1_close_change_{w}m']=C[np.maximum(ids-1,0)]-C[np.maximum(ids-1-w,0)]
 rh=pd.Series(H).shift(1).rolling(w,min_periods=w).max().to_numpy()
 rl=pd.Series(L).shift(1).rolling(w,min_periods=w).min().to_numpy()
 E[f'prior_{w}m_high']=rh[ids];E[f'prior_{w}m_low']=rl[ids]
 E[f'origin_new_{w}m_extreme']=np.where(up,P0<rl[ids],P0>rh[ids])
E['prior_M1_15m_direction_opposite_leg']=np.where(up,E.prior_M1_close_change_15m<0,E.prior_M1_close_change_15m>0)
local=M.index+pd.Timedelta(hours=3)
keys={'day':np.array(local.date),
'week':np.array((local-pd.to_timedelta(local.weekday,unit='D')).date),
'month':np.array(local.strftime('%Y-%m'))}
for name,key in keys.items():
 grp=pd.DataFrame({'key':key,'high':H,'low':L}).groupby('key').agg({'high':'max','low':'min'}).shift(1)
 refs=key[ids]
 E[f'prev_{name}_high']=pd.Series(refs).map(grp.high).to_numpy()
 E[f'prev_{name}_low']=pd.Series(refs).map(grp.low).to_numpy()
 E[f'origin_touches_prev_{name}_liquidity']=np.where(up,P0<=E[f'prev_{name}_low'],P0>=E[f'prev_{name}_high'])
 E[f'origin_distance_prev_{name}_level_atr']=np.where(up,(P0-E[f'prev_{name}_low'])/E.m5_atr14,(E[f'prev_{name}_high']-P0)/E.m5_atr14)
raw=M[['open','high','low','close']]
for freq,label in [('5min','M5'),('15min','M15'),('1h','H1'),('4h','H4'),('1D','D1')]:
 b=raw.resample(freq,label='left',closed='left').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
 previous=b.close.shift(1)
 tr=pd.concat([b.high-b.low,(b.high-previous).abs(),(b.low-previous).abs()],axis=1).max(axis=1)
 atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
 q=pd.DataFrame(index=b.index);q['trend5']=np.sign(b.close-b.close.shift(5));q['body_atr']=abs(b.close-b.open)/atr
 q=q.shift(1).reindex(E.ts,method='ffill')
 E[label+'_trend5']=q.trend5.to_numpy();E[label+'_last_body_atr']=q.body_atr.to_numpy()
 E[label+'_trend_opposes_direction']=np.where(up,E[label+'_trend5']<0,E[label+'_trend5']>0)
F['available']=pd.to_datetime(F.available_at,utc=True)
F['invalidated']=pd.to_datetime(F.invalidated_at,utc=True)
for (tf,side),g in F.groupby(['tf','direction']):
 starts=g.available.dt.tz_convert(None).to_numpy(dtype='datetime64[ns]')
 ends=g.invalidated.dt.tz_convert(None).fillna(pd.Timestamp('2260-01-01')).to_numpy(dtype='datetime64[ns]')
 lo=g.level_low.to_numpy();hi=g.level_high.to_numpy()
 a=np.argsort(starts);starts=starts[a];ends=ends[a];lo=lo[a];hi=hi[a]
 out=np.zeros(N,dtype=bool)
 for k,(t,v) in enumerate(zip(T,P0)):
  stop=np.searchsorted(starts,t,side='right')
  if stop:out[k]=bool(np.any((ends[:stop]>t)&(lo[:stop]<=v)&(hi[:stop]>=v)))
 E[f'active_fvg_{tf}_{side}']=out
fv=[c for c in E if c.startswith('active_fvg_')]
liq=[f'origin_touches_prev_{x}_liquidity' for x in ('day','week','month')]
E['fvg_type_count']=E[fv].sum(axis=1)
E['prior_htf_liquidity_count']=E[liq].fillna(False).sum(axis=1)
E['pre_origin_conditions_count']=E.fvg_type_count+E.prior_htf_liquidity_count+E.origin_new_15m_extreme.astype(int)+E.prior_M1_15m_direction_opposite_leg.astype(int)
def labels(r):
 labels=[x.replace('active_fvg_','FVG:').replace('origin_touches_prev_','LEVEL:').replace('_liquidity','') for x in fv+liq if r[x]]
 if r.origin_new_15m_extreme:labels.append('NEW_15M_EXTREME')
 if r.prior_M1_15m_direction_opposite_leg:labels.append('PRE_15M_COUNTER_MOVE')
 return '|'.join(labels) or 'NO_MATCH_IN_TESTED_RULES'
E['possible_explanation_labels']=E.apply(labels,axis=1)
E['causality_status']='OBSERVATIONAL_NOT_PROVEN'
E.drop(columns=['ts']).to_csv(P/'all_4584_event_context.csv',index=False)
summary={'events':N,'ambiguous':int((E.qa_flag!='OK').sum()),'avg_candidate_conditions':float(E.pre_origin_conditions_count.mean()),'no_match':int((E.possible_explanation_labels=='NO_MATCH_IN_TESTED_RULES').sum()),'counts':{c:int(E[c].fillna(False).astype(bool).sum()) for c in fv+liq+['origin_new_5m_extreme','origin_new_15m_extreme','origin_new_60m_extreme','prior_M1_15m_direction_opposite_leg','M5_trend_opposes_direction','M15_trend_opposes_direction','H1_trend_opposes_direction','H4_trend_opposes_direction']},'max_conditions':int(E.pre_origin_conditions_count.max())}
(P/'event_context_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
pd.DataFrame([{'parameter':k,'events':v,'pct':round(100*v/N,4)} for k,v in summary['counts'].items()]).sort_values('events',ascending=False).to_csv(P/'event_context_ranked.csv',index=False)
assert N==4584 and summary['no_match']==29
print(json.dumps(summary,indent=2))

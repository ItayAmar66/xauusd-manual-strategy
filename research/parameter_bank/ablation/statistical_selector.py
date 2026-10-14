#!/usr/bin/env python3
"""One fixed ML experiment: predict standalone net 4R outcomes from causal 43-factor conditions.
Train 2025H1 -> select coverage-vs-return entry threshold on 2025H2 -> refit through 2026Q1
-> review 2026Q2/Q3, which have already been inspected elsewhere (NOT untouched holdout).
All entry decisions are evaluated forward in clock order; no hindsight best signal of a day.
"""
from pathlib import Path
from zipfile import ZipFile
import numpy as np,pandas as pd,json,time
from numba import njit
from sklearn.ensemble import HistGradientBoostingRegressor
HERE=Path(__file__).resolve().parent;B=HERE.parent
F=pd.read_csv(B/'condition_bank_m5.csv');N=len(F)
local=Path('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv');zp=B.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
if local.exists():M=pd.read_csv(local)
else:
 with ZipFile(zp) as z:
  name=next(x for x in z.namelist() if x.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
  M=pd.read_csv(z.open(name))
np.random.seed(41)
mi=M.timestamp.to_numpy(np.int64)//60000
op=M.open.to_numpy(float);hi=M.high.to_numpy(float);lo=M.low.to_numpy(float);cl=M.close.to_numpy(float)
IX=F.entry_m1_index.to_numpy(np.int64);ATR=F.m5_atr14.to_numpy(float)
X={c:F[c].to_numpy(bool) for c in F.columns if F[c].dtype==bool};
if not X:X={c:F[c].to_numpy(bool) for c in F.columns if c not in ('entry_utc','entry_israel','entry_date','entry_m1_index','m5_atr14','signal_m5_close','fib_zone_low','fib_zone_high')}
def b(x):return X[x]
TT=[('rejection',b('m5_rejection_bull'),b('m5_rejection_bear')),
 ('engulfing',b('m5_engulf_bull'),b('m5_engulf_bear')),
 ('breakout12',b('m5_breakup'),b('m5_breakdown')),
 ('body',b('m5_body_bull'),b('m5_body_bear'))]
# Candidate side per trigger; both-sides-conflict eliminated for that trigger
rows=[]
for name,u,d in TT:
 inds=np.where(u ^ d)[0]
 for i in inds:rows.append((i,1 if u[i] else -1,name))
C=pd.DataFrame(rows,columns=['bank_index','direction','trigger']).sort_values(['bank_index','trigger']).reset_index(drop=True)
idx=C.bank_index.to_numpy(int);direction=C.direction.to_numpy(np.int8);j=IX[idx];atr=ATR[idx]
@njit
def independent_outcomes(j,d,atr,op,hi,lo,cl,minutes):
 n=len(j);r=np.zeros(n);exitidx=np.zeros(n,np.int64);gap=np.zeros(n,np.int8)
 for i in range(n):
  k=j[i];start=k;p=op[k];risk=1.5*atr[i];stop=p-d[i]*risk;tp=p+d[i]*4*risk
  while k<len(op):
   if k>start and minutes[k]-minutes[k-1]>1:
    k-=1;xp=cl[k];gap[i]=1;break
   if minutes[k]-minutes[start]>=120:xp=op[k];break
   if d[i]==1:
    if op[k]<=stop:xp=op[k];break
    if op[k]>=tp:xp=tp;break
    if lo[k]<=stop:xp=stop;break
    if hi[k]>=tp:xp=tp;break
   else:
    if op[k]>=stop:xp=op[k];break
    if op[k]<=tp:xp=tp;break
    if hi[k]>=stop:xp=stop;break
    if lo[k]<=tp:xp=tp;break
   k+=1
  if k==len(op):k=len(op)-1;xp=cl[k];gap[i]=1
  r[i]=d[i]*(xp-p)/risk-.35/risk
  exitidx[i]=k
 return r,exitidx,gap
r,ex,gap=independent_outcomes(j,direction,atr,op,hi,lo,cl,mi)
r=np.where(gap>0,-1.0-.35/(atr*1.5),r)  # stress unobservable gaps, not optimistic proxies
# All 43 flags available at timestamp. Use 43 binary plus logATR, direction, trigger indicators, time of day.
cols=list(X.keys())
fl=np.column_stack([X[c][idx].astype(np.int8) for c in cols]);
entrydates=F.entry_date.to_numpy(dtype='U10')[idx]
localtimes=pd.to_datetime(F.entry_israel.iloc[idx],utc=True).dt.tz_convert('Asia/Jerusalem')
minuteoftheday=(localtimes.dt.hour*60+localtimes.dt.minute).to_numpy()
feature=np.column_stack((fl,np.log1p(atr),direction,(minuteoftheday-360)/840.,*[ (C.trigger==key).to_numpy(np.int8) for key,_,_ in TT])).astype(np.float32)
feature_names=cols+['log1p_atr','direction','time_since_0600_normalized']+[f'trigger_{key}' for key,_,_ in TT]
# near-boundary trades PURGED if their 120min potential outcome crosses sample split; drop 1 calendar day embargo.
train1=entrydates<'2025-07-01';valid=(entrydates>='2025-07-02')&(entrydates<'2026-01-01');
full_train=entrydates<'2026-04-01';review=entrydates>='2026-04-02'
print('Candidates by period:',len(C),int(train1.sum()),int(valid.sum()),int(full_train.sum()),int(review.sum()))
def fit(mask):
 return HistGradientBoostingRegressor(max_iter=120,max_leaf_nodes=12,learning_rate=.04,l2_regularization=15.,min_samples_leaf=100,max_bins=64,random_state=41).fit(feature[mask],r[mask])
def run_policy(mask,scores,threshold):
 # All rows already sorted by bank_index/entry time. At simultaneous minute, select highest model score.
 elig=np.where(mask & (scores>=threshold))[0]
 if not len(elig):return np.array([],int)
 take=[];locked=-1;prev=-1;winner=-1;highest=-1e9
 for i in elig:
  k=j[i]
  if k!=prev and winner>=0:
   if j[winner]>locked:take.append(winner);locked=ex[winner]
   winner=-1;highest=-1e9
  if k>locked and scores[i]>highest:winner=i;highest=scores[i]
  prev=k
 if winner>=0 and j[winner]>locked:take.append(winner)
 return np.array(take,int)
def stats(ind,cal):
 z=r[ind];n=len(z);dates=entrydates[ind]
 dnum=len(np.unique(dates));coverage=100*dnum/max(len(np.unique(F.entry_date.to_numpy(dtype='U10')[np.isin(F.entry_date.to_numpy(dtype='U10'),cal)])),1)
 if not n:return {'n':0,'avg_R':None,'total_R':0,'coverage_pct':0,'winrate_pct':None,'maxdd_R':None,'gap_n':0}
 eq=np.r_[0.,np.cumsum(z)]
 return {'n':n,'avg_R':round(float(z.mean()),6),'total_R':round(float(z.sum()),3),'coverage_pct':round(coverage,3), 'winrate_pct':round(100*float(np.mean(z>0)),3),'maxdd_R':round(float(np.min(eq-np.maximum.accumulate(eq))),3),'gap_n':int(gap[ind].sum())}

def cal_range(start,end):
 a=F.entry_date.to_numpy(dtype='U10');return np.unique(a[(a>=start)&(a<end)])
V=fit(train1);vs=V.predict(feature)
# thresholds as FIXED percentiles of development training predictions, never of the evaluation period itself
qs=[0,30,50,65,75,85,90,95,97.5,99]
thresholds=np.percentile(vs[train1],qs)
variants=[]
valid_cal=cal_range('2025-07-02','2026-01-01')
for q,th in zip(qs,thresholds):
 ids=run_policy(valid,vs,th);m=stats(ids,valid_cal)
 # Penalize low-frequency variants and calendar no-trade days. This is only validation-based selection.
 score= (-99 if m['n']<80 else m['avg_R'] - .5*np.sqrt(100/m['n']) - .003*(100-m['coverage_pct']))
 variants.append({'train_pred_percentile':q,'threshold':round(float(th),7),'validation_selection_score':score,**m})
val=pd.DataFrame(variants).sort_values('validation_selection_score',ascending=False)
val.to_csv(HERE/'ml_threshold_validation_2025H2.csv',index=False)
q_best=float(val.iloc[0].train_pred_percentile)
Z=fit(full_train);scores=Z.predict(feature)
# freeze the percentile cutoff using ONLY TRAIN predictions
final_thresh=float(np.percentile(scores[full_train],q_best))
periods=[('2025H1_IN_SAMPLE_AFTER_REFIT',train1,cal_range('2025-01-01','2025-07-01')),
 ('2025H2_IN_SAMPLE_AFTER_REFIT',valid,valid_cal),
 ('2026Q1_IN_SAMPLE_AFTER_REFIT',(entrydates>='2026-01-01')&(entrydates<'2026-04-01'),cal_range('2026-01-01','2026-04-01')),
 ('2026Q2_REUSED',(entrydates>='2026-04-02')&(entrydates<'2026-07-01'),cal_range('2026-04-02','2026-07-01')),
 ('2026Q3_REUSED',(entrydates>='2026-07-01'),cal_range('2026-07-01','2026-10-01'))]
outputs=[];logs=[]
for name,mask,cal in periods:
 ids=run_policy(mask,scores,final_thresh)
 o={'period':name,'strategy':'gradient_boosted_condition_selector','selected_train_percentile':q_best,'threshold':final_thresh,'selection_only_using_past':True};o.update(stats(ids,cal));outputs.append(o)
 for v in ids: logs.append({'period':name,'entry_utc':F.entry_utc.iloc[idx[v]],'trigger':C.trigger.iloc[v],'direction':int(direction[v]),'score_predicted_R':round(float(scores[v]),5),'entry_price':round(float(op[j[v]]),5),'net_R':round(float(r[v]),6),'gap_uncertain_stress':bool(gap[v]),'exit_time_utc':str(pd.to_datetime(M.timestamp.iloc[ex[v]],unit='ms',utc=True))})
# Baseline uninformed, same signals and same portfolio execution, 4R fixed
for name,mask,cal in periods:
 ids=run_policy(mask,np.ones(len(C)),0)
 o={'period':name,'strategy':'all_triggers_fixed4','selected_train_percentile':0,'threshold':0,'selection_only_using_past':True};o.update(stats(ids,cal));outputs.append(o)
pd.DataFrame(outputs).to_csv(HERE/'ml_selector_period_results.csv',index=False)
pd.DataFrame(logs).to_csv(HERE/'ml_selector_trade_log.csv',index=False)
summ={'candidates':len(C),'independent_gap_stress_n':int(gap.sum()),'features':len(feature_names),'model':'HistGradientBoostingRegressor','train1_through':'2025-06-30','validation':'2025-07-02 through 2025-12-31','final_train_through':'2026-03-31','reused_review':'2026-04-02 through 2026-09-25','percentile_selected_on_validation':q_best,'actual_2025H2_validation_mean_R_at_selected_threshold':float(val.iloc[0].avg_R),'actual_2025H2_validation_n_at_selected_threshold':int(val.iloc[0].n),'chosen_threshold':final_thresh,'review_status':'REUSED_NOT_UNTOUCHED','note':'model estimates a hypothetical 4R outcome; signals were not selected by the retrospective winning-leg catalog'}
(HERE/'ml_summary.json').write_text(json.dumps(summ,indent=2))
print('ML SUMMARY',json.dumps(summ,indent=2));print('ML RESULTS:\n',pd.DataFrame(outputs).to_string(index=False));print('THRESHOLDS:\n',val.to_string(index=False))
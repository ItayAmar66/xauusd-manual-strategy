#!/usr/bin/env python3
"""Iteration 02: causal-at-entry filter ablation on an immutable 253-entry cohort.
Filters only drop entries, not a complete rerun of signal arbitration. Candidate filters
are predeclared; selection uses ONLY 2025, 2026 is REUSED, not virgin holdout.
"""
from pathlib import Path
from zipfile import ZipFile
import pandas as pd, numpy as np
P=Path(__file__).resolve().parent
R=P.parent/'reaction_confirmation_lab'
tr=pd.read_csv(R/'train_chosen_trade_log.csv')
cand=pd.read_csv(R/'confirmed_entry_inventory.csv')
cand=cand[(cand.family=='30M_SWEEP')&(cand.trigger=='MICRO_BOS3')&(cand.H1_aligned)&(cand.M15_aligned)&(cand.H4_aligned)&cand.hour_il.between(15,18,inclusive='left')]
d=tr.merge(cand,left_on=['signal_next_open_m1','side'],right_on=['entry_m1','side'],how='left',validate='many_to_one')
assert len(d)==253 and d.anchor_m1.notna().all()
mfile=Path('/mnt/data/full_rerun/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if mfile.exists():m=pd.read_csv(mfile,usecols=['high','low','open','close'])
else:
 with ZipFile(P.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip') as z:
  f=next(x for x in z.namelist() if x.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
  m=pd.read_csv(z.open(f),usecols=['high','low','open','close'])
h,l,o,c=[m[k].to_numpy() for k in ['high','low','open','close']]
idx=d.confirm_m1.to_numpy(int);anchors=d.anchor_m1.to_numpy(int);side=d.side.to_numpy(int)
d['confirm_lag_minutes']=(idx-anchors)
d['confirm_body_ratio']=abs(c[idx]-o[idx])/np.maximum(h[idx]-l[idx],0.0001)
d['confirm_range_to_risk']=(h[idx]-l[idx])/d.risk_price
d['entry_distance_from_anchor_R']=np.where(side==1,(d.entry_price-l[anchors])/d.risk_price,(h[anchors]-d.entry_price)/d.risk_price)
# The historical chosen entry/stop is unchanged. Pair with TP6-fixed counterfactual on identical entries.
man=pd.read_csv(P/'matched_entry_management_trades.csv')
r6=man[man.rule=='TP6_fixed'][['fill_m1','net_R','gross_R']]
d=d.drop(columns=['net_R','gross_R'])
d=d.merge(r6,on='fill_m1',how='left',validate='one_to_one')
assert d.net_R.notna().all()
# Fixed, interpretable rules; no outcome-based thresholds and no 2026-informed selection.
filters={
 'ALL':np.ones(len(d),bool),
 'CONFIRM_LAG_LE2':d.confirm_lag_minutes<=2,
 'CONFIRM_LAG_LE3':d.confirm_lag_minutes<=3,
 'CONFIRM_LAG_LE4':d.confirm_lag_minutes<=4,
 'CONFIRM_LAG_GE3':d.confirm_lag_minutes>=3,
 'CONFIRM_LAG_GE4':d.confirm_lag_minutes>=4,
 'BODY_GT30PCT':d.confirm_body_ratio>=.30,
 'BODY_GT50PCT':d.confirm_body_ratio>=.50,
 'BODY_GT70PCT':d.confirm_body_ratio>=.70,
 'CONFIRM_RANGE_LE0P25R':d.confirm_range_to_risk<=.25,
 'CONFIRM_RANGE_LE0P50R':d.confirm_range_to_risk<=.50,
 'ENTRY_DIST_ANCHOR_LE1P0R':d.entry_distance_from_anchor_R<=1,
 'ENTRY_DIST_ANCHOR_LE1P5R':d.entry_distance_from_anchor_R<=1.5,
 'ENTRY_DIST_ANCHOR_GE1P0R':d.entry_distance_from_anchor_R>=1,
 'LAG_LE3_AND_BODY_GT50PCT':(d.confirm_lag_minutes<=3)&(d.confirm_body_ratio>=.50),
 'LAG_LE3_AND_DIST_LE1P0R':(d.confirm_lag_minutes<=3)&(d.entry_distance_from_anchor_R<=1),
}
# Period from true entry date; 2025 split is unseen within subsequent 2025 comparison, but selected
# 30M_SWEEP signal family was previously optimized on all 2025 - do not mislabel as pristine.
iso=pd.to_datetime(d.entry_local.str.slice(0,10))
d['period2']=np.select([iso<pd.Timestamp('2025-07-01'),iso<pd.Timestamp('2026-01-01'),iso<pd.Timestamp('2026-04-01')],['2025H1','2025H2','2026Q1'],default='2026Q2Q3')
rows=[]
for name,mask in filters.items():
 for per,g in d[mask].groupby('period2'):
  rows.append(dict(filter=name,period=per,n=len(g),avg_R=g.net_R.mean(),win_pct=100*(g.net_R>0).mean(),total_R=g.net_R.sum(),traded_days=iso.iloc[g.index].nunique()))
  
x=pd.DataFrame(rows);x.to_csv(P/'entry_filter_16x4.csv',index=False)
piv=x.pivot(index='filter',columns='period',values=['avg_R','n']).fillna(0)
rank=[]
for name in filters:
 sub=d[filters[name]]
 train=sub[sub.period2.isin(['2025H1','2025H2'])]
 if len(train)<75:continue
 a=train[train.period2=='2025H1'];b=train[train.period2=='2025H2']
 sc=float(train.net_R.mean()-1.5/np.sqrt(len(train)))
 rank.append(dict(filter=name,train_n=len(train),train_avg=float(train.net_R.mean()),H1_mean=float(a.net_R.mean()) if len(a) else None,H2_mean=float(b.net_R.mean()) if len(b) else None,score=sc))
ranks=pd.DataFrame(rank).sort_values('score',ascending=False)
ranks.to_csv(P/'entry_filter_2025_rank.csv',index=False)
d[['fill_m1','period2','confirm_lag_minutes','confirm_body_ratio','confirm_range_to_risk','entry_distance_from_anchor_R','risk_price','net_R']].to_csv(P/'entry_features_on_253_original_entries.csv',index=False)
print('2025 pre-ranking')
print(ranks.round(3).to_string(index=False))
print('stability')
print(x.pivot(index='filter',columns='period',values='avg_R').round(3).to_string())
# Weekly bootstrap using sums/counts to avoid expensive per-sample dataframe rebuilds.
rg=np.random.default_rng(20261015)
bt=[]
for per in ['TRAIN_2025','REUSED_2026Q1','REUSED_2026Q2Q3']:
 j=d[d.period==per].copy()
 j['week']=pd.to_datetime(j.entry_local.str.slice(0,10)).dt.to_period('W-SUN').astype(str)
 weeks=sorted(j.week.unique())
 arr=np.zeros((len(weeks),4))
 for k,w in enumerate(weeks):
  g=j[j.week==w];sub=g[g.confirm_lag_minutes<=3]
  arr[k]=[g.net_R.sum(),len(g),sub.net_R.sum(),len(sub)]
 ids=rg.integers(0,len(weeks),size=(5000,len(weeks)))
 draws=arr[ids].sum(axis=1)
 keep=draws[:,3]>0;draws=draws[keep]
 means=np.column_stack([draws[:,0]/draws[:,1],draws[:,2]/draws[:,3]])
 differences=means[:,1]-means[:,0]
 ob=[j.net_R.mean(),j[j.confirm_lag_minutes<=3].net_R.mean()]; ob.append(ob[1]-ob[0])
 for k,name in enumerate(['baseline_all','lag_le3','lag_le3_minus_all']):
  vec=means[:,k] if k<2 else differences
  bt.append(dict(period=per,metric=name,observed=float(ob[k]),CI95_lo=float(np.quantile(vec,.025)),CI95_hi=float(np.quantile(vec,.975)),n_baseline=len(j),n_gated=int(sum(j.confirm_lag_minutes<=3)),weeks=len(weeks)))
pd.DataFrame(bt).to_csv(P/'entry_gate_week_bootstrap.csv',index=False)
print('GATE BOOTSTRAP',pd.DataFrame(bt).round(3).to_string(index=False))
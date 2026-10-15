#!/usr/bin/env python3
"""Follow-up iterative research, fixed entry cohort. Replays the recorded 253 M1 confirmations.

The historically selected M1 entry signals are held CONSTANT for every manager. No
extra trades are added when exit occurs sooner, so this is a matched-entry causal
ablation, not a full independent-strategy backtest. Target/manager chosen using
2025 only; 2026 was repeatedly inspected in prior work, not untouched holdout.
"""
import pandas as pd, numpy as np
from pathlib import Path
P=Path(__file__).resolve().parent
M=Path('/mnt/data/full_rerun/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
T=Path('/mnt/data/reaction_confirmation_lab/train_chosen_trade_log.csv')
if not M.exists():
 from zipfile import ZipFile
 zp=P.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
 with ZipFile(zp) as z:
  member=next(n for n in z.namelist() if n.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
  m=pd.read_csv(z.open(member),usecols=['timestamp','open','high','low','close'])
else:
 m=pd.read_csv(M,usecols=['timestamp','open','high','low','close'])
if not T.exists():T=P.parent/'reaction_confirmation_lab'/'train_chosen_trade_log.csv'
t=m.timestamp.to_numpy()//60000
open_=m.open.to_numpy();high=m.high.to_numpy();low=m.low.to_numpy();close=m.close.to_numpy()
tr=pd.read_csv(T)

def simulate(row,rr,manage,fee):
    entry=int(row.fill_m1); d=int(row.side);px=float(row.entry_price);origstop=float(row.SL_price);risk=float(row.risk_price)
    stop=origstop; target=px+d*rr*risk;maxf=0;end=entry;exprice=px;reason='NO_EXIT'
    for z in range(entry,len(t)):
        if t[z]-t[entry]>=120:
            end=z;exprice=open_[z];reason='TIME';break
        if z>entry and t[z]-t[z-1]!=1:
            end=z;exprice=open_[z];reason='DATA_GAP';break
        if d==1:
            if open_[z]<=stop:end=z;exprice=open_[z];reason='STOP_GAP';break
            if open_[z]>=target:end=z;exprice=target;reason='TP_GAP';break
            slhit=low[z]<=stop; tphit=high[z]>=target
            fav=(high[z]-px)/risk
        else:
            if open_[z]>=stop:end=z;exprice=open_[z];reason='STOP_GAP';break
            if open_[z]<=target:end=z;exprice=target;reason='TP_GAP';break
            slhit=high[z]>=stop; tphit=low[z]<=target
            fav=(px-low[z])/risk
        if slhit:end=z;exprice=stop;reason='STOP';break
        if tphit:end=z;exprice=target;reason='TP';break
        maxf=max(maxf,fav)
        newstop=stop
        if manage=='be1' and maxf>=1:newstop=px
        elif manage=='be15' and maxf>=1.5:newstop=px
        elif manage=='ladder1':
            if maxf>=1:newstop=px+d*np.floor(max(0,maxf-0.5)/0.5)*0.5*risk
        elif manage=='be2' and maxf>=2:newstop=px
        if d==1:stop=max(stop,newstop)
        else:stop=min(stop,newstop)
        if z==len(t)-1:end=z;exprice=close[z];reason='LAST'
    gross=d*(exprice-px)/risk
    return gross-fee/risk,gross,reason,int(t[end]-t[entry])

rows=[];logs=[]
for rr in [2,3,4,5,6,8]:
 for manage in ['fixed','be1','be15','be2','ladder1']:
  for _,r in tr.iterrows():
   net,gross,reason,duration=simulate(r,rr,manage,0.35)
   logs.append(dict(rule=f'TP{rr}_{manage}',period=r.period,fill_m1=int(r.fill_m1),entry_local=r.entry_local,net_R=net,gross_R=gross,exit_reason=reason,duration_minutes=duration,initial_risk=r.risk_price))
logs=pd.DataFrame(logs)
for (rule,period),g in logs.groupby(['rule','period']):
 rows.append(dict(rule=rule,period=period,n=len(g),avg_R=float(g.net_R.mean()),avg_R_fee070=float(np.mean(g.gross_R-0.70/g.initial_risk)),total_R=float(g.net_R.sum()),win_pct=float((g.net_R>0).mean()*100),stop_rate=float(g.exit_reason.str.startswith('STOP').mean()*100),tp_rate=float(g.exit_reason.str.startswith('TP').mean()*100),time_rate=float((g.exit_reason=='TIME').mean()*100),median_minutes=float(g.duration_minutes.median())))
results=pd.DataFrame(rows).sort_values(['rule','period']);results.to_csv(P/'matched_entry_management_30x3.csv',index=False)
logs.to_csv(P/'matched_entry_management_trades.csv',index=False)
# Verify replay's control condition exactly matches immutable prior trade log.
control=logs[logs.rule=='TP3_fixed'].sort_values('fill_m1').reset_index(drop=True)
orig=tr.sort_values('fill_m1').reset_index(drop=True)
assert len(control)==len(orig)==253
assert np.allclose(control.net_R,orig.net_R,atol=1e-10),f'Mismatch to source {np.max(abs(control.net_R-orig.net_R))}'
# Select on TRAIN_2025 ONLY; penalize wide variance of daily portfolio outcomes.
train=results.query("period=='TRAIN_2025'").copy()
train['rank_score']=train.avg_R-1.5*np.sqrt((1+(train.win_pct/100))/train.n)
train=train.sort_values('rank_score',ascending=False)
train.to_csv(P/'management_selected_train_only.csv',index=False)
print('CONTROL MATCHES PRIOR LOG',len(control))
print(results.pivot(index='rule',columns='period',values='avg_R').round(3).to_string())
print('TRAIN SELECT TOP',train[['rule','avg_R','rank_score']].head(6).to_string(index=False))

# Paired, weekly-block bootstrap; exploratory uncertainty, not familywise corrected.
from datetime import datetime
logs['week']=pd.to_datetime(logs.entry_local.str.slice(0,10)).dt.to_period('W-SUN').astype(str)
rg=np.random.default_rng(20261015)
selected_rules=['TP3_fixed','TP4_fixed','TP6_fixed','TP6_be1']
blocks=[]
for period in ('TRAIN_2025','REUSED_2026Q1','REUSED_2026Q2Q3'):
 f=logs[(logs.period==period)&logs.rule.isin(selected_rules)]
 for rule in selected_rules:
  tsub=f[f.rule==rule];w=tsub.groupby('week').net_R.agg(['sum','size']).to_numpy()
  idx=rg.integers(0,len(w),size=(5000,len(w)))
  sample=w[idx];means=sample[:,:,0].sum(axis=1)/sample[:,:,1].sum(axis=1)
  blocks.append(dict(period=period,comparison=rule,observed=float(tsub.net_R.mean()),CI95_lo=float(np.quantile(means,.025)),CI95_hi=float(np.quantile(means,.975)),bootstrap_weeks=len(w),n=len(tsub)))
 # Pair returns of 6R vs 3R on exactly the same entry times
 x=f[f.rule=='TP6_fixed'][['fill_m1','net_R','week']].merge(f[f.rule=='TP3_fixed'][['fill_m1','net_R']],on='fill_m1',suffixes=('_6','_3'))
 x['diff']=x.net_R_6-x.net_R_3
 w=x.groupby('week')['diff'].agg(['sum','size']).to_numpy();ix=rg.integers(0,len(w),size=(5000,len(w)));sample=w[ix];means=sample[:,:,0].sum(axis=1)/sample[:,:,1].sum(axis=1)
 blocks.append(dict(period=period,comparison='TP6_fixed_minus_TP3_fixed',observed=float(x['diff'].mean()),CI95_lo=float(np.quantile(means,.025)),CI95_hi=float(np.quantile(means,.975)),bootstrap_weeks=len(w),n=len(x)))
pd.DataFrame(blocks).to_csv(P/'bootstrap_paired_weekly.csv',index=False)
print('BOOTSTRAP',pd.DataFrame(blocks).round(3).to_string(index=False))
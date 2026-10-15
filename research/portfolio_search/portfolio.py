from pathlib import Path
import numpy as np,pandas as pd,json,itertools
from zipfile import ZipFile
P=Path(__file__).resolve().parent;ROOT=P.parent
B=pd.read_csv(ROOT/'parameter_bank'/'condition_bank_m5.csv')
local_m1=Path('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if local_m1.exists():M=pd.read_csv(local_m1)
else:
 with ZipFile(ROOT/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip') as z:
  member=next(a for a in z.namelist() if a.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
  M=pd.read_csv(z.open(member))
S=pd.read_csv(P/'serial_screen_all.csv')
cache=np.load(P/'outcomes_cache.npz');R=cache['r'];X=cache['exit'];FLAG=cache['flag'];N=len(B)
idx=np.repeat(B.entry_m1_index.to_numpy(),2);D=B.entry_date.to_numpy();local=pd.DatetimeIndex(pd.to_datetime(B.entry_israel,utc=True)).tz_convert('Asia/Jerusalem');hour=local.hour+local.minute/60
mv=np.isfinite(R[0]);period=np.repeat(np.where(D<'2026-01-01',0,np.where(D<'2026-04-01',1,2)),2)
# note: mapping j to management configs exactly follows explore.py
configs=[(s,t,ma) for s in [0.75,1.0,1.5,2.0,2.5] for t in [3,4,5,8] for ma in [0,1,3]]
features={}
def bv(n):return B[n].to_numpy(dtype=bool)
for a,b,k in [
 ('m15_up','m15_down','m15_aligned'),('h1_up','h1_down','h1_aligned'),('h4_up','h4_down','h4_aligned'),('m15_down','m15_up','m15_opposite'),('h1_down','h1_up','h1_opposite'),('h4_down','h4_up','h4_opposite'),
 ('weekly_discount','weekly_premium','weekly_value_side'),('weekly_premium','weekly_discount','weekly_opposite_side'),('weekly_rangebottom20','weekly_rangetop20','weekly_outer20'),('m5_up','m5_down','m5_up'),('m5_down','m5_up','m5_down'),('m5_body_bull','m5_body_bear','body'),('m5_rejection_bull','m5_rejection_bear','rejection'),('m5_engulf_bull','m5_engulf_bear','engulf'),('m5_breakup','m5_breakdown','breakout'),('prior_15m_down','prior_15m_up','prior15_opposite'),('prior_15m_up','prior_15m_down','prior15_aligned'),('m5_rsi_oversold','m5_rsi_overbought','rsi_fade'),('pdl_sweep_reclaim','pdh_sweep_reclaim','day_sweep'),('pwl_sweep_reclaim','pwh_sweep_reclaim','week_sweep'),('pdl_sweep_reclaim_last60m','pdh_sweep_reclaim_last60m','day_sweep_last60'),('pwl_sweep_reclaim_last60m','pwh_sweep_reclaim_last60m','week_sweep_last60'),('fib_h1_bull_618_786','fib_h1_bear_618_786','fib_h1'),('fvg_touch_H1_BULL','fvg_touch_H1_BEAR','h1_fvg'),('fvg_touch_H4_BULL','fvg_touch_H4_BEAR','h4_fvg'),('fvg_touch_M15_BULL','fvg_touch_M15_BEAR','m15_fvg'),('fvg_touch_M5_BULL','fvg_touch_M5_BEAR','m5_fvg')]:features[k]=np.stack([bv(a),bv(b)],axis=1).reshape(-1)
features['displacement']=np.repeat(bv('m15_displacement'),2)
for lo,hi in [(6,9),(9,12),(12,15),(15,17),(17,20),(6,12),(12,20),(9,17),(16,20)]:features[f'hour_{lo}_{hi}']=np.repeat(np.asarray((hour>=lo)&(hour<hi)),2)
def mask_rule(rule):
 tokens=rule.split('|');mask=features[tokens[0]].copy()
 for k in tokens[1:]:
  if k in features:mask &= features[k]
 return mask
# Recompute training lower confidence score from actually nonoverlapping trades, for independent candidates
sel=S[(S.train_n>=70)&(S.val_n>=12)&(S.review_n>=20)&(S.train_avgR>0)].copy()
sel['train_lcb_proxy']=sel.train_avgR-2.4/np.sqrt(sel.train_n)  # transparent aggressive conservative estimate
sel=sel.sort_values('train_lcb_proxy',ascending=False)
print('candidate count',len(sel),'top training LCB',sel[['rule','train_n','train_avgR','val_n','val_avgR','review_n','review_avgR','train_lcb_proxy']].head(20).to_string(index=False),flush=True)
# market denominator weekday >600 M1 candles; same index previous
mark=pd.DataFrame({'date':pd.DatetimeIndex(pd.to_datetime(M.timestamp,unit='ms',utc=True)).tz_convert('Asia/Jerusalem').date,'high':M.high,'low':M.low}).groupby('date').agg(n=('high','size'),hi=('high','max'),lo=('low','min'))
mark=mark[(mark.n>=600)&(mark.hi>mark.lo)&(pd.DatetimeIndex(mark.index).weekday<5)]
marketdays=np.array([str(x) for x in mark.index]);all_day=set(marketdays)
# Portfolio chronological, priority = preset list; later time trades if no active position; for same timestamp pick priority
# Selection train 2025, validation Q1, review 2026Q2Q3.
# Daily fallback 06:10 or first 06:00-07:00 valid bar for date (one each) with M15 direction inferred from closed candles.
fallback=np.zeros(2*N,dtype=bool)
for day,group in B.groupby('entry_date',sort=True):
 ix=group.index.to_numpy();jj=np.flatnonzero((hour[ix]>=6.1666666)&(hour[ix]<7)&(B.m15_up.iloc[ix].to_numpy()|B.m15_down.iloc[ix].to_numpy()))
 if len(jj):
  i=ix[jj[0]];fallback[2*i if B.m15_up.iloc[i] else 2*i+1]=True
# Unchosen fallback every day? yes approx
all_conds={}
# Deduplicate by trigger family and secondaries, select 4 diversifying 2025 result only.
for _,r in sel.head(350).iterrows():
 name=r['rule'];all_conds[name]=mask_rule(name)
# actual exec on one-direction mask, prioritization of day, if simultaneous conflict choose best training prior

def portfolio(strategies,with_daily=False,trace=False):
 # tuple(name,j,mask,weight_priority)
 offers=[]
 for priority,(name,j,mask) in enumerate(strategies):
  ids=np.flatnonzero(mask&np.isfinite(R[j]))
  offers.extend([(int(idx[a]),int(priority),int(a),int(j),name) for a in ids])
 if with_daily:
  ids=np.flatnonzero(fallback&np.isfinite(R[16]))
  offers.extend([(int(idx[a]),99,int(a),int(16), 'Daily_0610_M15_Trend') for a in ids])  # stop .75 ATR target 4R manager 1 = index 4
 offers.sort(key=lambda x:(x[0],x[1]))
 records=[];locked=-1;laststart=-1
 for when,priority,e,j,name in offers:
  if when<=locked or when==laststart:continue
  laststart=when;locked=int(X[j,e]);ret=float(R[j,e]);records.append((name,when,e,locked,ret,float(FLAG[j,e]),j))
 return records

def stats(trades):
 rows=[]
 for p in [0,1,2]:
  subset=[rec for rec in trades if period[rec[2]]==p]
  r=np.array([x[4] for x in subset]);ds=[D[x[2]//2] for x in subset]
  dates=np.array([dt for dt in marketdays if (dt<'2026-01-01' if p==0 else ('2026-01-01'<=dt<'2026-04-01' if p==1 else dt>='2026-04-01'))]);full=len(dates)
  equity=np.r_[0,np.cumsum(r)];dd=(equity-np.maximum.accumulate(equity)).min()
  rows.append(dict(n=len(r),avgR=float(r.mean()) if len(r) else np.nan,totalR=float(r.sum()),coverage=100*len(set(ds)&set(dates))/full if full else 0,days=len(set(ds)),eligible_days=full,max_dd=float(dd),gap_exits=sum(int(x[5]==2) for x in subset)))
 return rows

# Maximize training performance while rewarding new days in portfolio. Selected greedily, distinct trigger, >2/5 2025 subsets positive is desirable
picked=[];triggers=set();current=[]
for iteration in range(4):
 bestscore=-1e10;best=None
 for _,r in sel.head(350).iterrows():
  name=r.rule
  if name not in all_conds:continue
  if name in [x[0] for x in picked]:continue
  t=name.split('|')[0]
  if t in triggers:continue
  mgr=int(r['config']);cand=picked+[(name,mgr,all_conds[name])]
  per=stats(portfolio(cand,False))[0]
  if per['n']<max(80,50*(iteration+1)):continue
  # meanR goal, higher # traded days, no overlap bias; penalty for low n
  score=per['avgR']-1.2/np.sqrt(per['n'])+0.22*(per['coverage']/100)
  if score>bestscore:bestscore=score;best=(name,mgr,per)
 if not best:break
 name,mgr,p=best;picked.append((name,mgr,all_conds[name]));triggers.add(name.split('|')[0]);print('selected',iteration+1,name,configs[mgr],p,'score',bestscore,flush=True)
res={}
for n,with_daily in [('portfolio_without_fallback',False),('portfolio_with_daily_fallback',True)]:
 trades=portfolio(picked,with_daily)
 res[n]=stats(trades)
 def to_record(rec):
  name,when,e,exit_index,net,reason,j=rec
  d=1 if e%2==0 else -1
  st,rr,man=configs[j]
  entry=float(M.open.iloc[when]);risk=float(B.m5_atr14.iloc[e//2])*st
  price=entry+d*(net*risk+0.35)
  start=pd.Timestamp(int(M.timestamp.iloc[when]),unit='ms',tz='UTC')
  end=pd.Timestamp(int(M.timestamp.iloc[exit_index]),unit='ms',tz='UTC')
  return {'strategy':name,'entry_utc':str(start),'entry_israel':str(start.tz_convert('Asia/Jerusalem')),'date_israel':str(D[e//2]),'direction':'LONG' if d==1 else 'SHORT','entry_price':entry,'initial_stop_price':entry-d*risk,'target_price':entry+d*rr*risk,'exit_price':price,'exit_utc':str(end),'duration_minutes':(end-start).total_seconds()/60,'risk_atr_multiple':st,'target_R':rr,'manager':man,'net_R':net,'exit_reason_code':reason,'entry_m1_index':when,'exit_m1_index':exit_index}
 df=pd.DataFrame([to_record(rec) for rec in trades])
 df.to_csv(P/f'{n}_trade_log.csv',index=False)
 print(n,'len',len(df),stats(trades),flush=True)
 print('strategies',df.strategy.value_counts().to_dict(),flush=True)
# daily fallback stop 1.0ATR, target 4R and BE after +1.5R
with open(P/'portfolio_summary.json','w') as f:json.dump({'configs':configs,'selected_2025_only':[{'rule':a,'config':configs[b]} for a,b,_ in picked],'results':res,'n_screened_combinations':20302,'n_exit_configs':60,'n_ranked_serial_candidates':len(S),'warning':'2026 already used in prior research; not an untouched holdout; training 2025-only heavily data-mined; no certified trading edge.'},f,indent=2)
print('finish',flush=True)
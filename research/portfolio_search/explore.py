from pathlib import Path
import numpy as np,pandas as pd,time,os, itertools,json
from numba import njit
from zipfile import ZipFile
T0=time.time();P=str(Path(__file__).resolve().parent);ROOT=Path(__file__).resolve().parents[1]
bank=pd.read_csv(ROOT/'parameter_bank'/'condition_bank_m5.csv')
local_m1=Path('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if local_m1.exists(): m=pd.read_csv(local_m1)
else:
 with ZipFile(ROOT/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip') as z:
  member=next(a for a in z.namelist() if a.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
  m=pd.read_csv(z.open(member))
N=len(bank);n=len(m)
times=(m.timestamp.to_numpy(dtype=np.int64)//60000)
O=m.open.to_numpy(np.float64);H=m.high.to_numpy(np.float64);L=m.low.to_numpy(np.float64);C=m.close.to_numpy(np.float64)
ids=bank.entry_m1_index.to_numpy(np.int64);atr=bank.m5_atr14.to_numpy(np.float64)
side=np.repeat(np.array([1,-1],dtype=np.int8),N) if False else np.tile(np.array([1,-1],dtype=np.int8),N)
idx=np.repeat(ids,2);ATR=np.repeat(atr,2)
end_ix=np.searchsorted(times,times[idx]+120,side='left')
@njit
def outcomes(idx,ends,sides,atr,tm,op,hi,lo,cl,stopmult,rr,manager,cost):
 N=len(idx)
 ret=np.empty(N,np.float32);xit=np.empty(N,np.int64);flag=np.zeros(N,np.int8)
 for z in range(N):
  j=idx[z]; d=sides[z]; risk=atr[z]*stopmult
  if not np.isfinite(risk) or risk<0.7:
   ret[z]=np.nan;xit[z]=j;flag[z]=4;continue
  stop=op[j]-d*risk;tp=op[j]+d*rr*risk
  k=ends[z];limit=k if k<len(op) else len(op)-1
  xprice=cl[limit];xi=limit;exitflag=3;favor=0.
  for i in range(j,limit):
   if i>j and tm[i]-tm[i-1]>1:
    # stop evaluation because unknown price movement during a gap
    xi=i-1;xprice=cl[xi];exitflag=2;break
   if (d==1 and op[i]<=stop) or (d==-1 and op[i]>=stop):
    xi=i;xprice=op[i];exitflag=-1;break
   if (d==1 and op[i]>=tp) or (d==-1 and op[i]<=tp):
    xi=i;xprice=tp;exitflag=1;break
   hitstop=lo[i]<=stop if d==1 else hi[i]>=stop
   hittp=hi[i]>=tp if d==1 else lo[i]<=tp
   if hitstop:
    xi=i;xprice=stop;exitflag=-1;break
   if hittp:
    xi=i;xprice=tp;exitflag=1;break
   favorable=(hi[i]-op[j])*d if d==1 else (op[j]-lo[i])*d
   if favorable>favor:favor=favorable
   cand=stop
   if manager==1 and favor>=1.5*risk:cand=op[j]
   if manager==2 and favor>=2*risk:cand=op[j]
   if manager==3 and favor>=1*risk:cand=op[j]+d*max(0.,np.floor(favor/(0.5*risk))-2)*0.5*risk
   if manager==4 and favor>=1*risk:cand=op[j]+d*max(0.,np.floor(favor/risk)-1)*risk
   if d==1:stop=max(stop,cand)
   else:stop=min(stop,cand)
  # A market must be open at the 120-minute timeout: if gap exists at timeout, exit from last known observed close instead
  if exitflag==3 and limit>j and tm[limit]-tm[limit-1]>1:
   xi=limit-1;xprice=cl[xi];exitflag=2
  if exitflag==3 and limit<len(op) and tm[limit]-tm[j]<=120:xprice=op[limit]
  ret[z]=d*(xprice-op[j])/risk-cost/risk;xit[z]=xi;flag[z]=exitflag
 return ret,xit,flag

def bv(name):return bank[name].to_numpy(dtype=bool)
feat={}
for a,b,k in [
 ('m15_up','m15_down','m15_aligned'),('h1_up','h1_down','h1_aligned'),('h4_up','h4_down','h4_aligned'),
 ('m15_down','m15_up','m15_opposite'),('h1_down','h1_up','h1_opposite'),('h4_down','h4_up','h4_opposite'),
 ('weekly_discount','weekly_premium','weekly_value_side'),('weekly_premium','weekly_discount','weekly_opposite_side'),
 ('weekly_rangebottom20','weekly_rangetop20','weekly_outer20'),
 ('m5_up','m5_down','m5_up'),('m5_down','m5_up','m5_down'),
 ('m5_body_bull','m5_body_bear','body'),('m5_rejection_bull','m5_rejection_bear','rejection'),('m5_engulf_bull','m5_engulf_bear','engulf'),
 ('m5_breakup','m5_breakdown','breakout'),('prior_15m_down','prior_15m_up','prior15_opposite'),('prior_15m_up','prior_15m_down','prior15_aligned'),
 ('m5_rsi_oversold','m5_rsi_overbought','rsi_fade'),
 ('pdl_sweep_reclaim','pdh_sweep_reclaim','day_sweep'),('pwl_sweep_reclaim','pwh_sweep_reclaim','week_sweep'),
 ('pdl_sweep_reclaim_last60m','pdh_sweep_reclaim_last60m','day_sweep_last60'),('pwl_sweep_reclaim_last60m','pwh_sweep_reclaim_last60m','week_sweep_last60'),
 ('fib_h1_bull_618_786','fib_h1_bear_618_786','fib_h1'),
 ('fvg_touch_H1_BULL','fvg_touch_H1_BEAR','h1_fvg'),('fvg_touch_H4_BULL','fvg_touch_H4_BEAR','h4_fvg'),
 ('fvg_touch_M15_BULL','fvg_touch_M15_BEAR','m15_fvg'),('fvg_touch_M5_BULL','fvg_touch_M5_BEAR','m5_fvg'),
 ]:
 feat[k]=np.stack([bv(a),bv(b)],axis=1).reshape(-1)
feat['displacement']=np.repeat(bv('m15_displacement'),2)
# intraday windows local determined by saved timestamps
h=pd.DatetimeIndex(pd.to_datetime(bank.entry_israel,utc=True)).tz_convert('Asia/Jerusalem')
hh=h.hour+h.minute/60
for lo,hi in [(6,9),(9,12),(12,15),(15,17),(17,20),(6,12),(12,20),(9,17),(16,20)]:feat[f'hour_{lo}_{hi}']=np.repeat(np.asarray((hh>=lo)&(hh<hi)),2)
# market days calendar; don't exclude partial 2025 Feb only if 2 M1 bars etc
market=pd.DataFrame({'date':pd.DatetimeIndex(pd.to_datetime(m.timestamp,unit='ms',utc=True)).tz_convert('Asia/Jerusalem').date,'h':H,'l':L}).groupby('date').agg(n=('h','size'),hi=('h','max'),low=('l','min'))
market=market[(market.n>=600)&(market.hi>market.low)]
market=market[pd.DatetimeIndex(market.index).weekday<5]
print('market',len(market),'time',time.time()-T0,flush=True)
# include only 06-20 complete (bank already selected) no multiple parallel position
TRAINEND='2026-01-01';VALEND='2026-04-01'
tr=np.repeat(bank.entry_date.to_numpy()<TRAINEND,2)
val=np.repeat((bank.entry_date.to_numpy()>=TRAINEND)&(bank.entry_date.to_numpy()<VALEND),2)
rev=np.repeat(bank.entry_date.to_numpy()>=VALEND,2)
# only every other event is for given direction: baseline signal triggers set names
triggers=['body','rejection','engulf','breakout','rsi_fade','day_sweep','week_sweep','day_sweep_last60','week_sweep_last60','fib_h1','m15_fvg','m5_fvg','h1_fvg','h4_fvg']
# singular group base triggers: body common 50%, may dominate fallback coverage
basefilters=[k for k in feat if not k.startswith('hour_') and k not in ('body','rejection','engulf','breakout','rsi_fade','day_sweep','week_sweep','day_sweep_last60','week_sweep_last60','fib_h1','m15_fvg','m5_fvg','h1_fvg','h4_fvg')]
others=['m15_fvg','m5_fvg','h1_fvg','h4_fvg','day_sweep_last60','week_sweep_last60','fib_h1','displacement','rejection','engulf']
# 2-3 directional conditions; combinations selected on 2025 training only
features=[k for k in basefilters+others if k!='m5_down']
# costs and stop/TP grid, use two managers
configs=[(s,t,ma) for s in [0.75,1.0,1.5,2.0,2.5] for t in [3,4,5,8] for ma in [0,1,3]]
print('configs',len(configs),flush=True)
# compile call
outcomes(idx[:2],end_ix[:2],side[:2],ATR[:2],times,O,H,L,C,1.,4.,0,0.35)
# evaluate rule single signals by per-candidate hypothetical R on TRAIN, score small penalty for volume
# precompute outcomes array for all side-times and each exit config, ~150528 x 60 = ~ 140MB R + exits; 60*~10M 600m loops
out_arr=np.empty((len(configs),len(idx)),dtype='float32');x_arr=np.empty((len(configs),len(idx)),dtype='int32'); flag_arr=np.empty((len(configs),len(idx)),dtype='int8')
for i,(stop,rr,manager) in enumerate(configs):
 o,x,f=outcomes(idx,end_ix,side,ATR,times,O,H,L,C,stop,rr,manager,.35)
 out_arr[i]=o;x_arr[i]=x;flag_arr[i]=f
 if i%10==0:print('computed',i+1,'/',len(configs),'elapsed',round(time.time()-T0,1),flush=True)
np.savez_compressed(P+'/outcomes_cache.npz',r=out_arr,exit=x_arr,flag=flag_arr)
# shortlist thousands of conjunctions, score initial conditions using train only, never retain full masks for all variants
import heapq
basefilters=[k for k in basefilters if k!='m5_down']
features=['m15_aligned','h1_aligned','h4_aligned','m15_opposite','h1_opposite','h4_opposite','weekly_value_side','weekly_opposite_side','weekly_outer20','m5_up','prior15_opposite','prior15_aligned','m15_fvg','m5_fvg','h1_fvg','h4_fvg','day_sweep_last60','week_sweep_last60','fib_h1','displacement']
windows=['hour_6_12','hour_12_20','hour_6_9','hour_9_12','hour_12_15','hour_15_17','hour_17_20','hour_9_17','hour_16_20','NONE']
heap=[];rule_count=0
# use 4 preconfigured management variants to prevent prematurely omitting promising patterns
screen_configs=[0,3,12,16,21,34,52]
valid=np.any(np.isfinite(out_arr),axis=0)
for t in triggers:
 for hrs in windows:
  base=feat[t] if hrs=='NONE' else feat[t]&feat[hrs]
  if (base&tr).sum()<60:continue
  base_masks=[(t+'|'+hrs,base)]
  for a in features:
   if a==t:continue
   mm=base&feat[a]
   if (mm&tr).sum()>=60:base_masks.append((t+'|'+hrs+'|'+a,mm))
  for a,b0 in itertools.combinations(features,2):
   if t==a or t==b0:continue
   mm=base&feat[a]&feat[b0]
   if (mm&tr).sum()>=60:base_masks.append((t+'|'+hrs+'|'+a+'|'+b0,mm))
  for label,mm in base_masks:
   elig=np.flatnonzero(mm&tr&valid)
   k=len(elig)
   if k<60:continue
   rule_count+=1
   vals=np.nanmean(out_arr[screen_configs][:,elig],axis=1)
   j0=int(np.argmax(vals-0.8/np.sqrt(k)))
   score=float(vals[j0]-0.8/np.sqrt(k))
   if len(heap)<850:heapq.heappush(heap,(score,rule_count,label,screen_configs[j0]))
   elif score>heap[0][0]:heapq.heapreplace(heap,(score,rule_count,label,screen_configs[j0]))
 print('trigger',t,'total_rules',rule_count,'time',round(time.time()-T0,1),flush=True)
# recompute masks only for top candidates
best=sorted(heap,reverse=True)
featlist=[]
def reconstruct(label):
 tokens=label.split('|');m=feat[tokens[0]].copy()
 for extra in tokens[1:]:
  if extra in feat:m &= feat[extra]
 return m
names=[];masks=[]
for _,_,label,_ in best:
 names.append(label);masks.append(reconstruct(label))
print('top selected',len(names),'time',time.time()-T0,flush=True)
# Score all managers for shortlisted candidates; independent time values only train, then nonoverlapping serial outcomes
meta=[]
for i,mask in enumerate(masks):
 elig=np.flatnonzero(mask&tr&valid);k=len(elig)
 avg=np.nanmean(out_arr[:,elig],axis=1)
 best_j=np.argsort(avg)[:-8:-1]  # top 7 management variants
 for j in best_j:
  meta.append((i,int(j),k,float(avg[j])))
meta.sort(key=lambda x:x[-1],reverse=True)
pd.DataFrame([{'rule':names[i],'cfg':str(configs[j]),'train_events':k,'naive_train_R':mean} for i,j,k,mean in meta]).to_csv(P+'/train_rule_screen_all.csv',index=False)
# serial simulations: independent candidate entries must not overlap active position; repeat train/valid/review
periods=np.where(tr,0,np.where(val,1,2)).astype('int8')
marketdate=np.array([str(x) for x in market.index]);days=bank.entry_date.to_numpy()
def serial(mask,j,period):
 ev0=np.flatnonzero(mask&valid&(periods==period))
 # sorting naturally 5m events, at same timestamp different opposite sides. Reject when signal conflict.
 ev=[];rets=[];locked=-1;last=-1
 for x in ev0:
  if idx[x]<=locked:continue
  if x//2==last:continue
  ev.append(x);rets.append(out_arr[j,x]);locked=x_arr[j,x];last=x//2
 return np.array(ev,dtype=np.int64),np.array(rets,dtype=np.float32)
results=[]
# all shortlist and 7 managers, serial performance
for i,j,k,avg in meta:
 row={'rule':names[i],'stop_atr':configs[j][0],'tp_R':configs[j][1],'manager':configs[j][2],'index':i,'config':j,'train_event_naive_R':avg}
 for p,name in [(0,'train'),(1,'val'),(2,'review')]:
  ev,rs=serial(masks[i],j,p)
  d=days[ev//2]
  denom=((marketdate<TRAINEND) if p==0 else ((marketdate>=TRAINEND)&(marketdate<VALEND) if p==1 else marketdate>=VALEND)).sum()
  row.update({name+'_n':len(rs),name+'_avgR':float(rs.mean()) if len(rs) else np.nan,name+'_sumR':float(rs.sum()),name+'_coverage':len(np.unique(d))/denom if denom else 0,name+'_days':len(np.unique(d))})
 results.append(row)
scores=pd.DataFrame(results).sort_values('train_avgR',ascending=False)
scores.to_csv(P+'/serial_screen_all.csv',index=False)
print('tested serial',len(scores),'top',scores.head(20)[['rule','stop_atr','tp_R','manager','train_n','train_avgR','val_n','val_avgR','review_n','review_avgR','train_coverage']].to_string(index=False),flush=True)
print('train>1',sum((scores.train_avgR>=1)&(scores.train_n>=100)),'val>1',sum(scores.val_avgR>=1),'review>1',sum(scores.review_avgR>=1))
print('elapsed',round(time.time()-T0,1),flush=True)
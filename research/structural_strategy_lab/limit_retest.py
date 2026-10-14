"""Exploratory next-5m pending-limit entry price improvement, no hindsight selection."""
from pathlib import Path
import numpy as np,pandas as pd,json,time
from numba import njit
src=Path(__file__).with_name('research.py').read_text()
# import only data+feature setup, not the previous 1530-variant run
exec(src.split('records=[];trades=[]')[0],globals())
T0=time.time()
@njit
def limit_sim(sig_idx,sides,stops,limits,atrvals,rr,manager,O,H,L,C,TIME,hr,weekday):
    kmax=len(sig_idx)
    r=np.empty(kmax,np.float64);timestamps=np.empty(kmax,np.int64);durations=np.empty(kmax,np.int64)
    orig=np.empty(kmax,np.int64);ent=np.empty(kmax,np.int64);out=np.empty(kmax,np.int64);why=np.empty(kmax,np.int8)
    cnt=0;lock=-1
    for p in range(kmax):
        i=sig_idx[p];di=sides[p];sl=stops[p];want=limits[p]
        if i+1<=lock:continue
        j=-1;fill=0.0
        for k in range(i+1,min(i+7,len(TIME))):
            if TIME[k]-TIME[i]>6:break
            if (TIME[k]-TIME[k-1])!=1:break
            if hr[k]<6 or hr[k]>=20 or weekday[k]>=5:break
            # long limit crosses if low <= desired limit, and short limit crosses if high >=desired limit
            if (di==1 and L[k]<=want) or (di==-1 and H[k]>=want):
                fill=min(O[k],want) if di==1 else max(O[k],want)
                j=k;break
        if j==-1:continue
        risk=(fill-sl)*di
        if risk<0.65 or risk>6*atrvals[p] or not np.isfinite(risk):continue
        tp=fill+di*rr*risk
        stop=sl;maxf=0.;exit=j;px=fill;reason=8
        for k in range(j,len(TIME)):
            if TIME[k]-TIME[j]>=120:
                exit=k;px=O[k];reason=0;break
            if k>j and TIME[k]-TIME[k-1]!=1:
                exit=k-1;px=C[k-1];reason=2;break
            if di==1:
                if O[k]<=stop:exit=k;px=O[k];reason=-1;break
                if O[k]>=tp:exit=k;px=tp;reason=1;break
                hitstop=L[k]<=stop;hittp=H[k]>=tp
            else:
                if O[k]>=stop:exit=k;px=O[k];reason=-1;break
                if O[k]<=tp:exit=k;px=tp;reason=1;break
                hitstop=H[k]>=stop;hittp=L[k]<=tp
            if hitstop:exit=k;px=stop;reason=-1;break
            if hittp:exit=k;px=tp;reason=1;break
            favorable=(H[k]-fill) if di==1 else (fill-L[k])
            if favorable>maxf:maxf=favorable
            if manager==1 and maxf>=1.5*risk:
                if (di==1 and fill>stop) or (di==-1 and fill<stop):stop=fill
        r[cnt]=(di*(px-fill)-0.35)/risk
        timestamps[cnt]=TIME[j];durations[cnt]=TIME[exit]-TIME[j]
        orig[cnt]=i;ent[cnt]=j;out[cnt]=exit;why[cnt]=reason
        lock=exit;cnt+=1
    return r[:cnt],timestamps[:cnt],durations[:cnt],orig[:cnt],ent[:cnt],out[:cnt],why[:cnt]

prev_strategies=['01_PD_sweep_reclaim','03_PD_delayed_break3','07_Local15_engulf','12_FiboH1_reject','18_FVG_H1_local15_reject']
WEEKDAY=il.dt.weekday.to_numpy()
recs=[]
for name in prev_strategies:
 sb,ss=setups[name]
 for filtername in ['none','M15_align','H1_align','FVG_H1']:
    fb,fs=filters[filtername]
    buy=sb&fb&candidate_ok;sell=ss&fs&candidate_ok
    both=buy&sell;buy=buy&~both;sell=sell&~both
    idx=np.flatnonzero(buy|sell)
    if len(idx)<40:continue
    side=np.where(buy[idx],1,-1).astype(np.int8)
    for look in (5,):
        lo=sL.rolling(look,min_periods=look).min().to_numpy()[idx]
        hi=sH.rolling(look,min_periods=look).max().to_numpy()[idx]
        stop=np.where(side==1,lo-0.1*ATR[idx],hi+0.1*ATR[idx])
        for retr in (0.35,0.60):
            limit=C[idx]-side*retr*(H[idx]-L[idx])
            for tp in (3.,4.,6.):
                for manager in (0,1):
                    y,t,d,orig,ent,ex,why=limit_sim(idx.astype(np.int64),side,stop,limit,ATR[idx],tp,manager,O,H,L,C,TIME,hour,WEEKDAY)
                    rec={'family':name,'filter':filtername,'lookback_stop':look,'pullback_range_fraction':retr,'tp_R':tp,'BE_at_1p5R':bool(manager),'filled_trades':len(y),'signals':len(idx)}
                    for label,t0,t1 in periods:
                        s=score(y,t,t0,t1)
                        rec.update({label+'_'+k:v for k,v in s.items()})
                    recs.append(rec)
res=pd.DataFrame(recs)
res.to_csv(P/'limit_all_variants.csv',index=False)
chosen=[]
for name,grp in res.groupby('family'):
    q=grp[(grp.dev_2025_n>=80)&(grp.validation_2026Q1_n>=20)].copy()
    if not len(q):continue
    q['train_penalized']=q.dev_2025_avg_R-0.4*np.sqrt(80/q.dev_2025_n)
    chosen.append(q.sort_values('train_penalized',ascending=False).iloc[0])
sel=pd.DataFrame(chosen)
sel.to_csv(P/'limit_train_selected.csv',index=False)
cols=['family','filter','lookback_stop','pullback_range_fraction','tp_R','BE_at_1p5R','dev_2025_n','dev_2025_avg_R','validation_2026Q1_n','validation_2026Q1_avg_R','review_reused_2026Q2Q3_n','review_reused_2026Q2Q3_avg_R','review_reused_2026Q2Q3_coverage']
print('LIMIT variants',len(res),'selected',len(sel),'time',round(time.time()-T0,2))
print('BEST 2026 REUSED (posthoc):')
print(res[(res.dev_2025_n>=80)&(res.validation_2026Q1_n>=20)&(res.review_reused_2026Q2Q3_n>=50)].sort_values('review_reused_2026Q2Q3_avg_R',ascending=False)[cols].head(15).to_string(index=False))
print('TRAIN SELECTED:')
print(sel[cols].to_string(index=False))
good=res[(res.dev_2025_n>=50)&(res.validation_2026Q1_n>=20)&(res.review_reused_2026Q2Q3_n>=40)&(res.dev_2025_avg_R>0)&(res.validation_2026Q1_avg_R>0)&(res.review_reused_2026Q2Q3_avg_R>0)]
print('THREE PERIOD POSITIVE:',len(good));print(good[cols].head(20).to_string(index=False))
with open(P/'limit_summary.json','w') as f:json.dump({'variants':len(res),'train_selected':len(sel),'three_period_positive':len(good),'runtime_s':round(time.time()-T0,2)},f,indent=2)

# Document one retrospectively highlighted candidate; NOT a prespecified blind-validation winner.
name='01_PD_sweep_reclaim';filtername='H1_align';look=5;retr=0.35;tp=4.;manager=0
sb,ss=setups[name];fb,fs=filters[filtername]
buy=sb&fb&candidate_ok;sell=ss&fs&candidate_ok
both=buy&sell;buy=buy&~both;sell=sell&~both
idx=np.flatnonzero(buy|sell);side=np.where(buy[idx],1,-1).astype(np.int8)
lo=sL.rolling(look,min_periods=look).min().to_numpy()[idx];hi=sH.rolling(look,min_periods=look).max().to_numpy()[idx]
stop=np.where(side==1,lo-0.1*ATR[idx],hi+0.1*ATR[idx]);limit=C[idx]-side*retr*(H[idx]-L[idx])
y,t,d,orig,ent,ex,why=limit_sim(idx.astype(np.int64),side,stop,limit,ATR[idx],tp,manager,O,H,L,C,TIME,hour,WEEKDAY)
recs=[]
for j in range(len(y)):
    src_i=int(orig[j]);i=int(ent[j]);end=int(ex[j]);k=np.searchsorted(idx,src_i);di=int(side[k])
    fill=min(O[i],limit[k]) if di==1 else max(O[i],limit[k]);risk=(fill-stop[k])*di
    recs.append({'signal_close_israel':str(il.iloc[src_i]+pd.Timedelta(minutes=1)),
       'fill_israel':str(il.iloc[i]),'exit_israel':str(il.iloc[end]),
       'direction':'LONG' if di==1 else 'SHORT','signal_entry_id':src_i,
       'entry_price':fill,'structural_SL':stop[k],'take_profit':fill+di*tp*risk,
       'original_risk_price_usd':risk,'net_R':y[j],'duration_minutes':int(d[j]),
       'exit_flag':int(why[j]),'period':'2025_development' if t[j]<start('2026-01-01') else '2026Q1_validation' if t[j]<start('2026-04-01') else '2026Q2Q3_reused_review'})
log=pd.DataFrame(recs)
log.to_csv(P/'candidate_PD_H1_limit_trade_log.csv',index=False)
summary={}
for period,g in log.groupby('period'):
    r=g.net_R.to_numpy();eq=np.r_[0,np.cumsum(r)]
    summary[period]={'n':len(g),'avg_R':float(np.mean(r)),'win_rate_pct':float(np.mean(r>0)*100),
    'total_R':float(r.sum()),'max_drawdown_R':float(np.min(eq-np.maximum.accumulate(eq))),
    'max_loss_streak':int(max([sum(1 for _ in group) for val,group in __import__('itertools').groupby(r<=0) if val]+[0])),
    'median_hold_min':float(np.median(g.duration_minutes)),
    'days_traded':len(set(pd.to_datetime(g.fill_israel,utc=True).dt.tz_convert('Asia/Jerusalem').dt.date))}
with open(P/'candidate_PD_H1_summary.json','w') as f:json.dump(summary,f,indent=2)
print('PREDECLARED DAILY SWEEP + H1 CANDIDATE:');print(json.dumps(summary,indent=2))

# Reproducible sensitivity and exploratory weekly cluster bootstrap, no claim of valid CI
from itertools import groupby
x=log.copy()
sensitivity={}
for group_name,g in x.groupby('period'):
    sensitivity[group_name]={
      'meanR_fee_0_35':float(g.net_R.mean()),
      'meanR_fee_0_70':float((g.net_R-0.35/g.original_risk_price_usd).mean()),
      'meanR_fee_1_00':float((g.net_R-0.65/g.original_risk_price_usd).mean()),
      'median_stop_distance':float(g.original_risk_price_usd.median())}
review=x[x.period=='2026Q2Q3_reused_review'].copy()
review['week']=pd.to_datetime(review.fill_israel,utc=True).dt.tz_convert('Asia/Jerusalem').dt.strftime('%G-W%V')
clusters=[g.net_R.to_numpy() for _,g in review.groupby('week')]
rng=np.random.default_rng(20261014)
bootstrap=np.empty(10000)
for n in range(len(bootstrap)):
    ids=rng.integers(0,len(clusters),size=len(clusters))
    bootstrap[n]=np.concatenate([clusters[q] for q in ids]).mean()
robust={'week_clusters':len(clusters),'review_week_block_bootstrap_exploratory_CI95':np.percentile(bootstrap,[2.5,97.5]).tolist(),
'bootstrap_fraction_positive':float((bootstrap>0).mean()),'cost_sensitivity_XAUUSD_price_units':sensitivity,
'warning':'Exploratory posthoc selection, intervals not adjusted for familywise comparison; not evidence of live edge'}
(P/'candidate_cost_robustness.json').write_text(json.dumps(robust,indent=2))
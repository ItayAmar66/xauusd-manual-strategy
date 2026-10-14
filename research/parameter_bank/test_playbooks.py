#!/usr/bin/env python3
"""Exploratory full-market composites, 2026-04..09 was seen in prior research; NOT virgin holdout."""
import pandas as pd, numpy as np, json
from pathlib import Path
from numba import njit
P=Path(__file__).resolve().parent
F=pd.read_csv(P/'condition_bank_m5.csv')
from zipfile import ZipFile
local=Path('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if local.exists():
    M=pd.read_csv(local)
else:
    z=P.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
    with ZipFile(z) as archive:
        f=next(k for k in archive.namelist() if k.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
        M=pd.read_csv(archive.open(f))
assert len(M)==760337
op,hi,lo,cl=[M[x].to_numpy(float) for x in ['open','high','low','close']]
mins=M.timestamp.to_numpy(np.int64)//60000
ent=F.entry_m1_index.to_numpy(np.int64);atr=F.m5_atr14.to_numpy(float)
def B(k):return F[k].to_numpy(dtype=bool)
def E(x,y):return np.where(x&~y,1,np.where(y&~x,-1,0)).astype(np.int8)
R={}
R['R01_PDL_weekly_discount']=(B('pdl_sweep_reclaim_last60m')&B('weekly_discount')&B('m5_rejection_bull'),B('pdh_sweep_reclaim_last60m')&B('weekly_premium')&B('m5_rejection_bear'))
R['R02_daily_sweep_M15FVG']=(B('pdl_sweep_reclaim_last60m')&B('fvg_touch_M15_BULL')&B('m5_body_bull'),B('pdh_sweep_reclaim_last60m')&B('fvg_touch_M15_BEAR')&B('m5_body_bear'))
R['R03_week_sweep_H1FVG']=(B('pwl_sweep_reclaim_last60m')&B('fvg_touch_H1_BULL')&B('m5_rejection_bull'),B('pwh_sweep_reclaim_last60m')&B('fvg_touch_H1_BEAR')&B('m5_rejection_bear'))
R['R04_H1_fib_M15_trend']=(B('fib_h1_bull_618_786')&B('m15_up')&B('m5_rejection_bull'),B('fib_h1_bear_618_786')&B('m15_down')&B('m5_rejection_bear'))
R['R05_H1FVG_prior_15m_counter']=(B('fvg_touch_H1_BULL')&B('prior_15m_down')&B('m5_rejection_bull'),B('fvg_touch_H1_BEAR')&B('prior_15m_up')&B('m5_rejection_bear'))
R['R06_H4FVG_weekly_zone']=(B('fvg_touch_H4_BULL')&B('weekly_discount')&B('m5_rejection_bull'),B('fvg_touch_H4_BEAR')&B('weekly_premium')&B('m5_rejection_bear'))
R['R07_weighted_reversal']=( ((B('weekly_discount').astype(int)+B('pdl_sweep_reclaim_last60m').astype(int)+B('fvg_touch_H1_BULL').astype(int)+B('fib_h1_bull_618_786').astype(int))>=2)&B('m5_rejection_bull'),((B('weekly_premium').astype(int)+B('pdh_sweep_reclaim_last60m').astype(int)+B('fvg_touch_H1_BEAR').astype(int)+B('fib_h1_bear_618_786').astype(int))>=2)&B('m5_rejection_bear'))
R['R08_HTF_zone_FVG_rejection']=((B('weekly_discount')|B('pdl_sweep_reclaim_last60m'))&(B('fvg_touch_H1_BULL')|B('fvg_touch_H4_BULL')|B('fvg_touch_M15_BULL'))&B('m5_rejection_bull'),(B('weekly_premium')|B('pdh_sweep_reclaim_last60m'))&(B('fvg_touch_H1_BEAR')|B('fvg_touch_H4_BEAR')|B('fvg_touch_M15_BEAR'))&B('m5_rejection_bear'))
R['C01_3TF_trend_breakout']=(B('h4_up')&B('h1_up')&B('m15_up')&B('m5_breakup'),B('h4_down')&B('h1_down')&B('m15_down')&B('m5_breakdown'))
R['C02_H1trend_M5FVG']=(B('h1_up')&B('m15_up')&B('fvg_touch_M5_BULL')&B('m5_body_bull'),B('h1_down')&B('m15_down')&B('fvg_touch_M5_BEAR')&B('m5_body_bear'))
R['C03_H1_fib_trend']=(B('fib_h1_bull_618_786')&B('h1_up')&B('m5_rejection_bull'),B('fib_h1_bear_618_786')&B('h1_down')&B('m5_rejection_bear'))
R['C04_M15FVG_trend_engulf']=(B('fvg_touch_M15_BULL')&B('m15_up')&B('m5_engulf_bull'),B('fvg_touch_M15_BEAR')&B('m15_down')&B('m5_engulf_bear'))
R['C05_adaptive_trend']=( (B('h4_up')|B('h1_up'))&(B('m15_up')|B('m5_up'))&(B('m5_breakup')|B('m5_rejection_bull')), (B('h4_down')|B('h1_down'))&(B('m15_down')|B('m5_down'))&(B('m5_breakdown')|B('m5_rejection_bear')))
R['R09_weekly_extreme_RSI']=(B('weekly_rangebottom20')&B('m5_rsi_oversold')&B('m5_rejection_bull'),B('weekly_rangetop20')&B('m5_rsi_overbought')&B('m5_rejection_bear'))
R['R10_day_sweep_M15trend']=(B('pdl_sweep_reclaim_last60m')&B('m15_up')&B('m5_body_bull'),B('pdh_sweep_reclaim_last60m')&B('m15_down')&B('m5_body_bear'))
R['C06_H4H1_M15FVG_displace']=(B('h4_up')&B('h1_up')&B('fvg_touch_M15_BULL')&B('m15_displacement')&B('m5_body_bull'),B('h4_down')&B('h1_down')&B('fvg_touch_M15_BEAR')&B('m15_displacement')&B('m5_body_bear'))
@njit
def test(sig,ent,atr,op,hi,lo,cl,mins,stopmult,rr,manage):
    n=len(sig);ee=np.empty(n,np.int64);xx=np.empty(n,np.int64);sides=np.empty(n,np.int8)
    results=np.empty(n);dur=np.empty(n);reasons=np.empty(n,np.int8);cnt=0;locked=-1
    for i in range(n):
        d=sig[i];j=ent[i]
        if d==0 or j<=locked or j<0:continue
        risk=atr[i]*stopmult
        if risk<0.4 or not np.isfinite(risk):continue
        entry=op[j];stop=entry-d*risk;tp=entry+d*rr*risk;favmax=0.
        k=j;exitp=entry;why=4
        while k<len(op):
            if mins[k]-mins[j]>=120:exitp=op[k];why=0;break
            if k>j and mins[k]-mins[k-1]>1:exitp=op[k];why=3;break
            if d==1:
                if op[k]<=stop:exitp=op[k];why=-1;break
                if op[k]>=tp:exitp=tp;why=1;break
                hitstop=lo[k]<=stop;hittp=hi[k]>=tp;favorable=hi[k]-entry
            else:
                if op[k]>=stop:exitp=op[k];why=-1;break
                if op[k]<=tp:exitp=tp;why=1;break
                hitstop=hi[k]>=stop;hittp=lo[k]<=tp;favorable=entry-lo[k]
            if hitstop:exitp=stop;why=-1;break
            if hittp:exitp=tp;why=1;break
            if favorable>favmax:favmax=favorable
            candidate=stop
            if manage==1 and favmax>=1.5*risk:candidate=entry
            if manage==2 and favmax>=risk:candidate=entry+d*max(0.,(np.floor(favmax/(.5*risk))-2)*.5*risk)
            if d==1 and candidate>stop:stop=candidate
            elif d==-1 and candidate<stop:stop=candidate
            k+=1
        if k>=len(op):k=len(op)-1;exitp=cl[-1];why=4
        ee[cnt]=j;xx[cnt]=k;sides[cnt]=d;results[cnt]=d*(exitp-entry)/risk-.35/risk;dur[cnt]=mins[k]-mins[j];reasons[cnt]=why
        cnt+=1;locked=k
    return ee[:cnt],xx[:cnt],sides[:cnt],results[:cnt],dur[:cnt],reasons[:cnt]

israel=pd.to_datetime(M.timestamp,unit='ms',utc=True).dt.tz_convert('Asia/Jerusalem')
market=M.assign(day=israel.dt.date).groupby('day').agg(n=('close','size'),hi=('high','max'),lo=('low','min'))
market=market[(market.n>=200)&(market.hi>market.lo)]
marketdays=np.array([str(d) for d in market.index if pd.Timestamp(d).weekday()<5]);train=marketdays[marketdays<'2026-04-01'];review=marketdays[marketdays>='2026-04-01']
dates=np.array(israel.dt.date,dtype='U10')
def summarize(ee,r,dur,cal):
    mask=np.isin(dates[ee],cal);z=r[mask];d=dur[mask];traded=np.unique(dates[ee][mask])
    eq=np.cumsum(np.r_[0,z]);longest=0;run=0
    for v in z:
        if v<=0:run+=1;longest=max(longest,run)
        else:run=0
    return dict(n=len(z),avg_R=float(np.mean(z)) if len(z) else None,total_R=float(np.sum(z)),win_rate_pct=float(np.mean(z>0)*100) if len(z) else None,days_with_trades=len(traded),coverage_pct=float(np.isin(cal,traded).mean()*100),max_dd_R=float(np.min(eq-np.maximum.accumulate(eq))),loss_streak=longest,over_120min=int((d>120).sum()))
rows=[];trades=[]
for name,(buy,sell) in R.items():
    side=E(buy,sell)
    for stop in (1.5,2.0):
        for mode in (0,1,2):
            rr=4 if mode!=2 else 5
            e,x,s,r,d,w=test(side,ent,atr,op,hi,lo,cl,mins,stop,rr,mode)
            a=summarize(e,r,d,train);b=summarize(e,r,d,review)
            row=dict(playbook=name,stop_atr=stop,target_R=rr,management=['fixed4','be1p5_tp4','ladder0p5_tp5'][mode],long_candidate_count=int(buy.sum()),short_candidate_count=int(sell.sum()))
            row.update({'train_'+k:v for k,v in a.items()});row.update({'review_REUSED_'+k:v for k,v in b.items()});rows.append(row)
            # logs for all recipe+management combinations, allowing post-hoc audits
            for i in range(len(e)):
                trades.append((name,stop,mode,str(israel.iat[e[i]]),str(israel.iat[x[i]]),int(s[i]),round(r[i],6),int(d[i]),int(w[i]),'train' if dates[e[i]]<'2026-04-01' else 'reused_review'))
A=pd.DataFrame(rows);A.to_csv(P/'composite_prototypes_96.csv',index=False)
T=pd.DataFrame(trades,columns=['playbook','stop_atr','management_code','entry_israel','exit_israel','direction','net_R','minutes','exit_reason','sample']);T.to_csv(P/'prototype_trade_log.csv',index=False)
# Pick a fixed common configuration for transparent, NON-OPTIMIZED benchmark.
V=A[(A.stop_atr==1.5)&(A.management=='fixed4')].sort_values('review_REUSED_avg_R',ascending=False)
V.to_csv(P/'prototypes_fixed4R_comparison.csv',index=False)
print('PASS',len(R),'playbooks,',len(A),'variants',len(T),'logged trades');print(V[['playbook','train_n','train_avg_R','review_REUSED_n','review_REUSED_avg_R','review_REUSED_coverage_pct']].to_string(index=False))
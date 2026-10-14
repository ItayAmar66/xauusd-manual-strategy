#!/usr/bin/env python3
"""Reproduce 4xATR(14) M5 reversal leg catalog from archived XAUUSD M1 candles."""
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
import numpy as np
import json

HERE=Path(__file__).resolve().parent
ROOT=Path(__file__).resolve().parents[1]
ZIP=ROOT/"15M ATR/XAUUSD_Manual_Strategy_Research_Git_Import.zip"
MEMBER="research/01_reaction_zones_3x_m15_atr14/raw/xauusd-m1-bid-2025-01-01-2026-09-25.csv"
with ZipFile(ZIP) as z, z.open(MEMBER) as f:
    raw=pd.read_csv(f)
raw["dt"]=pd.to_datetime(raw.timestamp,unit="ms",utc=True)
raw=raw.set_index("dt")
m5=raw[["open","high","low","close"]].resample("5min",label="left",closed="left").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
prev=m5.close.shift()
tr=pd.concat([m5.high-m5.low,(m5.high-prev).abs(),(m5.low-prev).abs()],axis=1).max(axis=1)
m5["atr14"]=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
atr=m5.atr14.shift(1).reindex(raw.index,method="ffill").to_numpy()
hi=raw.high.to_numpy();lo=raw.low.to_numpy();times=raw.index
start=next(i for i,a in enumerate(atr) if np.isfinite(a) and a>0)
li=hi_i=start; low=lo[start];high=hi[start];state=0;pivots=[]
for i in range(start+1,len(raw)):
    a=atr[i]
    if not np.isfinite(a) or a<=0:continue
    if state==0:
        if lo[i]<low:low=lo[i];li=i
        if hi[i]>high:high=hi[i];hi_i=i
        if hi[i]-low>=4*atr[li] and li<=hi_i:
            pivots.append((li,float(low),"LOW"));state=1;high=hi[i];hi_i=i
        elif high-lo[i]>=4*atr[hi_i]:
            pivots.append((hi_i,float(high),"HIGH"));state=-1;low=lo[i];li=i
    elif state==1:
        if hi[i]>high:high=hi[i];hi_i=i
        if high-lo[i]>=4*atr[hi_i]:
            pivots.append((hi_i,float(high),"HIGH"));state=-1;low=lo[i];li=i
    else:
        if lo[i]<low:low=lo[i];li=i
        if hi[i]-low>=4*atr[li]:
            pivots.append((li,float(low),"LOW"));state=1;high=hi[i];hi_i=i
rows=[]
for (j,v,k),(z,v2,k2) in zip(pivots,pivots[1:]):
    if z<j or k==k2:raise AssertionError("non-alternating pivots")
    ratio=abs(v2-v)/atr[j]
    if ratio<4-1e-8:continue
    local=times[j]+pd.Timedelta(hours=3)
    hh=local.hour+local.minute/60
    session="London" if 9<=hh<12 else "New York" if 16.5<=hh<18.5 else "Asia" if 2<=hh<8 else "Outside"
    rows.append(dict(event_id=len(rows)+1,origin_datetime_utc=str(times[j]),end_datetime_utc=str(times[z]),date_il=str(local.date()),direction="LONG" if k=="LOW" else "SHORT",session=session,origin_price=v,end_price=v2,movement_usd=round(abs(v2-v),6),m5_atr14=float(atr[j]),movement_atr=float(ratio),duration_min=z-j,qa_flag="INTRABAR_SEQUENCE_AMBIGUOUS" if z==j else "OK"))
df=pd.DataFrame(rows)
assert df.event_id.is_unique and (df.movement_atr>=4-1e-8).all()
df.to_csv(HERE/"XAUUSD_Reversal_Legs_4ATR_M5.csv",index=False)
raw["localdate"]=(raw.index+pd.Timedelta(hours=3)).date
daily=raw.groupby("localdate").agg(bars=("high","size"),high=("high","max"),low=("low","min"))
daily=daily[(pd.to_datetime(daily.index).dayofweek<5)&(daily.high>daily.low)].copy()
origins=df.groupby("date_il").size()
daily["leg_origins"]=daily.index.astype(str).map(origins).fillna(0).astype(int)
daily.to_csv(HERE/"daily_coverage.csv")
stats=dict(m1_bars=len(raw),m5_candles=len(m5),events=len(df),threshold_atr=4,min_ratio=float(df.movement_atr.min()),ambiguous=int((df.duration_min==0).sum()),duration_1_to_120=int(df.duration_min.between(1,120).sum()),duration_gt120=int((df.duration_min>120).sum()),market_days=len(daily),days_with_new_leg=int((daily.leg_origins>0).sum()),days_without_new_leg=int((daily.leg_origins==0).sum()),sessions=df.session.value_counts().to_dict())
assert (stats["events"],stats["ambiguous"],stats["market_days"],stats["days_with_new_leg"])==(4584,291,449,447)
(HERE/"summary.json").write_text(json.dumps(stats,indent=2),encoding="utf8")
print(json.dumps(stats,indent=2))

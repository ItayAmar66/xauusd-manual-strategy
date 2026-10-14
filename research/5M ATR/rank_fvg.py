#!/usr/bin/env python3
"""Calculate FVG-at-origin frequency using original event-independent FVG lifecycle table."""
import pandas as pd, numpy as np
from pathlib import Path
from zipfile import ZipFile
p=Path(__file__).resolve().parent
zpath=p.parent/"15M ATR/XAUUSD_Manual_Strategy_Research_Git_Import.zip"
with ZipFile(zpath) as z:
    with z.open("research/01_reaction_zones_3x_m15_atr14/context/XAUUSD_FVG_Lifecycle_CloseInvalidation.csv") as f:
        fvg=pd.read_csv(f,usecols=["tf","direction","available_at","level_low","level_high","invalidated_at"])
ev=pd.read_csv(p/"XAUUSD_Reversal_Legs_4ATR_M5.csv")
fvg["a"]=pd.to_datetime(fvg.available_at,utc=True).astype("int64")//10**9
fvg["z"]=pd.to_datetime(fvg.invalidated_at,utc=True,errors="coerce").astype("int64")//10**9
fvg.loc[fvg.invalidated_at.isna(),"z"]=2**62//10**9
times=(pd.to_datetime(ev.origin_datetime_utc,utc=True).astype("int64")//10**9).to_numpy()
prices=ev.origin_price.to_numpy()
out=[]
for (tf,d),sub in fvg.groupby(["tf","direction"]):
    a=sub.a.to_numpy();z=sub.z.to_numpy();low=sub.level_low.to_numpy();high=sub.level_high.to_numpy()
    n=sum(bool(np.any((a<=t)&(z>t)&(low<=v)&(high>=v))) for t,v in zip(times,prices))
    out.append({"tf":tf,"direction":d,"events":n,"pct":round(100*n/len(ev),4)})
pd.DataFrame(out).sort_values("events",ascending=False).to_csv(p/"fvg_at_origin_ranked.csv",index=False)

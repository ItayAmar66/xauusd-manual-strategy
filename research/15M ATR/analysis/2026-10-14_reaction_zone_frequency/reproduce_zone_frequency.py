#!/usr/bin/env python3
"""Reproduce the 42 category event-frequency ranking from original CSV files."""
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]  # adjust: this file is in analysis/date/, root needs research/01...
ROOT=Path(__file__).resolve().parents[2]
N=2091
legs=pd.read_csv(ROOT/"primary/XAUUSD_Phase1_Reversal_Legs_3ATR_M15.csv")
liq=pd.read_csv(ROOT/"context/XAUUSD_Liquidity_Interactions.csv")
fvg=pd.read_csv(ROOT/"context/XAUUSD_ACTIVE_FVG_at_Origins.csv")
assert len(legs)==N and legs.event_id.is_unique and legs.movement_atr.min()>=3
liq["zone"]=liq.family+"|"+liq.level+"_"+liq.state
fvg["zone"]="ACTIVE_FVG|"+fvg.tf+"_"+fvg.direction
counts=pd.concat([liq[["event_id","zone"]],fvg[["event_id","zone"]]]).groupby("zone").event_id.nunique()
rows=[(*token.split("|",1),int(n)) for token,n in counts.items()]
df=pd.DataFrame(rows,columns=["family","zone","events"]).sort_values(["events","family","zone"],ascending=[False,True,True])
df.insert(0,"rank",range(1,len(df)+1))
df["percent_of_2091"]=df.events/N*100
out=Path(__file__).with_name("zone_interactions_ranked.csv")
existing=pd.read_csv(out)
assert len(df)==len(existing)==42
assert df[["family","zone","events"]].reset_index(drop=True).equals(existing[["family","zone","events"]])
print("PASS — 42/42 counts matched, 2091 unique event IDs")

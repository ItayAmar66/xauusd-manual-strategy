#!/usr/bin/env python3
"""Audit overlap between ALL historical 3x M15 ATR14 reversal legs."""
from pathlib import Path
import pandas as pd
P=Path(__file__).resolve().parents[2]/"primary/XAUUSD_Phase1_Reversal_Legs_3ATR_M15.csv"
d=pd.read_csv(P)
assert len(d)==2091 and d.event_id.is_unique
d["start"]=pd.to_datetime(d.origin_datetime_utc,errors="raise")
d["end"]=pd.to_datetime(d.end_datetime_utc,errors="raise")
d=d.sort_values(["start","end","event_id"]).reset_index(drop=True)
invalid=(d.end<d.start).sum()
zero=(d.end==d.start)
previous_end=d.end.shift()
gap_minutes=(d.start-previous_end).dt.total_seconds()/60
strict_overlapping_adjacencies=int((gap_minutes<0).sum())
# By definition, non-overlapping sorted intervals have no strict pair overlaps when all start >= max prior end.
max_earlier_end=d.end.cummax().shift()
strict_overlap_any=int((d.start<max_earlier_end).sum())
touch=int((gap_minutes==0).sum())
separated=int((gap_minutes>0).sum())
matched_prices=int(((gap_minutes==0) & (d.origin_price==d.end_price.shift())).sum())
assert strict_overlap_any==0 and strict_overlapping_adjacencies==0
assert int(zero.sum())==26 and int(d.loc[zero,"qa_flag"].eq("INTRABAR_SEQUENCE_AMBIGUOUS").sum())==26
assert touch==1998 and separated==92 and matched_prices==1992
print({"count":len(d),"strict_overlap_intervals":strict_overlap_any,"touching_adjacent_pairs":touch,"gapped_adjacent_pairs":separated,"touching_with_same_price":matched_prices,"zero_duration_events":int(zero.sum()),"negative_duration_events":int(invalid)})
d.loc[zero,["event_id","origin_datetime_utc","end_datetime_utc","direction","origin_price","end_price","movement_atr","qa_flag"]].to_csv(Path(__file__).with_name("zero_duration_26.csv"),index=False)

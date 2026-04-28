# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


RAW_PATH    = os.path.join(PROJECT_ROOT, "data", "dynamic_supply_chain_logistics_dataset.csv")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "ops_data_real.csv")


def adapt():
    df = pd.read_csv(RAW_PATH)
    print(f"Raw dataset: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")

    # parse timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # assign week number from start of data
    start_date   = df["timestamp"].min()
    df["week"]   = ((df["timestamp"] - start_date).dt.days // 7 + 1).clip(upper=12)
    df["date"]   = df["timestamp"].dt.strftime("%Y-%m-%d")

    # assign operation units based on route_risk_level or congestion
    def assign_unit(row):
        if "traffic_congestion_level" in df.columns:
            val = row.get("traffic_congestion_level", 0)
            if val >= 0.7:   return "Warehouse A"
            elif val >= 0.4: return "Warehouse B"
            else:            return "Support Team"
        return "Warehouse A"

    df["operation_unit"] = df.apply(assign_unit, axis=1)

    # assign process stage based on lead time
    def assign_stage(row):
        lt = row.get("lead_time_days", 5)
        if lt <= 2:   return "order_processing"
        elif lt <= 4: return "packaging"
        elif lt <= 7: return "shipping"
        else:         return "delivery"

    df["process_stage"] = df.apply(assign_stage, axis=1)

    # map columns to our schema
    df["orders_processed"]    = 100  # normalize — each row = 1 order unit
    df["orders_delayed"]      = (df["delay_probability"] > 0.5).astype(int) * 100 if "delay_probability" in df.columns else 10
    df["defects_count"]       = (df["cargo_condition_status"].astype(str).str.lower() == "damaged").astype(int) * 100 if "cargo_condition_status" in df.columns else 5
    df["avg_processing_time"] = df["loading_unloading_time"] if "loading_unloading_time" in df.columns else df["lead_time_days"]
    df["customer_complaints"] = (df["eta_variation_hours"].abs() > 2).astype(int) * 100 if "eta_variation_hours" in df.columns else 10
    df["cost_per_order"]      = df["shipping_costs"] if "shipping_costs" in df.columns else 12.0
    df["region"]              = df["operation_unit"].map({
        "Warehouse A": "North",
        "Warehouse B": "South",
        "Support Team": "West"
    })

    # aggregate to week + unit + stage level
    agg = df.groupby(["week", "date", "operation_unit", "process_stage", "region"]).agg(
        orders_processed   =("orders_processed",    "count"),
        orders_delayed     =("orders_delayed",       "sum"),
        defects_count      =("defects_count",        "sum"),
        avg_processing_time=("avg_processing_time",  "mean"),
        customer_complaints=("customer_complaints",  "sum"),
        cost_per_order     =("cost_per_order",       "mean"),
    ).reset_index()

    # keep only weeks 1-12
    agg = agg[agg["week"] <= 12].copy()

    # use first date of each week
    agg["date"] = agg.groupby("week")["date"].transform("first")

    # round
    agg["avg_processing_time"] = agg["avg_processing_time"].round(2)
    agg["cost_per_order"]      = agg["cost_per_order"].round(2)

    agg.to_csv(OUTPUT_PATH, index=False)
    print(f"\nAdapted dataset saved: {OUTPUT_PATH}")
    print(f"Shape: {agg.shape}")
    print(f"Weeks: {agg['week'].nunique()}")
    print(f"Units: {agg['operation_unit'].unique()}")
    print(f"Stages: {agg['process_stage'].unique()}")
    print(f"\nSample:")
    print(agg.head(5).to_string())


if __name__ == "__main__":
    adapt()
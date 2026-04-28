# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH  = os.path.join(PROJECT_ROOT, "data", "ops_data_simulated.csv")

UNITS   = ["Warehouse A", "Warehouse B", "Support Team"]
STAGES  = ["order_processing", "packaging", "shipping", "delivery"]
REGIONS = {"Warehouse A": "North", "Warehouse B": "South", "Support Team": "West"}

START_DATE = datetime(2024, 1, 1)
WEEKS      = 12


def main():
    np.random.seed(42)
    rows = []

    for week in range(1, WEEKS + 1):
        date = START_DATE + timedelta(weeks=week - 1)

        for unit in UNITS:
            orders_processed    = int(np.random.normal(1000, 50))
            base_delay_rate     = 0.05
            base_defect_rate    = 0.02
            base_complaint_rate = 0.02
            base_proc_time      = {"order_processing": 2.0, "packaging": 3.0,
                                   "shipping": 4.0, "delivery": 5.0}
            base_cost           = 12.0

            if unit == "Warehouse A" and week in [5, 6]:
                base_proc_time["packaging"] *= 1.20
            if unit == "Warehouse A" and week in [7, 8]:
                base_proc_time["packaging"] *= 1.35
                base_delay_rate = 0.15
            if unit == "Warehouse A" and week in [9, 10]:
                base_proc_time["packaging"] *= 1.35
                base_delay_rate     = 0.18
                base_complaint_rate = 0.12
                base_cost           = 14.5
            if unit == "Warehouse B" and week in [11, 12]:
                base_delay_rate     = 0.10
                base_complaint_rate = 0.07
                base_cost           = 13.5

            orders_delayed      = int(orders_processed * base_delay_rate
                                      * np.random.uniform(0.9, 1.1))
            defects_count       = int(orders_processed * base_defect_rate
                                      * np.random.uniform(0.85, 1.15))
            customer_complaints = int(orders_processed * base_complaint_rate
                                      * np.random.uniform(0.9, 1.1))
            cost_per_order      = round(base_cost * np.random.uniform(0.97, 1.03), 2)

            for stage in STAGES:
                avg_proc_time = round(
                    base_proc_time[stage] * np.random.uniform(0.95, 1.05), 2)
                rows.append({
                    "week":                week,
                    "date":                date.strftime("%Y-%m-%d"),
                    "operation_unit":      unit,
                    "process_stage":       stage,
                    "orders_processed":    orders_processed,
                    "orders_delayed":      orders_delayed,
                    "defects_count":       defects_count,
                    "avg_processing_time": avg_proc_time,
                    "customer_complaints": customer_complaints,
                    "cost_per_order":      cost_per_order,
                    "region":              REGIONS[unit],
                })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Dataset created: {OUTPUT_PATH}")
    print(f"Shape: {df.shape}")
    print(f"Weeks: {df['week'].nunique()}  |  "
          f"Units: {df['operation_unit'].nunique()}  |  "
          f"Stages: {df['process_stage'].nunique()}")


if __name__ == "__main__":
    main()
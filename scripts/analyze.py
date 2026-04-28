# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH    = os.path.join(PROJECT_ROOT, "data", "ops_data_simulated.csv")

BASELINE_WEEKS = [1, 2, 3, 4]
CURRENT_WEEKS  = [9, 10, 11, 12]

IMPACT_WEIGHTS = {
    "delay_rate":          9,
    "complaint_rate":      8,
    "cost_per_order":      7,
    "avg_processing_time": 6,
    "defect_rate":         5,
    "throughput":          4,
}


# ── 1. LOAD & KPI CALCULATION ─────────────────────────────────────
def load_and_calculate_kpis():
    df = pd.read_csv(DATA_PATH)

    unit_week = df.groupby(["week", "operation_unit", "region"]).agg(
        orders_processed   =("orders_processed",   "first"),
        orders_delayed     =("orders_delayed",      "first"),
        defects_count      =("defects_count",       "first"),
        customer_complaints=("customer_complaints", "first"),
        cost_per_order     =("cost_per_order",      "first"),
    ).reset_index()

    unit_week["delay_rate"]     = (unit_week["orders_delayed"]      / unit_week["orders_processed"] * 100).round(2)
    unit_week["defect_rate"]    = (unit_week["defects_count"]       / unit_week["orders_processed"] * 100).round(2)
    unit_week["complaint_rate"] = (unit_week["customer_complaints"] / unit_week["orders_processed"] * 100).round(2)

    stage_week = df.groupby(["week", "operation_unit", "process_stage"]).agg(
        avg_processing_time=("avg_processing_time", "mean")
    ).reset_index()

    return unit_week, stage_week


# ── 2. BASELINE COMPARISON ────────────────────────────────────────
def calculate_baseline(unit_week):
    baseline = unit_week[unit_week["week"].isin(BASELINE_WEEKS)].groupby("operation_unit").agg(
        baseline_delay     =("delay_rate",     "mean"),
        baseline_complaint =("complaint_rate", "mean"),
        baseline_cost      =("cost_per_order", "mean"),
        baseline_throughput=("orders_processed","mean"),
    ).reset_index()

    current = unit_week[unit_week["week"].isin(CURRENT_WEEKS)].groupby("operation_unit").agg(
        current_delay     =("delay_rate",     "mean"),
        current_complaint =("complaint_rate", "mean"),
        current_cost      =("cost_per_order", "mean"),
        current_throughput=("orders_processed","mean"),
    ).reset_index()

    comp = baseline.merge(current, on="operation_unit")
    comp["delay_change"]     = ((comp["current_delay"]     - comp["baseline_delay"])     / comp["baseline_delay"]     * 100).round(1)
    comp["complaint_change"] = ((comp["current_complaint"] - comp["baseline_complaint"]) / comp["baseline_complaint"] * 100).round(1)
    comp["cost_change"]      = ((comp["current_cost"]      - comp["baseline_cost"])      / comp["baseline_cost"]      * 100).round(1)

    result = []
    for _, row in comp.iterrows():
        result.append({
            "unit":                row["operation_unit"],
            "baseline_delay":      round(row["baseline_delay"],     1),
            "current_delay":       round(row["current_delay"],      1),
            "delay_change":        row["delay_change"],
            "baseline_complaint":  round(row["baseline_complaint"], 1),
            "current_complaint":   round(row["current_complaint"],  1),
            "complaint_change":    row["complaint_change"],
            "baseline_cost":       round(row["baseline_cost"],      2),
            "current_cost":        round(row["current_cost"],       2),
            "cost_change":         row["cost_change"],
        })
    return result


# ── 3. PROBLEM DETECTION ──────────────────────────────────────────
def detect_problems(unit_week, stage_week):
    detected = []

    for unit in unit_week["operation_unit"].unique():
        data = unit_week[unit_week["operation_unit"] == unit].sort_values("week")

        for i in range(1, len(data)):
            prev = data.iloc[i - 1]
            curr = data.iloc[i]

            # Delay Spike
            delay_change = curr["delay_rate"] - prev["delay_rate"]
            if delay_change > 5:
                detected.append({
                    "problem_type":    "Delay Spike",
                    "unit":            unit,
                    "stage":           "multi-stage",
                    "week_detected":   int(curr["week"]),
                    "value_before":    f"{prev['delay_rate']:.1f}%",
                    "value_after":     f"{curr['delay_rate']:.1f}%",
                    "change":          f"+{delay_change:.1f} pp",
                    "metric":          "delay_rate",
                    "pct_change":      (delay_change / max(prev["delay_rate"], 0.1)) * 100,
                    "orders_affected": int(curr["orders_processed"]),
                })

            # Complaint Surge
            complaint_change = curr["complaint_rate"] - prev["complaint_rate"]
            if complaint_change > 8:
                detected.append({
                    "problem_type":    "Complaint Surge",
                    "unit":            unit,
                    "stage":           "customer-facing",
                    "week_detected":   int(curr["week"]),
                    "value_before":    f"{prev['complaint_rate']:.1f}%",
                    "value_after":     f"{curr['complaint_rate']:.1f}%",
                    "change":          f"+{complaint_change:.1f} pp",
                    "metric":          "complaint_rate",
                    "pct_change":      (complaint_change / max(prev["complaint_rate"], 0.1)) * 100,
                    "orders_affected": int(curr["orders_processed"]),
                })

            # Cost Increase Without Volume
            cost_pct = (curr["cost_per_order"] - prev["cost_per_order"]) / prev["cost_per_order"] * 100
            vol_pct  = (curr["orders_processed"] - prev["orders_processed"]) / prev["orders_processed"] * 100
            if cost_pct > 10 and vol_pct < 5:
                detected.append({
                    "problem_type":    "Cost Increase",
                    "unit":            unit,
                    "stage":           "operations",
                    "week_detected":   int(curr["week"]),
                    "value_before":    f"${prev['cost_per_order']:.2f}",
                    "value_after":     f"${curr['cost_per_order']:.2f}",
                    "change":          f"+{cost_pct:.1f}%",
                    "metric":          "cost_per_order",
                    "pct_change":      cost_pct,
                    "orders_affected": int(curr["orders_processed"]),
                })

    # Processing Time Surge
    for unit in stage_week["operation_unit"].unique():
        for stage in stage_week["process_stage"].unique():
            stage_data = stage_week[
                (stage_week["operation_unit"] == unit) &
                (stage_week["process_stage"]  == stage)
            ].sort_values("week")

            for i in range(1, len(stage_data)):
                prev = stage_data.iloc[i - 1]
                curr = stage_data.iloc[i]
                pct  = (curr["avg_processing_time"] - prev["avg_processing_time"]) / prev["avg_processing_time"] * 100
                if pct > 15:
                    orders = int(unit_week[
                        (unit_week["operation_unit"] == unit) &
                        (unit_week["week"] == int(curr["week"]))
                    ]["orders_processed"].values[0])
                    detected.append({
                        "problem_type":    "Processing Time Surge",
                        "unit":            unit,
                        "stage":           stage,
                        "week_detected":   int(curr["week"]),
                        "value_before":    f"{prev['avg_processing_time']:.2f}h",
                        "value_after":     f"{curr['avg_processing_time']:.2f}h",
                        "change":          f"+{pct:.1f}%",
                        "metric":          "avg_processing_time",
                        "pct_change":      pct,
                        "orders_affected": orders,
                    })

    return detected


# ── 4. SEVERITY SCORING ───────────────────────────────────────────
def magnitude_score(pct_change):
    if pct_change >= 50:   return 10
    elif pct_change >= 30: return 8
    elif pct_change >= 20: return 6
    elif pct_change >= 10: return 4
    else:                  return 2


def severity_label(score):
    if score >= 500:    return "CRITICAL"
    elif score >= 300:  return "HIGH"
    elif score >= 150:  return "MEDIUM"
    else:               return "LOW"


def score_problems(detected):
    for p in detected:
        mag    = magnitude_score(abs(p["pct_change"]))
        weight = IMPACT_WEIGHTS.get(p["metric"], 5)
        vol    = min(p["orders_affected"] / 100, 10)
        p["severity_score"] = round(mag * weight * vol, 1)
        p["severity_label"] = severity_label(p["severity_score"])

    return sorted(detected, key=lambda x: x["severity_score"], reverse=True)


# ── 5. ROOT CAUSE CHAIN ───────────────────────────────────────────
def build_root_cause_chain(detected):
    chain      = sorted(detected, key=lambda x: x["week_detected"])
    first_week = chain[0]["week_detected"] if chain else 1

    result = []
    for i, p in enumerate(chain, 1):
        lag = p["week_detected"] - first_week
        result.append({
            "sequence": i,
            "week":     p["week_detected"],
            "event":    f"{p['problem_type']} — {p['unit']} ({p['stage']}): {p['value_before']} -> {p['value_after']}",
            "metric":   p["metric"],
            "lag":      "Root cause" if lag == 0 else f"{lag} weeks after root cause",
        })
    return result


# ── 6. KPI SUMMARY STRING ─────────────────────────────────────────
def build_kpi_summary(unit_week):
    lines = []
    for unit in unit_week["operation_unit"].unique():
        data   = unit_week[unit_week["operation_unit"] == unit]
        latest = data[data["week"].isin(CURRENT_WEEKS)]
        lines.append(
            f"{unit}: Delay rate avg {latest['delay_rate'].mean():.1f}% "
            f"(peak {latest['delay_rate'].max():.1f}%), "
            f"complaint rate avg {latest['complaint_rate'].mean():.1f}%, "
            f"cost per order avg ${latest['cost_per_order'].mean():.2f}"
        )
    return " | ".join(lines)


# ── 7. PRINT REPORT ───────────────────────────────────────────────
def print_report(unit_week, baseline_comparison, detected, root_chain):
    print("\n-- BASELINE vs CURRENT --")
    for row in baseline_comparison:
        print(f"\n  {row['unit']}:")
        print(f"    Delay      : {row['baseline_delay']:.1f}% -> {row['current_delay']:.1f}%  ({row['delay_change']:+.1f}%)")
        print(f"    Complaints : {row['baseline_complaint']:.1f}% -> {row['current_complaint']:.1f}%  ({row['complaint_change']:+.1f}%)")
        print(f"    Cost/Order : ${row['baseline_cost']:.2f} -> ${row['current_cost']:.2f}  ({row['cost_change']:+.1f}%)")

    print(f"\n-- DETECTED PROBLEMS: {len(detected)} --")
    for p in detected:
        print(f"  Week {p['week_detected']} | {p['problem_type']:<25} | {p['unit']:<15} | {p['stage']:<20} | {p['value_before']} -> {p['value_after']}")

    print(f"\n-- SEVERITY RANKING --")
    print(f"{'Rank':<5} {'Problem':<25} {'Unit':<15} {'Severity':<10} {'Score'}")
    print("-" * 70)
    for i, p in enumerate(detected, 1):
        print(f"{i:<5} {p['problem_type']:<25} {p['unit']:<15} {p['severity_label']:<10} {p['severity_score']}")

    print(f"\n-- ROOT CAUSE CHAIN --")
    for p in root_chain:
        print(f"  [{p['sequence']}] Week {p['week']} | {p['event']} | {p['lag']}")


# ── MAIN (run standalone) ─────────────────────────────────────────
def run_analysis():
    print("Loading data and calculating KPIs...")
    unit_week, stage_week = load_and_calculate_kpis()

    print("Calculating baseline comparison...")
    baseline_comparison = calculate_baseline(unit_week)

    print("Detecting problems...")
    detected = detect_problems(unit_week, stage_week)

    print("Scoring severity...")
    detected = score_problems(detected)

    print("Building root cause chain...")
    root_chain = build_root_cause_chain(detected)

    kpi_summary = build_kpi_summary(unit_week)

    print_report(unit_week, baseline_comparison, detected, root_chain)

    return unit_week, stage_week, detected, baseline_comparison, root_chain, kpi_summary


if __name__ == "__main__":
    run_analysis()
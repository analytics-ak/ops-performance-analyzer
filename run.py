# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from generate_data   import main as run_generate_data
from analyze         import run_analysis
from ai_insights     import get_ai_insights, parse_sections
from generate_report import generate_all_charts, generate_pdf
from send_email      import send_report

print("=" * 55)
print("  OPS PERFORMANCE ANALYZER — PIPELINE START")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 55)

# ── STEP 1 — GENERATE DATA ────────────────────────────────────────
print("\n[1/5] Generating simulated dataset...")
run_generate_data()

# ── STEP 2 — ANALYZE ──────────────────────────────────────────────
print("\n[2/5] Running analysis...")
unit_week, stage_week, detected, baseline_comparison, root_chain, kpi_summary = run_analysis()

# ── STEP 3 — AI INSIGHTS ──────────────────────────────────────────
print("\n[3/5] Calling AI for insights...")
raw_response = get_ai_insights(
    kpi_summary         = kpi_summary,
    detected_problems   = detected,
    root_cause_chain    = root_chain,
    baseline_comparison = baseline_comparison,
)
ai_sections = parse_sections(raw_response)
print("AI sections parsed:")
for key, val in ai_sections.items():
    status = "OK" if val.strip() else "EMPTY"
    print(f"  {key:<25} : {status} ({len(val)} chars)")

# ── STEP 4 — GENERATE REPORT ──────────────────────────────────────
print("\n[4/5] Generating charts and PDF report...")
generate_all_charts(detected)
output_path = generate_pdf(detected, ai_sections, baseline_comparison)

# ── STEP 5 — SEND EMAIL ───────────────────────────────────────────
print("\n[5/5] Sending report via email...")
send_report(output_path, detected, baseline_comparison)

# ── DONE ──────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  PIPELINE COMPLETE")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  Report: {output_path}")
print("=" * 55)
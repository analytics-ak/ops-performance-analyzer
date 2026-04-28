# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import analyze

# point to real dataset
analyze.DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "ops_data_real.csv"
)

unit_week, stage_week = analyze.load_and_calculate_kpis()
baseline   = analyze.calculate_baseline(unit_week)
detected   = analyze.detect_problems(unit_week, stage_week)
detected   = analyze.score_problems(detected)
chain      = analyze.build_root_cause_chain(detected)

print(f"Real dataset — Problems detected: {len(detected)}")
for p in detected[:5]:
    print(f"  {p['problem_type']} | {p['unit']} | Week {p['week_detected']} | {p['severity_label']}")
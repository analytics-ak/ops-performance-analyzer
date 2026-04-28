# -*- coding: utf-8 -*-
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def get_ai_insights(kpi_summary, detected_problems, root_cause_chain,
                    baseline_comparison):

    ranked_issues = "\n".join([
        f"  Rank {i+1}: {p['problem_type']} | {p['unit']} | {p['stage']} | "
        f"{p['value_before']} -> {p['value_after']} | "
        f"Severity: {p['severity_label']} (Score: {p['severity_score']})"
        for i, p in enumerate(detected_problems)
    ])

    chain_text = "\n".join([
        f"  [{p['sequence']}] Week {p['week']} | {p['event']} | "
        f"Lag: {p.get('lag', 'Root cause')}"
        for p in root_cause_chain
    ])

    baseline_text = "\n".join([
        f"  {row['unit']}: Delay {row['baseline_delay']:.1f}% -> {row['current_delay']:.1f}% "
        f"({row['delay_change']:+.1f}%) | "
        f"Complaints {row['baseline_complaint']:.1f}% -> {row['current_complaint']:.1f}% "
        f"({row['complaint_change']:+.1f}%) | "
        f"Cost ${row['baseline_cost']:.2f} -> ${row['current_cost']:.2f} "
        f"({row['cost_change']:+.1f}%)"
        for row in baseline_comparison
    ])

    prompt = f"""You are a senior operations performance analyst reviewing weekly data.

Do not describe the data. Diagnose it.

BASELINE vs CURRENT PERFORMANCE (Weeks 1-4 baseline vs Weeks 9-12 current):
{baseline_text}

DETECTED ISSUES (ranked by severity score):
{ranked_issues}

ROOT CAUSE CHAIN (ordered by week of first detection):
{chain_text}

KPI SUMMARY:
{kpi_summary}

Your task:
1. Identify the FIRST problem that occurred and explain why it is the root cause
2. Explain exactly how it propagated across stages and units with specific numbers
3. Identify which issue currently has the highest business impact and quantify it
4. Give 3 to 5 specific recommended actions in priority order — most urgent first

Strict rules:
- Use only the numbers provided — do not invent figures
- Be specific — name the unit, stage, week, and metric in every statement
- Write the Executive Summary as one clear paragraph, no bullet points
- Use these exact section headers: EXECUTIVE SUMMARY, ROOT CAUSE ANALYSIS, IMPACT ANALYSIS, RECOMMENDED ACTIONS, DECISION PRIORITY TABLE
- In DECISION PRIORITY TABLE, format as: Action | Urgency (High/Medium/Low) | Estimated Impact
- Never use generic statements like 'it is important to monitor' — be specific and actionable"""

    print("Calling Claude API...")
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    print("AI response received.")
    return message.content[0].text


def parse_sections(response_text):
    sections = {
        "executive_summary":   "",
        "root_cause_analysis": "",
        "impact_analysis":     "",
        "recommended_actions": "",
        "decision_priority":   "",
    }

    section_map = {
        "EXECUTIVE SUMMARY":       "executive_summary",
        "ROOT CAUSE ANALYSIS":     "root_cause_analysis",
        "IMPACT ANALYSIS":         "impact_analysis",
        "RECOMMENDED ACTIONS":     "recommended_actions",
        "DECISION PRIORITY TABLE": "decision_priority",
        "DECISION PRIORITY":       "decision_priority",
        "PRIORITY TABLE":          "decision_priority",
    }

    current_section = None
    lines = response_text.split("\n")

    for line in lines:
        matched = False
        for header, key in section_map.items():
            if header in line.upper():
                current_section = key
                matched = True
                break
        if not matched and current_section:
            sections[current_section] += line + "\n"

    for key in sections:
        sections[key] = sections[key].strip()

    return sections


if __name__ == "__main__":
    sample_problems = [
        {
            "problem_type": "Delay Spike", "unit": "Warehouse A",
            "stage": "multi-stage", "week_detected": 7,
            "value_before": "4.9%", "value_after": "13.6%",
            "severity_label": "CRITICAL", "severity_score": 855.0
        },
        {
            "problem_type": "Complaint Surge", "unit": "Warehouse A",
            "stage": "customer-facing", "week_detected": 9,
            "value_before": "2.0%", "value_after": "12.9%",
            "severity_label": "CRITICAL", "severity_score": 764.0
        },
        {
            "problem_type": "Processing Time Surge", "unit": "Warehouse A",
            "stage": "packaging", "week_detected": 5,
            "value_before": "2.99h", "value_after": "3.49h",
            "severity_label": "MEDIUM", "severity_score": 230.2
        },
    ]

    sample_chain = [
        {"sequence": 1, "week": 5,
         "event": "Packaging processing time increased 17% in Warehouse A",
         "lag": "Root cause"},
        {"sequence": 2, "week": 7,
         "event": "Delay rate spiked from 4.9% to 13.6% in Warehouse A",
         "lag": "2 weeks after root cause"},
        {"sequence": 3, "week": 9,
         "event": "Customer complaints surged from 2.0% to 12.9%, cost rose to $14.61",
         "lag": "4 weeks after root cause"},
        {"sequence": 4, "week": 11,
         "event": "Delay and complaint rates increased in Warehouse B",
         "lag": "6 weeks after root cause"},
    ]

    sample_baseline = [
        {
            "unit": "Warehouse A",
            "baseline_delay": 4.9,  "current_delay": 12.2,  "delay_change": 150.4,
            "baseline_complaint": 1.9, "current_complaint": 7.0, "complaint_change": 267.2,
            "baseline_cost": 11.87, "current_cost": 13.13, "cost_change": 10.6,
        },
        {
            "unit": "Warehouse B",
            "baseline_delay": 4.9,  "current_delay": 7.1,   "delay_change": 44.3,
            "baseline_complaint": 1.9, "current_complaint": 4.6, "complaint_change": 141.0,
            "baseline_cost": 11.99, "current_cost": 12.72, "cost_change": 6.1,
        },
    ]

    kpi_summary = (
        "Warehouse A: Delay rate peaked at 19.7% (week 9), complaint rate 12.9%, "
        "cost per order $14.61. Warehouse B: Delay rate 9.3% (week 12), "
        "complaint rate 7.4%, cost $13.67. Support Team: Stable throughout."
    )

    response = get_ai_insights(kpi_summary, sample_problems,
                               sample_chain, sample_baseline)
    print("\n-- AI RESPONSE --")
    print(response)

    sections = parse_sections(response)
    print("\n-- PARSED SECTIONS --")
    for key, val in sections.items():
        print(f"\n[{key.upper()}]")
        print(val[:300] + "..." if len(val) > 300 else val)
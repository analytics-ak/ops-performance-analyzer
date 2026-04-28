# -*- coding: utf-8 -*-
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings("ignore")

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import Flowable
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH    = os.path.join(PROJECT_ROOT, "data", "ops_data_simulated.csv")
CHARTS_DIR   = os.path.join(PROJECT_ROOT, "charts")
OUTPUT_DIR   = os.path.join(PROJECT_ROOT, "output")
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── CHART PALETTE ─────────────────────────────────────────────────
SAPPHIRE   = "#0F52BA"
GOLD       = "#D4AF37"
DANGER_RED = "#C0392B"
SUCCESS    = "#27AE60"
NEUTRAL    = "#7F8C8D"
LIGHT_BG   = "#F8F9FA"
DARK_TEXT  = "#2C3E50"

# ── PDF PALETTE ───────────────────────────────────────────────────
PDF_SAPPHIRE   = colors.HexColor("#0F52BA")
PDF_DARK_NAVY  = colors.HexColor("#1A2340")
PDF_GOLD       = colors.HexColor("#D4AF37")
PDF_LIGHT_GREY = colors.HexColor("#F4F6FB")
PDF_MID_GREY   = colors.HexColor("#7F8C8D")
PDF_WHITE      = colors.white
PDF_BLACK      = colors.HexColor("#1C1C1E")
PDF_RED        = colors.HexColor("#C0392B")
PDF_GREEN      = colors.HexColor("#27AE60")
PDF_BORDER     = colors.HexColor("#DDE3F0")


# ══════════════════════════════════════════════════════════════════
# CHART FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def set_style(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=14, fontweight="bold",
                 color=DARK_TEXT, pad=16)
    ax.set_xlabel(xlabel, fontsize=10, color=NEUTRAL, labelpad=10)
    ax.set_ylabel(ylabel, fontsize=10, color=NEUTRAL, labelpad=10)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#DDE3F0")
    ax.spines["bottom"].set_color("#DDE3F0")
    ax.tick_params(colors=NEUTRAL, labelsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.5, color="#DDE3F0")
    ax.set_axisbelow(True)
    ax.set_facecolor(LIGHT_BG)


def load_data():
    df = pd.read_csv(DATA_PATH)
    unit_week = df.groupby(["week", "operation_unit"]).agg(
        orders_processed   =("orders_processed",   "first"),
        orders_delayed     =("orders_delayed",      "first"),
        customer_complaints=("customer_complaints", "first"),
        cost_per_order     =("cost_per_order",      "first"),
    ).reset_index()
    unit_week["delay_rate"]     = (unit_week["orders_delayed"]      / unit_week["orders_processed"] * 100).round(2)
    unit_week["complaint_rate"] = (unit_week["customer_complaints"] / unit_week["orders_processed"] * 100).round(2)

    stage_week = df.groupby(["week", "operation_unit", "process_stage"]).agg(
        avg_processing_time=("avg_processing_time", "mean")
    ).reset_index()

    return unit_week, stage_week


def chart1_delay_rate_trend(unit_week):
    fig, ax = plt.subplots(figsize=(12, 5), facecolor="white")
    unit_colors = {"Warehouse A": DANGER_RED, "Warehouse B": SAPPHIRE, "Support Team": SUCCESS}
    for unit, color in unit_colors.items():
        data = unit_week[unit_week["operation_unit"] == unit]
        ax.plot(data["week"], data["delay_rate"], marker="o",
                color=color, linewidth=2, markersize=5, label=unit)
    wa   = unit_week[unit_week["operation_unit"] == "Warehouse A"]
    peak = wa.loc[wa["delay_rate"].idxmax()]
    ax.annotate(f"Peak: {peak['delay_rate']:.1f}%\n(Week {int(peak['week'])})",
                xy=(peak["week"], peak["delay_rate"]),
                xytext=(peak["week"] - 2, peak["delay_rate"] + 1.5),
                fontsize=8, color=DANGER_RED, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=DANGER_RED, lw=1.2))
    ax.axvspan(4.5, 6.5, alpha=0.08, color=GOLD,       label="Packaging slowdown")
    ax.axvspan(6.5, 8.5, alpha=0.08, color=DANGER_RED, label="Delay spike")
    set_style(ax, "DELAY RATE TREND — 12 WEEKS", "Week", "Delay Rate (%)")
    ax.set_xticks(range(1, 13))
    ax.legend(fontsize=9, framealpha=0.8)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "delay_rate_trend.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: delay_rate_trend.png")


def chart2_processing_time_by_stage(stage_week):
    wa  = stage_week[stage_week["operation_unit"] == "Warehouse A"]
    fig, ax = plt.subplots(figsize=(12, 5), facecolor="white")
    stage_colors = {
        "order_processing": SAPPHIRE,
        "packaging":        GOLD,
        "shipping":         SUCCESS,
        "delivery":         NEUTRAL,
    }
    for stage, color in stage_colors.items():
        data = wa[wa["process_stage"] == stage]
        lw   = 2.5 if stage == "packaging" else 1.5
        ax.plot(data["week"], data["avg_processing_time"],
                marker="o", color=color, linewidth=lw,
                markersize=5 if stage == "packaging" else 4,
                label=stage.replace("_", " ").title(),
                zorder=5 if stage == "packaging" else 3)
    ax.axvspan(4.5, 8.5, alpha=0.08, color=GOLD)
    pkg_peak = wa[wa["process_stage"] == "packaging"]["avg_processing_time"].max()
    ax.annotate("Packaging surge\nbegins Week 5",
                xy=(5, pkg_peak),
                xytext=(6.5, pkg_peak + 0.1),
                fontsize=8, color=GOLD, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=GOLD, lw=1.2))
    set_style(ax, "AVG PROCESSING TIME BY STAGE — WAREHOUSE A", "Week", "Avg Time (hours)")
    ax.set_xticks(range(1, 13))
    ax.legend(fontsize=9, framealpha=0.8)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "processing_time_by_stage.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: processing_time_by_stage.png")


def chart3_complaint_trend(unit_week):
    fig, ax = plt.subplots(figsize=(12, 5), facecolor="white")
    unit_colors = {"Warehouse A": DANGER_RED, "Warehouse B": SAPPHIRE, "Support Team": SUCCESS}
    for unit, color in unit_colors.items():
        data = unit_week[unit_week["operation_unit"] == unit]
        ax.plot(data["week"], data["complaint_rate"], marker="o",
                color=color, linewidth=2, markersize=5, label=unit)
    wa   = unit_week[unit_week["operation_unit"] == "Warehouse A"]
    peak = wa.loc[wa["complaint_rate"].idxmax()]
    ax.annotate(f"Peak: {peak['complaint_rate']:.1f}%\n(Week {int(peak['week'])})",
                xy=(peak["week"], peak["complaint_rate"]),
                xytext=(peak["week"] - 2.5, peak["complaint_rate"] + 0.5),
                fontsize=8, color=DANGER_RED, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=DANGER_RED, lw=1.2))
    ax.axvspan(8.5, 10.5, alpha=0.08, color=DANGER_RED, label="Complaint surge")
    set_style(ax, "COMPLAINT RATE TREND — LAG EFFECT VISIBLE", "Week", "Complaint Rate (%)")
    ax.set_xticks(range(1, 13))
    ax.legend(fontsize=9, framealpha=0.8)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "complaint_trend.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: complaint_trend.png")


def chart4_cost_trend(unit_week):
    fig, ax = plt.subplots(figsize=(12, 5), facecolor="white")
    unit_colors = {"Warehouse A": DANGER_RED, "Warehouse B": SAPPHIRE, "Support Team": SUCCESS}
    for unit, color in unit_colors.items():
        data = unit_week[unit_week["operation_unit"] == unit]
        ax.plot(data["week"], data["cost_per_order"], marker="o",
                color=color, linewidth=2, markersize=5, label=unit)
    wa   = unit_week[unit_week["operation_unit"] == "Warehouse A"]
    peak = wa.loc[wa["cost_per_order"].idxmax()]
    ax.annotate(f"Peak: ${peak['cost_per_order']:.2f}\n(Week {int(peak['week'])})",
                xy=(peak["week"], peak["cost_per_order"]),
                xytext=(peak["week"] - 2.5, peak["cost_per_order"] + 0.15),
                fontsize=8, color=DANGER_RED, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=DANGER_RED, lw=1.2))
    set_style(ax, "COST PER ORDER TREND", "Week", "Cost Per Order ($)")
    ax.set_xticks(range(1, 13))
    ax.legend(fontsize=9, framealpha=0.8)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "cost_per_order_trend.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: cost_per_order_trend.png")


def chart5_unit_comparison(unit_week):
    BASELINE_WKS = [1, 2, 3, 4]
    CURRENT_WKS  = [9, 10, 11, 12]
    baseline = unit_week[unit_week["week"].isin(BASELINE_WKS)].groupby("operation_unit").agg(
        delay_rate    =("delay_rate",     "mean"),
        complaint_rate=("complaint_rate", "mean"),
        cost_per_order=("cost_per_order", "mean"),
    ).reset_index()
    current = unit_week[unit_week["week"].isin(CURRENT_WKS)].groupby("operation_unit").agg(
        delay_rate    =("delay_rate",     "mean"),
        complaint_rate=("complaint_rate", "mean"),
        cost_per_order=("cost_per_order", "mean"),
    ).reset_index()
    units   = baseline["operation_unit"].tolist()
    x       = range(len(units))
    width   = 0.35
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), facecolor="white")
    metrics = [
        ("delay_rate",     "Delay Rate (%)",     "DELAY RATE"),
        ("complaint_rate", "Complaint Rate (%)", "COMPLAINT RATE"),
        ("cost_per_order", "Cost Per Order ($)", "COST PER ORDER"),
    ]
    for ax, (metric, ylabel, title) in zip(axes, metrics):
        b_vals = baseline[metric].tolist()
        c_vals = current[metric].tolist()
        bars1 = ax.bar([i - width/2 for i in x], b_vals, width,
                       label="Baseline", color=SAPPHIRE, alpha=0.7)
        bars2 = ax.bar([i + width/2 for i in x], c_vals, width,
                       label="Current",  color=DANGER_RED, alpha=0.85)
        for bar in bars1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f"{bar.get_height():.1f}", ha="center", fontsize=7, color=DARK_TEXT)
        for bar in bars2:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f"{bar.get_height():.1f}", ha="center", fontsize=7, color=DARK_TEXT)
        ax.set_xticks(list(x))
        ax.set_xticklabels([u.replace(" ", "\n") for u in units], fontsize=8)
        set_style(ax, title, "", ylabel)
        ax.legend(fontsize=8)
    fig.suptitle("UNIT COMPARISON — BASELINE vs CURRENT",
                 fontsize=14, fontweight="bold", color=DARK_TEXT, y=1.02)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "unit_comparison.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: unit_comparison.png")


def chart6_severity_ranking(detected_problems):
    if not detected_problems:
        print("No problems to chart")
        return
    labels     = [f"{p['problem_type']}\n{p['unit']}" for p in detected_problems]
    scores     = [p["severity_score"] for p in detected_problems]
    colors_map = {"CRITICAL": DANGER_RED, "HIGH": "#E67E22", "MEDIUM": GOLD, "LOW": SUCCESS}
    bar_colors = [colors_map.get(p["severity_label"], NEUTRAL) for p in detected_problems]
    fig, ax    = plt.subplots(figsize=(12, 6), facecolor="white")
    bars       = ax.barh(labels[::-1], scores[::-1], color=bar_colors[::-1],
                         alpha=0.88, height=0.6)
    for bar, p in zip(bars, detected_problems[::-1]):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                f"{p['severity_label']}  {p['severity_score']}",
                va="center", fontsize=9, fontweight="bold",
                color=colors_map.get(p["severity_label"], NEUTRAL))
    legend_patches = [
        mpatches.Patch(color=DANGER_RED, label="CRITICAL"),
        mpatches.Patch(color="#E67E22",  label="HIGH"),
        mpatches.Patch(color=GOLD,       label="MEDIUM"),
        mpatches.Patch(color=SUCCESS,    label="LOW"),
    ]
    ax.legend(handles=legend_patches, fontsize=9, loc="lower right")
    set_style(ax, "DETECTED ISSUES RANKED BY SEVERITY SCORE", "Severity Score", "")
    ax.grid(axis="x", linestyle=":", alpha=0.5, color="#DDE3F0")
    ax.grid(axis="y", visible=False)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "severity_ranking.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: severity_ranking.png")


def generate_all_charts(detected_problems):
    print("\nGenerating charts...")
    unit_week, stage_week = load_data()
    chart1_delay_rate_trend(unit_week)
    chart2_processing_time_by_stage(stage_week)
    chart3_complaint_trend(unit_week)
    chart4_cost_trend(unit_week)
    chart5_unit_comparison(unit_week)
    chart6_severity_ranking(detected_problems)
    print("All 6 charts saved to charts/")


# ══════════════════════════════════════════════════════════════════
# PDF FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def get_styles():
    return {
        "cover_title": ParagraphStyle(
            "cover_title", fontName="Helvetica-Bold", fontSize=28,
            textColor=PDF_WHITE, alignment=TA_CENTER, leading=36
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", fontName="Helvetica", fontSize=12,
            textColor=colors.HexColor("#BDD0F5"), alignment=TA_CENTER, leading=18
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=10,
            textColor=PDF_BLACK, leading=16, spaceAfter=6
        ),
        "sub_title": ParagraphStyle(
            "sub_title", fontName="Helvetica-Bold", fontSize=12,
            textColor=PDF_DARK_NAVY, spaceBefore=10, spaceAfter=6
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Helvetica", fontSize=8,
            textColor=PDF_MID_GREY, alignment=TA_CENTER
        ),
    }


def sp(n=1):
    return Spacer(1, n * 0.3 * cm)


def divider():
    return HRFlowable(width="100%", thickness=0.5,
                      color=PDF_BORDER, spaceAfter=6, spaceBefore=6)


def color_bar(text, W, bg=None):
    bg = bg or PDF_SAPPHIRE

    class Bar(Flowable):
        def __init__(self):
            Flowable.__init__(self)
            self.width  = W
            self.height = 1.1 * cm

        def draw(self):
            self.canv.setFillColor(bg)
            self.canv.roundRect(0, 0, W, 0.85 * cm, 4, fill=1, stroke=0)
            self.canv.setFillColor(PDF_WHITE)
            self.canv.setFont("Helvetica-Bold", 12)
            self.canv.drawString(0.4 * cm, 0.25 * cm, text)

    return Bar()


def make_table(headers, rows, col_widths, header_bg=None):
    header_bg = header_bg or PDF_SAPPHIRE
    data = [[Paragraph(f"<b>{h}</b>", ParagraphStyle(
        "th", fontName="Helvetica-Bold", fontSize=9,
        textColor=PDF_WHITE, leading=12)) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(cell), ParagraphStyle(
            "td", fontName="Helvetica", fontSize=9,
            textColor=PDF_BLACK, leading=13)) for cell in row])
    style = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  header_bg),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [PDF_WHITE, PDF_LIGHT_GREY]),
        ("GRID",          (0, 0), (-1, -1), 0.4, PDF_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ])
    return Table(data, colWidths=col_widths, style=style,
                 repeatRows=1, hAlign="LEFT")


def add_chart(path, W, height=7*cm):
    if os.path.exists(path):
        return Image(path, width=W, height=height)
    return Paragraph(f"Chart not found: {path}", get_styles()["body"])


def clean_ai_text(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*',     r'\1', text)
    text = re.sub(r'#{1,6}\s*',     '',    text)
    text = re.sub(r'\|.+\|',        '',    text)
    text = re.sub(r'\n{3,}',        '\n\n', text)
    return text.strip()


def generate_pdf(detected_problems, ai_sections, baseline_comparison,
                 output_path=None):
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, "Operations_Report.pdf")

    S = get_styles()
    W = A4[0] - 4 * cm

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="Operations Performance Report"
    )

    story = []

    # PAGE 1 — COVER
    cover = Table([[Paragraph("", S["body"])]],
                  colWidths=[W], rowHeights=[25*cm])
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PDF_DARK_NAVY),
        ("GRID",       (0,0), (-1,-1), 0, PDF_DARK_NAVY),
    ]))
    story.append(cover)
    story.append(Spacer(1, -25.5*cm))
    story.append(sp(4))
    story.append(Paragraph("OPERATIONS PERFORMANCE REPORT", S["cover_title"]))
    story.append(sp(1))
    story.append(HRFlowable(width="50%", thickness=1.5, color=PDF_GOLD,
                            hAlign="CENTER", spaceAfter=10, spaceBefore=6))
    story.append(Paragraph("AI-Powered Issue Detection & Root Cause Analysis", S["cover_sub"]))
    story.append(sp(1))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", S["cover_sub"]))
    story.append(sp(1))
    story.append(Paragraph(
        "Data: ops_data_simulated.csv  |  Weeks 1-12  |  3 Units  |  4 Stages",
        S["cover_sub"]))
    story.append(sp(3))
    sev_counts = {}
    for p in detected_problems:
        sev_counts[p["severity_label"]] = sev_counts.get(p["severity_label"], 0) + 1
    summary_text = "  |  ".join([f"{v} {k}" for k, v in sev_counts.items()])
    story.append(Paragraph(f"Issues Detected: {summary_text}", ParagraphStyle(
        "badge", fontName="Helvetica-Bold", fontSize=11,
        textColor=PDF_GOLD, alignment=TA_CENTER)))
    story.append(PageBreak())

    # PAGE 2 — EXECUTIVE SUMMARY + BASELINE TABLE
    story.append(color_bar("01 — EXECUTIVE SUMMARY", W))
    story.append(sp(1))
    exec_text = clean_ai_text(ai_sections.get("executive_summary", ""))
    for para in exec_text.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), S["body"]))
            story.append(sp(0.5))
    story.append(sp(1))
    story.append(color_bar("02 — BASELINE vs CURRENT PERFORMANCE", W))
    story.append(sp(1))
    headers = ["Unit", "Base Delay", "Curr Delay", "Change",
               "Base Complaints", "Curr Complaints", "Change"]
    rows = []
    for row in baseline_comparison:
        rows.append([
            row["unit"],
            f"{row['baseline_delay']:.1f}%",
            f"{row['current_delay']:.1f}%",
            f"{row['delay_change']:+.1f}%",
            f"{row['baseline_complaint']:.1f}%",
            f"{row['current_complaint']:.1f}%",
            f"{row['complaint_change']:+.1f}%",
        ])
    story.append(make_table(headers, rows,
                            [3.5*cm, 2*cm, 2*cm, 1.8*cm, 2.8*cm, 2.8*cm, 1.6*cm]))
    story.append(PageBreak())

    # PAGE 3 — RANKED ISSUES + SEVERITY CHART
    story.append(color_bar("03 — TOP ISSUES RANKED BY SEVERITY", W, bg=PDF_DARK_NAVY))
    story.append(sp(1))
    headers = ["Rank", "Problem", "Unit", "Stage", "Before", "After", "Severity", "Score"]
    rows = []
    for i, p in enumerate(detected_problems, 1):
        rows.append([
            str(i),
            p["problem_type"],
            p["unit"],
            p.get("stage", "—"),
            p.get("value_before", "—"),
            p.get("value_after",  "—"),
            p["severity_label"],
            str(p["severity_score"]),
        ])
    story.append(make_table(headers, rows,
                            [1*cm, 3.5*cm, 3*cm, 2.5*cm, 1.8*cm, 1.8*cm, 2*cm, 1.4*cm]))
    story.append(sp(1))
    story.append(color_bar("04 — SEVERITY RANKING CHART", W))
    story.append(sp(1))
    story.append(add_chart(os.path.join(CHARTS_DIR, "severity_ranking.png"), W, 9*cm))
    story.append(PageBreak())

    # PAGE 4 — DELAY + PROCESSING TIME
    story.append(color_bar("05 — DELAY RATE TREND", W))
    story.append(sp(1))
    story.append(add_chart(os.path.join(CHARTS_DIR, "delay_rate_trend.png"), W, 8*cm))
    story.append(sp(1))
    story.append(color_bar("06 — PROCESSING TIME BY STAGE", W))
    story.append(sp(1))
    story.append(add_chart(os.path.join(CHARTS_DIR, "processing_time_by_stage.png"), W, 8*cm))
    story.append(PageBreak())

    # PAGE 5 — COMPLAINT + COST
    story.append(color_bar("07 — COMPLAINT RATE TREND", W))
    story.append(sp(1))
    story.append(add_chart(os.path.join(CHARTS_DIR, "complaint_trend.png"), W, 8*cm))
    story.append(sp(1))
    story.append(color_bar("08 — COST PER ORDER TREND", W))
    story.append(sp(1))
    story.append(add_chart(os.path.join(CHARTS_DIR, "cost_per_order_trend.png"), W, 8*cm))
    story.append(PageBreak())

    # PAGE 6 — UNIT COMPARISON
    story.append(color_bar("09 — UNIT COMPARISON — BASELINE vs CURRENT", W))
    story.append(sp(1))
    story.append(add_chart(os.path.join(CHARTS_DIR, "unit_comparison.png"), W, 10*cm))
    story.append(PageBreak())

    # PAGE 7 — ROOT CAUSE ANALYSIS
    story.append(color_bar("10 — ROOT CAUSE ANALYSIS", W, bg=PDF_DARK_NAVY))
    story.append(sp(1))
    rca_text = clean_ai_text(ai_sections.get("root_cause_analysis", ""))
    for para in rca_text.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), S["body"]))
            story.append(sp(0.5))
    story.append(PageBreak())

    # PAGE 8 — IMPACT ANALYSIS
    story.append(color_bar("11 — IMPACT ANALYSIS", W))
    story.append(sp(1))
    impact_text = clean_ai_text(ai_sections.get("impact_analysis", ""))
    for para in impact_text.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), S["body"]))
            story.append(sp(0.5))
    story.append(PageBreak())

    # PAGE 9 — RECOMMENDED ACTIONS
    story.append(color_bar("12 — RECOMMENDED ACTIONS", W, bg=PDF_DARK_NAVY))
    story.append(sp(1))
    actions_text = clean_ai_text(ai_sections.get("recommended_actions", ""))
    for para in actions_text.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), S["body"]))
            story.append(sp(0.5))
    story.append(PageBreak())

    # PAGE 10 — DECISION PRIORITY + FOOTER
    story.append(color_bar("13 — DECISION PRIORITY TABLE", W, bg=PDF_GOLD))
    story.append(sp(1))
    priority_text = clean_ai_text(ai_sections.get("decision_priority", ""))
    for para in priority_text.split("\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), S["body"]))
            story.append(sp(0.3))
    story.append(sp(2))
    story.append(divider())
    story.append(sp(1))
    story.append(Paragraph(
        "AI narrative generated by Claude (Anthropic) using structured operational data. "
        "Detection logic is rule-based with severity scoring. "
        "Baseline: Weeks 1-4. Current: Weeks 9-12.",
        S["footer"]))

    doc.build(story)
    print(f"\nPDF saved: {output_path}")
    return output_path


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sample_problems = [
        {"problem_type": "Delay Spike",          "unit": "Warehouse A",
         "stage": "multi-stage",     "value_before": "4.9%",   "value_after": "13.6%",
         "severity_label": "CRITICAL", "severity_score": 855.0},
        {"problem_type": "Complaint Surge",       "unit": "Warehouse A",
         "stage": "customer-facing", "value_before": "2.0%",   "value_after": "12.9%",
         "severity_label": "CRITICAL", "severity_score": 764.0},
        {"problem_type": "Delay Spike",           "unit": "Warehouse A",
         "stage": "multi-stage",     "value_before": "14.5%",  "value_after": "19.7%",
         "severity_label": "CRITICAL", "severity_score": 687.6},
        {"problem_type": "Cost Increase",         "unit": "Warehouse B",
         "stage": "operations",      "value_before": "$12.15", "value_after": "$13.39",
         "severity_label": "MEDIUM",   "severity_score": 280.0},
        {"problem_type": "Cost Increase",         "unit": "Warehouse A",
         "stage": "operations",      "value_before": "$12.29", "value_after": "$14.61",
         "severity_label": "MEDIUM",   "severity_score": 267.4},
        {"problem_type": "Processing Time Surge", "unit": "Warehouse A",
         "stage": "packaging",       "value_before": "2.99h",  "value_after": "3.49h",
         "severity_label": "MEDIUM",   "severity_score": 230.2},
    ]

    sample_baseline = [
        {"unit": "Warehouse A",  "baseline_delay": 4.9, "current_delay": 12.2,
         "delay_change": 150.4,  "baseline_complaint": 1.9, "current_complaint": 7.0,
         "complaint_change": 267.2, "baseline_cost": 11.87, "current_cost": 13.13,
         "cost_change": 10.6},
        {"unit": "Warehouse B",  "baseline_delay": 4.9, "current_delay": 7.1,
         "delay_change": 44.3,   "baseline_complaint": 1.9, "current_complaint": 4.6,
         "complaint_change": 141.0, "baseline_cost": 11.99, "current_cost": 12.72,
         "cost_change": 6.1},
        {"unit": "Support Team", "baseline_delay": 4.9, "current_delay": 4.8,
         "delay_change": -2.9,   "baseline_complaint": 2.0, "current_complaint": 1.9,
         "complaint_change": -1.3, "baseline_cost": 11.80, "current_cost": 12.06,
         "cost_change": 2.2},
    ]

    sample_ai_sections = {
        "executive_summary": "Warehouse A experienced a packaging processing time surge in Week 5, increasing from 2.99 hours to 3.49 hours (17% deterioration), which triggered a cascading operational failure. This bottleneck caused Warehouse A delay rate to spike from 4.9% to 13.6% by Week 7, peaking at 19.7% in Week 9, simultaneously driving customer complaints from 2.0% to 12.9% and costs to $14.61 per order. The contagion spread to Warehouse B by Week 11, elevating its delay rate to 9.3% and complaint rate to 7.4% by Week 12.",
        "root_cause_analysis": "The originating failure occurred in Week 5 within Warehouse A packaging stage, where processing time increased from 2.99 hours to 3.49 hours — a 17% deterioration. This packaging bottleneck is the root cause because it precedes all downstream failures by at least 2 weeks and directly constrains throughput capacity. The 0.50 hour processing time increase translates to approximately 20% reduced daily throughput capacity, creating queue accumulation that no existing system buffer could absorb.",
        "impact_analysis": "The complaint surge in Warehouse A carries the highest current business impact with Severity Score 764.0, manifesting as a 12.9% complaint rate in Week 9 — 545% above the 2.0% baseline. The cost impact reached $14.61 per order in Week 9, a $2.74 premium above the $11.87 baseline (23.1% increase). Warehouse B mirrors a delayed trajectory with 7.1% delays and 4.6% complaints in Weeks 9-12, suggesting crisis propagation that has not yet resolved.",
        "recommended_actions": "1. Deploy temporary packaging capacity surge in Warehouse A within 48 hours — add second shift staff to reduce the 3.49 hour processing time back toward the 2.99 hour baseline.\n\n2. Implement order volume redistribution protocol immediately — reduce Warehouse A allocation by 25-30% and divert volume to allow packaging queue to clear.\n\n3. Execute root cause investigation within 5 business days — conduct time-motion study and equipment audit in Warehouse A packaging stage.\n\n4. Establish customer recovery program for complaint population by end of week.\n\n5. Install real-time packaging stage monitoring with 4-hour alert thresholds.",
        "decision_priority": "Action 1 — Deploy packaging capacity surge | Urgency: High | Impact: Resolves root bottleneck\nAction 2 — Redistribute order volume | Urgency: High | Impact: Prevents Warehouse B escalation\nAction 3 — Root cause investigation | Urgency: Medium | Impact: Prevents recurrence\nAction 4 — Customer recovery program | Urgency: Medium | Impact: Reduces churn risk\nAction 5 — Install monitoring alerts | Urgency: Low | Impact: Early warning system",
    }

    generate_all_charts(sample_problems)
    generate_pdf(sample_problems, sample_ai_sections, sample_baseline)
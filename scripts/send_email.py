# -*- coding: utf-8 -*-
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SENDER    = os.getenv("GMAIL_SENDER")
PASSWORD  = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT = os.getenv("GMAIL_RECIPIENT")


def send_report(pdf_path, detected_problems, baseline_comparison):
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        return False

    # ── BUILD EMAIL ───────────────────────────────────────────────
    msg = MIMEMultipart()
    msg["From"]    = SENDER
    msg["To"]      = RECIPIENT
    msg["Subject"] = f"Operations Performance Report — {datetime.now().strftime('%B %d, %Y')}"

    # count critical issues
    critical_count = sum(1 for p in detected_problems if p["severity_label"] == "CRITICAL")
    medium_count   = sum(1 for p in detected_problems if p["severity_label"] == "MEDIUM")

    # find worst unit
    worst = max(baseline_comparison, key=lambda x: x["delay_change"])

    body = f"""Dear Team,

Please find attached the automated Operations Performance Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}.

SUMMARY
-------
Total Issues Detected : {len(detected_problems)}
Critical              : {critical_count}
Medium                : {medium_count}
Worst Performing Unit : {worst['unit']} (Delay rate +{worst['delay_change']:.1f}% vs baseline)

The full analysis including root cause identification, impact assessment, and prioritised recommended actions is available in the attached PDF report.

This report was generated automatically by the Ops Performance Analyzer pipeline.

Regards,
Analytics System
Skillwalo.com
"""

    msg.attach(MIMEText(body, "plain"))

    # ── ATTACH PDF ────────────────────────────────────────────────
    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename=Operations_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
    )
    msg.attach(part)

    # ── SEND ──────────────────────────────────────────────────────
    try:
        print(f"Sending report to {RECIPIENT}...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER, PASSWORD)
            server.sendmail(SENDER, RECIPIENT, msg.as_string())
        print(f"Report sent successfully to {RECIPIENT}")
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False


if __name__ == "__main__":
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(PROJECT_ROOT, "output", "Operations_Report.pdf")

    sample_problems = [
        {"severity_label": "CRITICAL"},
        {"severity_label": "CRITICAL"},
        {"severity_label": "MEDIUM"},
    ]
    sample_baseline = [
        {"unit": "Warehouse A", "delay_change": 150.4},
        {"unit": "Warehouse B", "delay_change": 44.3},
        {"unit": "Support Team", "delay_change": -2.9},
    ]

    send_report(pdf_path, sample_problems, sample_baseline)
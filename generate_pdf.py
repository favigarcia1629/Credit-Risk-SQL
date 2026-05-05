"""
Generates a professional PDF report for the Credit Risk SQL Analysis.
Usage: python generate_pdf.py
"""
import sqlite3
import os
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUTPUT  = Path(__file__).parent / "exports" / "Credit_Risk_SQL_Report.pdf"
DB_PATH = Path(__file__).parent / "credit_risk.db"

RED    = colors.HexColor("#E74C3C")
BLUE   = colors.HexColor("#3498DB")
GREEN  = colors.HexColor("#27AE60")
DARK   = colors.HexColor("#1A1A2E")
ACCENT = colors.HexColor("#0D47A1")
LIGHT  = colors.HexColor("#F5F5F5")
GOLD   = colors.HexColor("#F39C12")
GRAY   = colors.HexColor("#888888")


def build_styles():
    S = {}
    S["cover_title"] = ParagraphStyle(
        "cover_title", fontSize=24, fontName="Helvetica-Bold",
        textColor=DARK, alignment=TA_CENTER, spaceAfter=8, leading=30,
    )
    S["cover_sub"] = ParagraphStyle(
        "cover_sub", fontSize=12, fontName="Helvetica",
        textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceAfter=4,
    )
    S["cover_date"] = ParagraphStyle(
        "cover_date", fontSize=10, fontName="Helvetica",
        textColor=GRAY, alignment=TA_CENTER,
    )
    S["section_header"] = ParagraphStyle(
        "section_header", fontSize=16, fontName="Helvetica-Bold",
        textColor=ACCENT, spaceBefore=18, spaceAfter=6, leading=20,
    )
    S["sub_header"] = ParagraphStyle(
        "sub_header", fontSize=12, fontName="Helvetica-Bold",
        textColor=DARK, spaceBefore=12, spaceAfter=4,
    )
    S["body"] = ParagraphStyle(
        "body", fontSize=10, fontName="Helvetica",
        textColor=colors.HexColor("#222222"), leading=16,
        alignment=TA_JUSTIFY, spaceAfter=6,
    )
    S["linkedin"] = ParagraphStyle(
        "linkedin", fontSize=10.5, fontName="Helvetica",
        textColor=colors.HexColor("#1a1a1a"), leading=17,
        alignment=TA_LEFT, spaceAfter=6, leftIndent=12, rightIndent=12,
    )
    S["caption"] = ParagraphStyle(
        "caption", fontSize=8.5, fontName="Helvetica-Oblique",
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=8,
    )
    S["disclaimer"] = ParagraphStyle(
        "disclaimer", fontSize=8, fontName="Helvetica-Oblique",
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=4,
    )
    return S


def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM loans", conn)
    df["annual_income"] = np.exp(df["log_annual_inc"]).round(2)

    kpis = {
        "total_loans":    len(df),
        "total_defaults": int(df["not_fully_paid"].sum()),
        "default_rate":   df["not_fully_paid"].mean() * 100,
        "avg_fico":       df["fico"].mean(),
        "avg_rate":       df["int_rate"].mean() * 100,
        "avg_dti":        df["dti"].mean(),
        "avg_income":     df["annual_income"].mean(),
    }

    q1 = pd.read_sql_query("""
        SELECT purpose,
               COUNT(*) AS total_loans,
               ROUND(AVG(not_fully_paid)*100,1) AS default_rate_pct,
               ROUND(AVG(int_rate)*100,1) AS avg_rate_pct
        FROM loans GROUP BY purpose ORDER BY default_rate_pct DESC
    """, conn)

    q2 = pd.read_sql_query("""
        SELECT
            CASE WHEN fico>=750 THEN '750+ Excellent'
                 WHEN fico>=700 THEN '700-749 Good'
                 WHEN fico>=650 THEN '650-699 Fair'
                 ELSE '600-649 Poor' END AS fico_bucket,
            CASE WHEN fico>=750 THEN 1 WHEN fico>=700 THEN 2
                 WHEN fico>=650 THEN 3 ELSE 4 END AS sort_order,
            COUNT(*) AS loans,
            ROUND(AVG(not_fully_paid)*100,1) AS default_rate_pct,
            ROUND(AVG(int_rate)*100,1) AS avg_rate_pct
        FROM loans GROUP BY fico_bucket, sort_order ORDER BY sort_order
    """, conn)

    conn.close()
    return kpis, q1, q2


def build_pdf():
    os.makedirs(OUTPUT.parent, exist_ok=True)
    print("Loading data...")
    kpis, q1, q2 = load_data()

    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=letter,
        rightMargin=0.75*inch, leftMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch,
    )
    S = build_styles()
    story = []

    # ── COVER ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("Credit Risk SQL Analysis", S["cover_title"]))
    story.append(Paragraph("Who Defaults — and Why?", S["cover_title"]))
    story.append(Spacer(1, 0.1*inch))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "A SQL-driven analysis of 9,578 personal loans from LendingClub",
        S["cover_date"]
    ))
    story.append(Paragraph(
        f"Generated {date.today().strftime('%B %d, %Y')}",
        S["cover_date"]
    ))
    story.append(Spacer(1, 0.4*inch))

    # KPI summary box
    kpi_data = [[
        Paragraph(
            f"<b>{kpis['total_loans']:,} Loans</b>  |  "
            f"<b>{kpis['default_rate']:.1f}% Default Rate</b>  |  "
            f"<b>Avg FICO {kpis['avg_fico']:.0f}</b>  |  "
            f"<b>Avg Rate {kpis['avg_rate']:.1f}%</b>",
            ParagraphStyle("kpi", fontSize=12, fontName="Helvetica-Bold",
                           textColor=colors.white, alignment=TA_CENTER)
        )
    ]]
    kpi_box = Table(kpi_data, colWidths=[6.5*inch])
    kpi_box.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), ACCENT),
        ("TOPPADDING",    (0,0),(-1,-1), 14),
        ("BOTTOMPADDING", (0,0),(-1,-1), 14),
    ]))
    story.append(kpi_box)
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(
        "The bank charges higher rates to riskier borrowers — but the spread is too narrow. "
        "Borrowers with a 32% default rate pay only ~3% more than the safest tier.",
        S["cover_sub"]
    ))

    story.append(PageBreak())

    # ── SECTION 1: LinkedIn Post ──────────────────────────────────────────────
    story.append(Paragraph("Section 1 — LinkedIn Post Draft", S["section_header"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 0.1*inch))

    linkedin_lines = [
        "16% of loans in this dataset defaulted.",
        "",
        "I wanted to understand why — so I built a SQL pipeline to find out.",
        "",
        "9,578 LendingClub personal loans. 14 variables. 9 SQL queries.",
        "Here's what the data actually shows:",
        "",
        "1. LOAN PURPOSE is the biggest single predictor of default:",
        "   Small business:  27.8% default rate",
        "   Educational:     20.1% default rate",
        "   Major purchase:  11.2% default rate",
        "   Credit card:     11.6% default rate",
        "",
        "2. FICO score creates a 4x difference in outcomes:",
        "   600-649 (Poor):      32.0% default rate",
        "   700-749 (Good):      14.5% default rate",
        "   750+ (Excellent):     7.4% default rate",
        "",
        "3. The bank is underpricing risk for low-FICO borrowers:",
        "   Poor FICO borrowers pay ~15% interest.",
        "   Excellent FICO borrowers pay ~9% interest.",
        "   A 6% rate spread for a 4x difference in default probability",
        "   is not nearly enough to compensate for the risk.",
        "",
        "4. Loans outside the bank's credit policy default at nearly",
        "   double the rate of compliant loans — validating the policy.",
        "",
        "5. Payment burden matters:",
        "   $800+/month payments: 24.3% default rate",
        "   Under $200/month:     14.8% default rate",
        "",
        "The finding that stands out most: the bank knows who is risky",
        "(they charge higher rates), but they're not charging ENOUGH.",
        "The pricing doesn't fully reflect the underlying default probability.",
        "",
        "Full Tableau dashboard + SQL code in the comments.",
        "",
        "#SQL #DataAnalysis #CreditRisk #Finance #Tableau #Python",
    ]

    for line in linkedin_lines:
        if line == "":
            story.append(Spacer(1, 0.07*inch))
        else:
            story.append(Paragraph(line, S["linkedin"]))

    story.append(PageBreak())

    # ── SECTION 2: Thought Process ────────────────────────────────────────────
    story.append(Paragraph("Section 2 — Project Thought Process", S["section_header"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 0.08*inch))

    story.append(Paragraph("The Question", S["sub_header"]))
    story.append(Paragraph(
        "Lenders face a fundamental challenge: they must decide who to lend to and at what rate "
        "before knowing who will default. This project uses a real LendingClub dataset to reverse-engineer "
        "that problem — starting from the outcome (default vs. repaid) and working backwards to identify "
        "which borrower characteristics were most predictive. The central question is whether the interest "
        "rates charged actually reflect the underlying risk.",
        S["body"]
    ))

    story.append(Paragraph("Why SQL?", S["sub_header"]))
    story.append(Paragraph(
        "SQL is the language of the lending industry. Risk analysts, credit officers, and data teams "
        "all work with relational databases. This project demonstrates the ability to answer real business "
        "questions — default rates by segment, risk pricing analysis, policy compliance — using the same "
        "tools a bank would use. The pipeline goes from raw CSV → SQLite → 9 analytical queries → "
        "Tableau dashboard, mimicking a real production workflow.",
        S["body"]
    ))

    story.append(Paragraph("Key Business Questions Answered", S["sub_header"]))
    questions = [
        ["#", "Business Question", "Query"],
        ["1", "Which loan types are riskiest?",                    "Default rate by purpose"],
        ["2", "How does credit score predict default?",            "FICO bucket risk profile"],
        ["3", "Which borrowers combine multiple risk factors?",    "High-risk borrower filter"],
        ["4", "Is the bank pricing risk correctly?",               "Rate vs. outcome comparison"],
        ["5", "Does payment burden predict default?",              "Installment bucket analysis"],
        ["6", "What are the portfolio-level KPIs?",                "Executive summary"],
        ["7", "Does income level correlate with default?",         "Income decile analysis"],
        ["8", "Does credit policy compliance matter?",             "Policy vs. default rate"],
        ["9", "What does the full loan-level data show?",          "Scatter / filter base table"],
    ]
    qt = Table(questions, colWidths=[0.3*inch, 3.2*inch, 3.0*inch])
    qt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  ACCENT),
        ("TEXTCOLOR",     (0,0),(-1,0),  colors.white),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 9),
        ("ALIGN",         (0,0),(-1,-1), "LEFT"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [LIGHT, colors.white]),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
    ]))
    story.append(qt)

    story.append(PageBreak())

    # ── SECTION 3: Key Findings ───────────────────────────────────────────────
    story.append(Paragraph("Section 3 — Key Findings", S["section_header"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 0.08*inch))

    story.append(Paragraph("Finding 1 — Default Rate by Loan Purpose", S["sub_header"]))
    purpose_data = [["Purpose", "Total Loans", "Default Rate", "Avg Rate"]]
    for _, row in q1.iterrows():
        purpose_data.append([
            row["purpose"].replace("_", " ").title(),
            f"{int(row['total_loans']):,}",
            f"{row['default_rate_pct']}%",
            f"{row['avg_rate_pct']}%",
        ])
    pt = Table(purpose_data, colWidths=[2.2*inch, 1.4*inch, 1.4*inch, 1.5*inch])
    pt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  ACCENT),
        ("TEXTCOLOR",     (0,0),(-1,0),  colors.white),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 9),
        ("ALIGN",         (1,0),(-1,-1), "CENTER"),
        ("ALIGN",         (0,0),(0,-1),  "LEFT"),
        ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [LIGHT, colors.white]),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        # Highlight top row (highest risk)
        ("BACKGROUND",    (0,1),(-1,1),  colors.HexColor("#FDECEA")),
        ("TEXTCOLOR",     (2,1),(2,1),   RED),
        ("FONTNAME",      (0,1),(-1,1),  "Helvetica-Bold"),
    ]))
    story.append(pt)
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph(
        "Small business loans default at 27.8% — 2.5x the rate of major purchases. "
        "Yet the average interest rate difference between these two categories is only ~2.4%. "
        "This is the clearest example of underpriced risk in the portfolio.",
        S["body"]
    ))

    story.append(Paragraph("Finding 2 — FICO Score Risk Tiers", S["sub_header"]))
    fico_data = [["FICO Tier", "Loans", "Default Rate", "Avg Interest Rate"]]
    for _, row in q2.iterrows():
        fico_data.append([
            row["fico_bucket"],
            f"{int(row['loans']):,}",
            f"{row['default_rate_pct']}%",
            f"{row['avg_rate_pct']}%",
        ])
    ft = Table(fico_data, colWidths=[2.2*inch, 1.4*inch, 1.4*inch, 2.0*inch])
    ft.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  ACCENT),
        ("TEXTCOLOR",     (0,0),(-1,0),  colors.white),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 9),
        ("ALIGN",         (1,0),(-1,-1), "CENTER"),
        ("ALIGN",         (0,0),(0,-1),  "LEFT"),
        ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [LIGHT, colors.white]),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("BACKGROUND",    (0,-1),(-1,-1), colors.HexColor("#FDECEA")),
        ("FONTNAME",      (0,-1),(-1,-1), "Helvetica-Bold"),
    ]))
    story.append(ft)
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph(
        "FICO below 650 carries a 32% default rate — 4.3x higher than the 750+ tier. "
        "The interest rate differential is only ~6%, which is far too narrow to compensate "
        "for the additional credit risk. A proper risk-based pricing model would require "
        "substantially higher rates or stricter loan limits for this segment.",
        S["body"]
    ))

    story.append(PageBreak())

    # ── SECTION 4: Methods & Tools ────────────────────────────────────────────
    story.append(Paragraph("Section 4 — Methods & Tools", S["section_header"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 0.08*inch))

    story.append(Paragraph("SQL Techniques Used", S["sub_header"]))
    sql_data = [[
        Paragraph(
            "<b>CASE WHEN</b> — FICO buckets, payment tiers, outcome labels, policy status<br/>"
            "<b>NTILE(10)</b> — Income decile window function for ranked bucketing<br/>"
            "<b>GROUP BY + Aggregates</b> — COUNT, SUM, AVG, MIN, MAX per segment<br/>"
            "<b>ROUND()</b> — Consistent decimal formatting across all outputs<br/>"
            "<b>sort_order column</b> — Manual ordering for correct Tableau axis sorting<br/>"
            "<b>Subquery / CTE</b> — Income decile analysis uses NTILE in a WITH clause",
            ParagraphStyle("sql", fontSize=10, fontName="Helvetica",
                          textColor=DARK, leading=17, leftIndent=8)
        )
    ]]
    sql_box = Table(sql_data, colWidths=[6.5*inch])
    sql_box.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#F0F7FF")),
        ("BOX",           (0,0),(-1,-1), 1, ACCENT),
        ("TOPPADDING",    (0,0),(-1,-1), 12),
        ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ("LEFTPADDING",   (0,0),(-1,-1), 14),
    ]))
    story.append(sql_box)
    story.append(Spacer(1, 0.12*inch))

    story.append(Paragraph("Tech Stack", S["sub_header"]))
    tech_data = [
        ["Tool",                    "Purpose"],
        ["Python (pandas, sqlite3)", "ETL — load CSV → SQLite database, run queries, export CSVs"],
        ["SQL (SQLite)",             "9 analytical queries: CASE, NTILE, window functions, aggregates"],
        ["Tableau Public",           "Interactive dashboard — 5 sheets + KPI header bar"],
        ["reportlab",                "PDF report generation"],
        ["GitHub",                   "Version control — code only, data gitignored"],
    ]
    tt = Table(tech_data, colWidths=[2.0*inch, 4.5*inch])
    tt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  ACCENT),
        ("TEXTCOLOR",     (0,0),(-1,0),  colors.white),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 9),
        ("ALIGN",         (0,0),(-1,-1), "LEFT"),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [LIGHT, colors.white]),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
    ]))
    story.append(tt)

    # ── SECTION 5: Key Takeaways ──────────────────────────────────────────────
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Section 5 — Key Takeaways", S["section_header"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 0.08*inch))

    takeaways = [
        ("<b>Small business loans are dramatically underpriced for risk.</b> A 27.8% default rate "
         "receiving only ~2% more in interest than the safest category represents a significant "
         "mispricing that a lender should address immediately.", RED),
        ("<b>FICO score is the single strongest predictor of default in this dataset.</b> "
         "The 4x difference in default rates across FICO tiers dwarfs the variation explained "
         "by loan purpose, income, or payment size.", BLUE),
        ("<b>The bank's credit policy works — but it's not used consistently enough.</b> "
         "Outside-policy loans default at materially higher rates across every loan category. "
         "Stricter policy enforcement would meaningfully reduce portfolio risk.", GREEN),
        ("<b>Payment burden adds independent predictive power.</b> Even controlling for FICO, "
         "loans with $800+ monthly payments default at 24.3% — suggesting that cash flow "
         "stress compounds credit score risk.", GOLD),
        ("<b>SQL alone can surface major business insights.</b> No machine learning needed. "
         "Nine well-constructed queries produced actionable findings that could directly "
         "inform lending policy, pricing models, and risk appetite decisions.", ACCENT),
    ]

    for text, color in takeaways:
        row = Table([[Paragraph(text, S["body"])]], colWidths=[6.5*inch])
        row.setStyle(TableStyle([
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("LINEBEFORE",    (0,0),(0,-1),  3, color),
            ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#FAFAFA")),
        ]))
        story.append(row)
        story.append(Spacer(1, 0.05*inch))

    # ── FOOTER ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        f"Generated {date.today().strftime('%B %d, %Y')} · "
        "Data: LendingClub via Kaggle · "
        "Dashboard: public.tableau.com/app/profile/favianesi.garcia/viz/SQLCreditAnalysis · "
        "Not financial advice — for educational and research purposes only.",
        S["disclaimer"]
    ))

    doc.build(story)
    print(f"PDF saved to: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

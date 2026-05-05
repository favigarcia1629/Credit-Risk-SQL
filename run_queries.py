"""
Credit Risk SQL Analysis
Runs all queries against the SQLite database and exports CSVs for Tableau.
"""
import sqlite3
import pandas as pd
import numpy as np
import os

DB_PATH  = os.path.join(os.path.dirname(__file__), 'credit_risk.db')
OUT_DIR  = os.path.join(os.path.dirname(__file__), 'exports')
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)


def save(df, filename, label):
    path = os.path.join(OUT_DIR, filename)
    df.to_csv(path, index=False)
    print(f"  Saved {filename:40s} ({len(df):>6,} rows)  — {label}")
    return df


# ── Q1: Default Rate by Loan Purpose ────────────────────────────────────────
q1 = pd.read_sql_query("""
    SELECT
        purpose,
        COUNT(*)                                    AS total_loans,
        SUM(not_fully_paid)                         AS total_defaults,
        ROUND(AVG(not_fully_paid) * 100, 2)         AS default_rate_pct,
        ROUND(AVG(int_rate) * 100, 2)               AS avg_interest_rate_pct,
        ROUND(AVG(installment), 2)                  AS avg_monthly_payment,
        ROUND(AVG(dti), 2)                          AS avg_dti,
        ROUND(AVG(fico), 0)                         AS avg_fico
    FROM loans
    GROUP BY purpose
    ORDER BY default_rate_pct DESC
""", conn)
save(q1, 'q1_default_by_purpose.csv', 'Default rate by loan purpose')


# ── Q2: Risk Profile by FICO Score Bucket ───────────────────────────────────
# sort_order added so Tableau can sort correctly (not alphabetically)
q2 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN fico >= 750 THEN '750+ Excellent'
            WHEN fico >= 700 THEN '700-749 Good'
            WHEN fico >= 650 THEN '650-699 Fair'
            WHEN fico >= 600 THEN '600-649 Poor'
            ELSE 'Below 600 Very Poor'
        END                                         AS fico_bucket,
        CASE
            WHEN fico >= 750 THEN 1
            WHEN fico >= 700 THEN 2
            WHEN fico >= 650 THEN 3
            WHEN fico >= 600 THEN 4
            ELSE 5
        END                                         AS sort_order,
        COUNT(*)                                    AS total_loans,
        SUM(not_fully_paid)                         AS defaults,
        ROUND(AVG(not_fully_paid) * 100, 2)         AS default_rate_pct,
        ROUND(AVG(int_rate) * 100, 2)               AS avg_interest_rate_pct,
        ROUND(AVG(dti), 2)                          AS avg_dti,
        ROUND(AVG(annual_income), 0)                AS avg_annual_income
    FROM loans
    GROUP BY fico_bucket, sort_order
    ORDER BY sort_order
""", conn)
save(q2, 'q2_risk_by_fico.csv', 'Risk profile by FICO bucket')


# ── Q3: All High-Risk Borrowers (no LIMIT — Tableau needs full dataset) ──────
q3 = pd.read_sql_query("""
    SELECT
        purpose,
        ROUND(int_rate * 100, 2)                    AS interest_rate_pct,
        fico,
        ROUND(dti, 2)                               AS debt_to_income,
        ROUND(annual_income, 0)                     AS annual_income,
        installment                                 AS monthly_payment,
        inq_last_6mths,
        delinq_2yrs,
        not_fully_paid                              AS defaulted,
        CASE
            WHEN not_fully_paid = 1 THEN 'Defaulted'
            ELSE 'Repaid'
        END                                         AS outcome
    FROM loans
    WHERE dti > 20
      AND fico < 650
      AND int_rate > 0.13
    ORDER BY dti DESC
""", conn)
save(q3, 'q3_high_risk_borrowers.csv', 'All high-risk borrowers (DTI>20, FICO<650, Rate>13%)')


# ── Q4: Interest Rate vs Loan Outcome ───────────────────────────────────────
q4 = pd.read_sql_query("""
    SELECT
        CASE WHEN not_fully_paid = 1 THEN 'Defaulted' ELSE 'Repaid' END AS loan_outcome,
        COUNT(*)                                    AS total_loans,
        ROUND(AVG(int_rate) * 100, 2)               AS avg_interest_rate_pct,
        ROUND(MIN(int_rate) * 100, 2)               AS min_rate_pct,
        ROUND(MAX(int_rate) * 100, 2)               AS max_rate_pct,
        ROUND(AVG(fico), 0)                         AS avg_fico,
        ROUND(AVG(dti), 2)                          AS avg_dti,
        ROUND(AVG(installment), 2)                  AS avg_monthly_payment,
        ROUND(AVG(annual_income), 0)                AS avg_annual_income
    FROM loans
    GROUP BY loan_outcome
""", conn)
save(q4, 'q4_rate_vs_outcome.csv', 'Interest rate distribution by outcome')


# ── Q5: Monthly Payment Stress ───────────────────────────────────────────────
q5 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN installment < 200 THEN '$0-$199'
            WHEN installment < 400 THEN '$200-$399'
            WHEN installment < 600 THEN '$400-$599'
            WHEN installment < 800 THEN '$600-$799'
            ELSE '$800+'
        END                                         AS payment_bucket,
        CASE
            WHEN installment < 200 THEN 1
            WHEN installment < 400 THEN 2
            WHEN installment < 600 THEN 3
            WHEN installment < 800 THEN 4
            ELSE 5
        END                                         AS sort_order,
        COUNT(*)                                    AS total_loans,
        SUM(not_fully_paid)                         AS defaults,
        ROUND(AVG(not_fully_paid) * 100, 2)         AS default_rate_pct,
        ROUND(AVG(int_rate) * 100, 2)               AS avg_interest_rate_pct,
        ROUND(AVG(dti), 2)                          AS avg_dti
    FROM loans
    GROUP BY payment_bucket, sort_order
    ORDER BY sort_order
""", conn)
save(q5, 'q5_payment_stress.csv', 'Default rate by monthly payment bucket')


# ── Q6: Executive KPI Summary ────────────────────────────────────────────────
q6 = pd.read_sql_query("""
    SELECT
        COUNT(*)                                    AS total_loans,
        SUM(not_fully_paid)                         AS total_defaults,
        ROUND(AVG(not_fully_paid) * 100, 2)         AS overall_default_rate_pct,
        ROUND(AVG(int_rate) * 100, 2)               AS avg_interest_rate_pct,
        ROUND(AVG(fico), 0)                         AS avg_fico_score,
        ROUND(AVG(dti), 2)                          AS avg_dti,
        ROUND(AVG(installment), 2)                  AS avg_monthly_payment,
        ROUND(AVG(annual_income), 0)                AS avg_annual_income,
        ROUND(SUM(installment), 0)                  AS total_monthly_payments,
        COUNT(DISTINCT purpose)                     AS loan_categories,
        SUM(CASE WHEN credit_policy = 1 THEN 1 ELSE 0 END) AS meets_credit_policy,
        SUM(CASE WHEN credit_policy = 0 THEN 1 ELSE 0 END) AS outside_credit_policy
    FROM loans
""", conn)
save(q6, 'q6_executive_kpis.csv', 'Portfolio-level KPIs')


# ── Q7: Annual Income vs Default Rate (income deciles) ───────────────────────
q7 = pd.read_sql_query("""
    WITH income_deciles AS (
        SELECT *,
            NTILE(10) OVER (ORDER BY annual_income) AS income_decile
        FROM loans
    )
    SELECT
        income_decile,
        ROUND(MIN(annual_income), 0)                AS income_min,
        ROUND(MAX(annual_income), 0)                AS income_max,
        COUNT(*)                                    AS total_loans,
        SUM(not_fully_paid)                         AS defaults,
        ROUND(AVG(not_fully_paid) * 100, 2)         AS default_rate_pct,
        ROUND(AVG(fico), 0)                         AS avg_fico,
        ROUND(AVG(dti), 2)                          AS avg_dti,
        ROUND(AVG(int_rate) * 100, 2)               AS avg_interest_rate_pct
    FROM income_deciles
    GROUP BY income_decile
    ORDER BY income_decile
""", conn)
save(q7, 'q7_income_vs_default.csv', 'Default rate by income decile')


# ── Q8: Credit Policy Compliance Analysis ────────────────────────────────────
q8 = pd.read_sql_query("""
    SELECT
        CASE WHEN credit_policy = 1 THEN 'Meets Policy' ELSE 'Outside Policy' END AS credit_policy_status,
        purpose,
        COUNT(*)                                    AS total_loans,
        SUM(not_fully_paid)                         AS defaults,
        ROUND(AVG(not_fully_paid) * 100, 2)         AS default_rate_pct,
        ROUND(AVG(int_rate) * 100, 2)               AS avg_interest_rate_pct,
        ROUND(AVG(fico), 0)                         AS avg_fico,
        ROUND(AVG(dti), 2)                          AS avg_dti
    FROM loans
    GROUP BY credit_policy_status, purpose
    ORDER BY credit_policy_status, default_rate_pct DESC
""", conn)
save(q8, 'q8_credit_policy.csv', 'Default rate by credit policy compliance + purpose')


# ── Q9: Full loan-level data for scatter plots / filters ─────────────────────
q9 = pd.read_sql_query("""
    SELECT
        purpose,
        ROUND(int_rate * 100, 2)                    AS interest_rate_pct,
        fico,
        ROUND(dti, 2)                               AS dti,
        ROUND(annual_income, 0)                     AS annual_income,
        installment                                 AS monthly_payment,
        revol_bal,
        ROUND(revol_util, 1)                        AS revol_util_pct,
        inq_last_6mths,
        delinq_2yrs,
        pub_rec,
        CASE WHEN credit_policy = 1 THEN 'Meets Policy' ELSE 'Outside Policy' END AS credit_policy_status,
        CASE WHEN not_fully_paid = 1 THEN 'Defaulted' ELSE 'Repaid' END AS outcome
    FROM loans
""", conn)
save(q9, 'q9_loan_level.csv', 'Full loan-level data for scatter plots and filters')

conn.close()
print(f"\nAll 9 CSVs written to: {OUT_DIR}/")
print("Ready to import into Tableau Public Desktop.")

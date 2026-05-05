# Credit Risk SQL Analysis

**Who defaults — and why? A SQL-driven analysis of 9,578 personal loans.**

🔗 **[Live Interactive Dashboard](https://public.tableau.com/app/profile/favianesi.garcia/viz/SQLCreditAnalysis/CreditRiskDashboard)**

Built a complete data pipeline from raw loan data to a Tableau Public dashboard using SQL to answer the core question lenders face: which borrowers are most likely to default, and is the bank pricing that risk correctly?

---

## The Question

Across 9,578 loans with a 16% overall default rate, this project uses SQL to identify the key drivers of default risk — loan purpose, FICO score, income, payment burden, and credit policy compliance — and tests whether interest rates actually reflect the underlying risk.

---

## Key Findings

| Finding | Result |
|---|---|
| Riskiest loan type | Small business (27.8% default rate) |
| Safest loan type | Major purchase (11.2% default rate) |
| FICO below 650 | 32% default rate vs. 7.4% for 750+ |
| High payment ($800+/mo) | 24.3% default rate |
| Defaulted vs. repaid avg rate | 13.3% vs. 12.1% — only 1.2pp difference |
| Outside credit policy loans | Significantly higher default rates |

> The bank charges higher rates to riskier borrowers — but the spread is too narrow. Borrowers with a 32% default rate are only paying ~3% more than the safest tier.

---

## Dashboard Sheets

| Sheet | Data Source | Insight |
|---|---|---|
| KPI Header | q6_executive_kpis | Portfolio-level: 9,578 loans, 16% default rate, avg FICO 711 |
| Default by Purpose | q1_default_by_purpose | Small business 2.5x riskier than major purchase |
| FICO Risk Tiers | q2_risk_by_fico | Default rate falls from 32% to 7% as FICO improves |
| FICO vs Rate Scatter | q9_loan_level | Low FICO = higher rate, but defaults cluster across all rates |
| Income vs Default | q7_income_vs_default | Lower income deciles carry higher default rates |

---

## SQL Queries

| Query | Business Question |
|---|---|
| `q1_default_by_purpose.sql` | Which loan types are riskiest? |
| `q2_risk_by_fico.sql` | How does credit score predict default? |
| `q3_high_risk_borrowers.sql` | Which borrowers combine multiple risk factors? |
| `q4_rate_vs_outcome.sql` | Is the bank pricing risk correctly? |
| `q5_payment_stress.sql` | Does payment burden predict default? |
| `q6_executive_kpis.sql` | What are the portfolio-level risk metrics? |
| `q7_income_vs_default.sql` | Does income level correlate with default? |
| `q8_credit_policy.sql` | How does credit policy compliance affect outcomes? |
| `q9_loan_level.sql` | Full loan-level data for scatter plots and filtering |

---

## Project Structure

```
credit_risk/
├── run_queries.py      # Runs all 9 SQL queries → exports CSVs
├── credit_risk.db      # SQLite database (generated from loan_data.csv)
├── exports/            # 9 CSVs ready for Tableau (gitignored)
└── README.md
```

---

## Run Locally

```bash
git clone https://github.com/favigarcia1629/Credit-Risk-SQL.git
cd Credit-Risk-SQL

# Add loan_data.csv to this directory (source: LendingClub via Kaggle)
pip install pandas numpy

# Build database and export all CSVs
python run_queries.py

# CSVs will appear in exports/ — import into Tableau Public Desktop
```

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python (pandas, sqlite3) | ETL — load CSV → SQLite, run queries, export CSVs |
| SQL (SQLite) | 9 analytical queries with CASE, NTILE, window functions |
| Tableau Public | Interactive dashboard |

---

## Dataset

9,578 personal loans from LendingClub. Features include FICO score, loan purpose, interest rate, installment, debt-to-income ratio, annual income, revolving balance, delinquency history, and loan outcome (fully paid vs. defaulted).

*Not financial advice — built for research and education.*

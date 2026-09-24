# Superstore Fulfillment SLA Analysis

> Where does a shipping promise break, what does it cost operationally, and what should change?

I used the public Superstore dataset to model fulfillment performance from order placement through shipment. The source has no promised delivery date, so I defined a transparent, ship-mode-specific SLA and tested how the result changes when the assumption moves by one business day.

## Current status

The Python transformation, SLA analysis, reporting star schema, and PostgreSQL reproduction are complete. The automated suite reports 21 passing tests. The live SQL run on OmenLEO matched the Python outputs with zero reconciliation failures across overall, ship-mode, regional, and monthly summaries.

The remaining portfolio work is presentation refinement. The findings and technical explanation are documented in:

- [Findings memo](findings-memo.md): the business question, results, operational interpretation, and limitations.
- [Technical defense](technical-defense.md): the Python and SQL design, grain choices, validation, and interview-level explanations.

## Headline result

I use the calibrated `0/2/3/4` scenario as the primary comparison. It produces a similar late-rate range across the three non-Same-Day modes:

| Ship mode | Orders | Late orders | Late-order rate |
|---|---:|---:|---:|
| First Class | 787 | 137 | 17.4% |
| Second Class | 964 | 154 | 16.0% |
| Standard Class | 2,994 | 526 | 17.6% |
| Same Day | 264 | 9 | 3.4% |

The conclusion is assumption-sensitive. The overall late-order rate is 15.2% under the initial benchmark, 16.5% under the calibrated scenario, 37.4% under the strict sensitivity, and 6.0% under the lenient sensitivity. These are modeled comparisons, not official contractual SLA results.

## What I built

- A validated Python transformation that profiles the source, preserves order-line grain, and creates a one-row-per-order SLA fact.
- Holiday-aware business-day logic that excludes the order date and includes the ship date.
- Four explicit SLA scenarios: base, calibrated, strict, and lenient.
- A reporting star schema with date, customer, location, product, and ship-mode dimensions.
- A PostgreSQL reproduction that preserves both fact-table grains, aggregates financials to order grain, produces four summary families, and reconciles to Python.
- Automated tests for source quality, dates, grain, keys, SLA logic, and star-schema integrity.

## Reproduce the analysis

Run these commands from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.transform_superstore
.\.venv\Scripts\python.exe -m scripts.analyze_sla
psql -d portfolio_sla -f sql\fulfillment_sla_analysis.sql
```

The SQL script uses temporary tables and ends with `ROLLBACK`. It reads the processed CSV files from the client machine and does not create persistent database objects.

## Repository map

- `scripts/transform_superstore.py`: source validation, business-day logic, facts, and star schema.
- `scripts/analyze_sla.py`: scenario analysis and Python summaries.
- `sql/fulfillment_sla_analysis.sql`: PostgreSQL reproduction and reconciliation.
- `analysis-notes.md`: detailed definitions, results, and interpretation limits.
- `data-model-notes.md`: grain, key, join, and dimension decisions.
- `tests/`: automated validation and regression coverage.

## Data and confidentiality

This uses a public dataset. It demonstrates the same analysis pattern built in production: turning operational data into documented rules, validated transformations, and decision-ready analysis without exposing employer data or confidential figures.

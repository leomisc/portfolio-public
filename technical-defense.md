# Technical Defense

This document is the short explanation I would use if someone asked me to defend the Superstore fulfillment-SLA analysis from source data through SQL output.

## One-minute explanation

I kept the source at order-line grain and created a separate one-row-per-order fact for SLA evaluation. That prevents sales and profit from being repeated when line-level financials are joined to order-level service status. Python validates the source, calculates holiday-aware business days, and applies explicit SLA scenarios. PostgreSQL loads those validated facts, aggregates financials to order grain, produces the same summaries, and reconciles its output to Python. The automated suite reports 21 passing tests, and the live SQL run matched Python with zero reconciliation failures.

## Source and grain

The raw archive contains 9,994 order-line rows and 5,009 orders.

- `Row ID` is the unique order-line key.
- `Order ID` is the order-level key.
- The line fact retains sales, quantity, discount, profit, product, customer, and location fields.
- The order fact retains order dates, ship mode, business days to ship, SLA days, SLA variance, and the late flag.

The source was checked for required columns, duplicate line keys, nulls, invalid dates, inconsistent order-level fields, and row-count changes. Every order's lines share the same order date, ship date, ship mode, and location attributes in this dataset.

## Python responsibilities

The transformation in `scripts/transform_superstore.py` does the source-facing work:

1. Loads the Windows-1252 source and preserves Postal Code as text.
2. Parses dates explicitly using the source format.
3. Validates the source profile and expected grain.
4. Calculates calendar days and holiday-aware business days.
5. Excludes the order date and includes the ship date in the business-day calculation.
6. Applies the documented SLA mapping and treats equality as success.
7. Writes `fact_order_lines`, `fact_orders`, and the reporting star-schema files.

The observed holiday calendar covers 2014 through 2017 and January 1, 2018. The extra January holiday is needed for the early-January shipment in the source period.

## Scenario design

The scenarios are rows in the SQL model and mappings in the Python analysis:

| Scenario | Same Day | First Class | Second Class | Standard Class |
|---|---:|---:|---:|---:|
| Initial benchmark | 0 | 1 | 2 | 5 |
| Calibrated | 0 | 2 | 3 | 4 |
| Strict | 0 | 0 | 1 | 4 |
| Lenient | 0 | 2 | 3 | 6 |

The strict and lenient cases shift only modes with a positive base SLA. Same Day remains zero because a one-day shift would change the meaning of that service mode rather than test the same assumption.

## Financial aggregation

Sales and profit are line-level measures. SLA status is order-level. The analysis therefore aggregates sales and profit by `Order ID` before joining them to scenario-level late status.

Discount is a rate, not an additive measure. When comparing discount at order level, I use a sales-weighted discount rather than summing the line values.

Late-order sales and late-order profit are exposure measures. The data does not support a causal claim that late shipment caused the financial result.

## SQL responsibilities

The SQL file in `sql/fulfillment_sla_analysis.sql` reproduces the analysis from validated inputs:

1. Loads the processed line and order facts with `\copy`.
2. Asserts the expected row counts and unique keys.
3. Builds `order_financials` before the order-level SLA join.
4. Stores scenario thresholds as rows in `scenario_sla`.
5. Produces 20,036 scenario-order rows: 5,009 orders across four scenarios.
6. Creates overall, ship-mode, regional, and monthly summaries.
7. Loads the Python summaries into temporary tables.
8. Compares SQL counts, rates, and financial totals with Python.
9. Prints the result tables and reconciliation status.
10. Ends with `ROLLBACK` so the database is not changed.

The SQL is not a second raw-data-cleaning pipeline. Python owns source validation and the holiday-aware date calculation. SQL demonstrates the relational analysis and proves that the summary layer agrees with the Python implementation.

## Reporting model decisions

The reporting fact remains at order-line grain and links directly to date, customer, location, product, and ship-mode dimensions. The order-level SLA fact remains separate because repeating SLA measures on every line would make downstream financial joins easy to double count.

The source contains Product IDs with conflicting descriptions. The reporting layer therefore uses a descriptor-based product key and retains the original Product ID as an attribute. It does not assume Product ID is unique.

## Validation evidence

- Python test suite: 21 passed.
- SQL overall reconciliation failures: 0.
- SQL ship-mode reconciliation failures: 0.
- SQL regional reconciliation failures: 0.
- SQL monthly reconciliation failures: 0.
- Live PostgreSQL execution completed on OmenLEO.

## Questions I should be able to answer

### Why not evaluate the SLA at line grain?

The business question is whether an order shipped within the modeled promise. The source shows all lines in an order moving together, so order grain avoids repeating the service result across lines.

### Why not call the result contractual performance?

The source has no promised-delivery field. The threshold is modeled from ship mode and tested for sensitivity.

### Why aggregate financials before the SLA join?

Joining an order-level status to unaggregated lines would repeat an order's financial values for each line. Aggregating first keeps the order's sales and profit at one row.

### Why does equality count as success?

The documented rule is `business_days_to_ship <= SLA_days`. A shipment on the threshold meets the modeled promise.

### Why do Python and SQL both exist?

Python is the source-validation and transformation layer. SQL is the relational reproduction and reconciliation layer. Each is responsible for the part it handles best.

### What would change in a split-shipment environment?

The SLA would need to move to shipment or order-line grain. The current order-level fact is appropriate only because the source shows orders moving together.

## Reproduction commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.transform_superstore
.\.venv\Scripts\python.exe -m scripts.analyze_sla
psql -d portfolio_sla -f sql\fulfillment_sla_analysis.sql
```

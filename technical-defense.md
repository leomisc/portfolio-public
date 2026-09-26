# Technical Defense

This document explains the design choices behind the Superstore fulfillment-SLA analysis. It is intended as a technical appendix for a reviewer who wants to understand the data model, transformation logic, SQL reproduction, and validation evidence.

## One-minute explanation

The source remains at order-line grain; a separate one-row-per-order fact supports time-to-ship classification. Python validates the source, calculates holiday-aware business days, and applies explicit thresholds. PostgreSQL loads the processed facts, aggregates line-level financials by order, produces the same summaries, and reconciles them to Python. The recorded validation run had 21 passing tests and zero SQL reconciliation failures.

## Source and grain

The raw archive contains 9,994 order-line rows and 5,009 orders.

- `Row ID` is the unique order-line key.
- `Order ID` is the order-level key.
- The line fact retains sales, quantity, discount, profit, product, customer, and location fields.
- The order fact retains order dates, ship mode, business days to ship, SLA days, SLA variance, and the late flag.

The source is checked for required columns, duplicate line keys, nulls, invalid dates, inconsistent order-level fields, and row-count changes. Every order's lines share the same order date, ship date, ship mode, and location attributes in this dataset.

## Python responsibilities

The transformation in `scripts/transform_superstore.py` performs the source-facing work:

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

The calibrated thresholds were selected using the observed data. They support within-dataset exploration, not an independent assessment of contractual performance. Strict and lenient cases shift only modes with a positive threshold; Same Day remains at zero.

## Financial aggregation

Sales and profit are line-level measures. SLA status is order-level. The analysis therefore aggregates sales and profit by `Order ID` before joining them to scenario-level late status.

Discount is a rate, not an additive measure. When comparing discount at order level, the analysis uses a sales-weighted discount rather than summing line values.

Late-order sales and late-order profit are exposure measures. The data does not support a causal claim that late shipment caused the financial result.

## Cross-tab methodology

The regional and product diagnostics use the same calibrated order-level status as the primary analysis. For subcategory results, the line data is first reduced to distinct `(Order ID, Sub-Category)` pairs. That keeps a subcategory from being counted multiple times simply because an order contains several lines of the same product family. The one-row-per-order attributes are then joined and grouped by the requested dimensions.

The thresholds are deliberate rather than hidden filters:

- State comparisons use at least 100 orders.
- Subcategory comparisons use at least 50 orders.
- Three-way subcategory × ship mode × region cells shown in the chart use at least 30 distinct orders.

The lower threshold is useful for finding investigation points, but it is not a claim that every displayed percentage is equally stable. A small cell can have a high rate from a modest number of late orders. The findings therefore pair percentages with late-order and total-order counts.

The regional volume check compares annual order counts and modeled late rates across 16 region-year observations. Each within-region correlation has only four annual observations and is exploratory.

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

Python owns source validation and the holiday-aware date calculation. SQL reproduces the relational summaries from those processed inputs and checks agreement with the Python output; it does not independently verify the source transformation.

## Reporting model decisions

The reporting fact remains at order-line grain and links directly to date, customer, location, product, and ship-mode dimensions. The order-level SLA fact remains separate because repeating SLA measures on every line would make downstream financial joins easy to double count.

The source contains Product IDs with conflicting descriptions. The reporting layer therefore uses a descriptor-based product key and retains the original Product ID as an attribute. It does not assume Product ID is unique.

## Chart production

The three portfolio charts are generated by `scripts/create_portfolio_charts.py`. The script reads the local processed order and line facts, selects the calibrated scenario, calculates the regional, yearly ship-mode, and three-way cross-tab summaries, and writes tracked SVG files under `docs/assets/`.

The chart command is:

```powershell
.\.venv\Scripts\python.exe scripts\create_portfolio_charts.py
```

The charts are presentation aids, not a separate analytical source. If the processed facts change, regenerate them before reviewing the written findings.

## Validation evidence

The recorded local validation run had 21 passing Python tests. A PostgreSQL execution reported zero reconciliation failures for overall, ship-mode, regional, and monthly summaries. The commands below provide the current verification path.

## Questions the analysis should withstand

### Why not evaluate the SLA at line grain?

The question is whether an order shipped within the modeled time threshold. The source shows all lines in an order moving together, so order grain avoids repeating the service result across lines.

### Why not call the result contractual performance?

The source has no promised ship or delivery field. The analysis measures time to shipment against modeled thresholds, then tests sensitivity to those thresholds.

### Why aggregate financials before the SLA join?

Joining an order-level status to unaggregated lines would repeat an order's financial values for each line. Aggregating first keeps the order's sales and profit at one row.

### Why does equality count as success?

The documented rule is `business_days_to_ship <= SLA_days`. An order shipped on the threshold is classified as on time.

### Why do Python and SQL both exist?

Python is the source-validation and transformation layer. SQL is the relational reproduction and reconciliation layer. Each is responsible for the part it handles best.

### What would change in a split-shipment environment?

The SLA would need to move to shipment or order-line grain. The current order-level fact is appropriate only because the source shows orders moving together.

## Reproduction commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.transform_superstore
.\.venv\Scripts\python.exe -m scripts.analyze_sla
.\.venv\Scripts\python.exe scripts\create_portfolio_charts.py
psql -d portfolio_sla -f sql\fulfillment_sla_analysis.sql
```

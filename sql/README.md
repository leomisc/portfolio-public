# PostgreSQL Reproduction

The PostgreSQL script reproduces the scenario summaries from the processed Python facts. It starts after source validation and business-day calculation; it does not independently parse the raw archive.

## Run it

Run these commands from the repository root after setting up the Python environment described in the [project README](../README.md). PostgreSQL and an existing database named `portfolio_sla` are required for the final command. The example uses the `postgres` role; substitute your local PostgreSQL role if it differs:

```powershell
.\.venv\Scripts\python.exe -m scripts.transform_superstore
.\.venv\Scripts\python.exe -m scripts.analyze_sla
psql -U postgres -d portfolio_sla -f sql/fulfillment_sla_analysis.sql
```

The script expects `psql` to be connected to an existing database. It uses
temporary tables and ends with `ROLLBACK`, so it does not create or alter
persistent database objects.

## What the SQL is proving

### 1. The two fact tables retain their grains

`fact_order_lines` contains 9,994 rows at `Row ID` grain. `fact_orders`
contains 5,009 rows at `Order ID` grain. The script asserts both counts and
asserts that the keys are unique before analysis begins.

### 2. Financial measures are aggregated before the order-level join

Sales and profit exist on order lines. SLA status is evaluated at order grain.
The `order_financials` CTE-equivalent temporary table performs:

```sql
SELECT order_id,
       sum(sales) AS order_sales,
       sum(profit) AS order_profit
FROM fact_order_lines
GROUP BY order_id;
```

This creates one financial row per order before joining to scenario-level status, so the reported sales and profit associated with classified-late orders are counted once per order.

### 3. SLA assumptions are modeled as rows

The `scenario_sla` table stores one row per scenario and ship mode:

| Scenario | Same Day | First Class | Second Class | Standard Class |
|---|---:|---:|---:|---:|
| Initial benchmark | 0 | 1 | 2 | 5 |
| Calibrated | 0 | 2 | 3 | 4 |
| Strict | 0 | 1 | 2 | 3 |
| Lenient | 0 | 3 | 4 | 5 |

This is preferable to burying the assumptions inside nested `CASE` logic.
The calibrated mapping is intentionally explicit because it is not a uniform
one-day shift: First and Second Class increase while Standard Class decreases.

### 4. Each order is evaluated under each scenario

Each order joins to exactly one SLA row for each scenario through `ship_mode`.
The resulting primary key is `(scenario, order_id)`, giving 5,009 orders × 4
scenarios = 20,036 scenario-order rows.

The success rule is:

```sql
business_days_to_ship <= scenario_sla_days
```

The late rule is its strict complement:

```sql
business_days_to_ship > scenario_sla_days
```

Equality is therefore success, matching the Python implementation.

### 5. `FILTER` performs readable conditional aggregation

For example:

```sql
count(*) FILTER (WHERE is_late) AS late_orders,
sum(order_sales) FILTER (WHERE is_late) AS late_order_sales
```

The denominator remains all orders in the group. This produces an order late
rate, rather than a line late rate.

### 6. Reconciliation checks implementation independence

The script loads the Python summary CSVs into separate temporary tables and
compares counts, financial totals, and rates with the SQL results. It prints
the number of failures for the overall, ship-mode, region, and monthly
outputs. A successful run should report zero failures in every output.

## Expected headline results

| Scenario | Late orders | Late-order rate |
|---|---:|---:|
| Initial benchmark | 762 | 15.2% |
| Calibrated | 826 | 16.5% |
| Strict | 2,364 | 47.2% |
| Lenient | 33 | 0.7% |

Matching summaries confirm that the SQL aggregation agrees with Python for these processed inputs. Python remains responsible for source validation and the holiday-aware business-day calculation.

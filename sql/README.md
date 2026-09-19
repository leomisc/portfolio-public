# PostgreSQL reproduction

This directory reproduces the Python fulfillment-SLA analysis in PostgreSQL.
The SQL reads the processed facts, not the raw archive, so the database step
starts from the same validated inputs as the Python analysis.

## Run it

Run these commands from the repository root after generating the processed
facts and Python analysis outputs:

```powershell
.\.venv\Scripts\python.exe -m scripts.transform_superstore
.\.venv\Scripts\python.exe -m scripts.analyze_sla
psql -d portfolio_sla -f sql/fulfillment_sla_analysis.sql
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

This prevents a many-to-one join from repeating an order's financial value for
every line when calculating late-order financial impact.

### 3. SLA assumptions are modeled as rows

The `scenario_sla` table stores one row per scenario and ship mode:

| Scenario | Same Day | First Class | Second Class | Standard Class |
|---|---:|---:|---:|---:|
| Base | 0 | 1 | 2 | 5 |
| Calibrated | 0 | 2 | 3 | 4 |
| Strict | 0 | 0 | 1 | 4 |
| Lenient | 0 | 2 | 3 | 6 |

This is preferable to burying the assumptions inside nested `CASE` logic.
The calibrated mapping is intentionally explicit because it is not a uniform
one-day shift: First and Second Class increase while Standard Class decreases.

### 4. `CROSS JOIN` logic is represented by a controlled scenario join

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
| Base | 762 | 15.2% |
| Calibrated | 826 | 16.5% |
| Strict | 1,875 | 37.4% |
| Lenient | 300 | 6.0% |

The SQL reproduces the Python results; it does not replace the Python
transformation. Python remains responsible for source validation and the
holiday-aware business-day calculation, while PostgreSQL demonstrates the
relational analysis and aggregation layer.

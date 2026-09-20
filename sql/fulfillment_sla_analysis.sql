-- PostgreSQL reproduction of the Python fulfillment-SLA analysis.
--
-- Run this file from the repository root with psql:
--   psql -d portfolio_sla -f sql/fulfillment_sla_analysis.sql
--
-- The script is intentionally read-only with respect to the database: all
-- tables are temporary and disappear when the transaction rolls back.
-- The \copy commands read the processed CSVs from the client machine, so the
-- PostgreSQL server does not need filesystem access to the repository.

\set ON_ERROR_STOP on
\pset pager off

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Load the two processed facts at their intended grains.
-- ---------------------------------------------------------------------------

CREATE TEMP TABLE fact_order_lines (
    row_id bigint,
    order_id text,
    order_date date,
    ship_date date,
    ship_mode text,
    customer_id text,
    customer_name text,
    segment text,
    country text,
    city text,
    state text,
    postal_code text,
    region text,
    product_id text,
    category text,
    sub_category text,
    product_name text,
    sales numeric(18, 4),
    quantity integer,
    discount numeric(9, 6),
    profit numeric(18, 4)
);

\copy fact_order_lines (row_id, order_id, order_date, ship_date, ship_mode, customer_id, customer_name, segment, country, city, state, postal_code, region, product_id, category, sub_category, product_name, sales, quantity, discount, profit) FROM 'data/processed/fact_order_lines.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE TEMP TABLE fact_orders (
    order_id text,
    order_date date,
    ship_date date,
    ship_mode text,
    customer_id text,
    country text,
    city text,
    state text,
    postal_code text,
    region text,
    calendar_days_to_ship integer,
    business_days_to_ship integer,
    sla_days integer,
    sla_variance integer,
    is_late boolean
);

\copy fact_orders (order_id, order_date, ship_date, ship_mode, customer_id, country, city, state, postal_code, region, calendar_days_to_ship, business_days_to_ship, sla_days, sla_variance, is_late) FROM 'data/processed/fact_orders.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

-- Input assertions make grain and source completeness explicit before any
-- aggregate is calculated.
DO $$
BEGIN
    IF (SELECT count(*) FROM fact_order_lines) <> 9994 THEN
        RAISE EXCEPTION 'Expected 9,994 order lines';
    END IF;

    IF (SELECT count(*) FROM fact_orders) <> 5009 THEN
        RAISE EXCEPTION 'Expected 5,009 orders';
    END IF;

    IF (SELECT count(DISTINCT row_id) FROM fact_order_lines) <> 9994 THEN
        RAISE EXCEPTION 'Row ID is not unique at order-line grain';
    END IF;

    IF (SELECT count(DISTINCT order_id) FROM fact_order_lines) <> 5009 THEN
        RAISE EXCEPTION 'Order ID count does not reconcile between facts';
    END IF;

    IF (SELECT count(DISTINCT order_id) FROM fact_orders) <> 5009 THEN
        RAISE EXCEPTION 'Order ID is not unique at order grain';
    END IF;
END;
$$;

-- ---------------------------------------------------------------------------
-- 2. Aggregate line-level financials to order grain.
-- ---------------------------------------------------------------------------

-- This is the key grain-control step. Sales and profit belong to order lines,
-- but late-order analysis is evaluated once per order. Aggregating before the
-- scenario join prevents multiplying an order's financials by its line count.
CREATE TEMP TABLE order_financials AS
SELECT
    order_id,
    sum(sales)::numeric(18, 4) AS order_sales,
    sum(profit)::numeric(18, 4) AS order_profit,
    count(*)::integer AS order_line_count
FROM fact_order_lines
GROUP BY order_id;

ALTER TABLE order_financials ADD PRIMARY KEY (order_id);

DO $$
BEGIN
    IF (SELECT count(*) FROM order_financials) <> (SELECT count(*) FROM fact_orders) THEN
        RAISE EXCEPTION 'Financial aggregation did not produce one row per order';
    END IF;
END;
$$;

-- ---------------------------------------------------------------------------
-- 3. Declare the SLA scenarios as data.
-- ---------------------------------------------------------------------------

-- A normalized mapping table is easier to audit than nested CASE expressions.
-- The calibrated scenario is explicit rather than derived by a generic shift:
-- Standard Class moves from 5 to 4 while First and Second Class move upward.
CREATE TEMP TABLE scenario_sla (
    scenario text,
    ship_mode text,
    scenario_sla_days integer,
    PRIMARY KEY (scenario, ship_mode)
);

INSERT INTO scenario_sla (scenario, ship_mode, scenario_sla_days)
VALUES
    ('base', 'Same Day', 0),
    ('base', 'First Class', 1),
    ('base', 'Second Class', 2),
    ('base', 'Standard Class', 5),
    ('calibrated', 'Same Day', 0),
    ('calibrated', 'First Class', 2),
    ('calibrated', 'Second Class', 3),
    ('calibrated', 'Standard Class', 4),
    ('strict', 'Same Day', 0),
    ('strict', 'First Class', 0),
    ('strict', 'Second Class', 1),
    ('strict', 'Standard Class', 4),
    ('lenient', 'Same Day', 0),
    ('lenient', 'First Class', 2),
    ('lenient', 'Second Class', 3),
    ('lenient', 'Standard Class', 6);

-- ---------------------------------------------------------------------------
-- 4. Build one row per order per scenario.
-- ---------------------------------------------------------------------------

CREATE TEMP TABLE scenario_orders AS
SELECT
    s.scenario,
    o.order_id,
    o.order_date,
    o.ship_mode,
    o.region,
    o.business_days_to_ship,
    s.scenario_sla_days,
    (o.business_days_to_ship <= s.scenario_sla_days) AS is_success,
    (o.business_days_to_ship > s.scenario_sla_days) AS is_late,
    f.order_sales,
    f.order_profit,
    f.order_line_count,
    date_trunc('month', o.order_date)::date AS order_month
FROM fact_orders AS o
JOIN scenario_sla AS s
  ON s.ship_mode = o.ship_mode
JOIN order_financials AS f
  ON f.order_id = o.order_id;

ALTER TABLE scenario_orders ADD PRIMARY KEY (scenario, order_id);

DO $$
BEGIN
    IF (SELECT count(*) FROM scenario_orders) <> 5009 * 4 THEN
        RAISE EXCEPTION 'Expected 20,036 scenario-order rows';
    END IF;
END;
$$;

-- ---------------------------------------------------------------------------
-- 5. Summarize using conditional aggregation.
-- ---------------------------------------------------------------------------

-- COUNT(*) FILTER (WHERE ...) is PostgreSQL's readable form of conditional
-- aggregation. The denominator remains the complete order population, so the
-- rate is an order rate rather than a line rate.
CREATE TEMP TABLE summary_overall AS
SELECT
    scenario,
    count(*)::integer AS orders,
    (count(*) FILTER (WHERE is_success))::integer AS successful_orders,
    (count(*) FILTER (WHERE is_late))::integer AS late_orders,
    sum(order_sales)::numeric(18, 4) AS total_sales,
    coalesce(sum(order_sales) FILTER (WHERE is_late), 0)::numeric(18, 4) AS late_order_sales,
    sum(order_profit)::numeric(18, 4) AS total_profit,
    coalesce(sum(order_profit) FILTER (WHERE is_late), 0)::numeric(18, 4) AS late_order_profit,
    round((count(*) FILTER (WHERE is_success))::numeric / nullif(count(*), 0), 15) AS success_rate,
    round((count(*) FILTER (WHERE is_late))::numeric / nullif(count(*), 0), 15) AS late_order_rate
FROM scenario_orders
GROUP BY scenario;

CREATE TEMP TABLE summary_by_ship_mode AS
SELECT
    scenario,
    ship_mode,
    count(*)::integer AS orders,
    (count(*) FILTER (WHERE is_success))::integer AS successful_orders,
    (count(*) FILTER (WHERE is_late))::integer AS late_orders,
    sum(order_sales)::numeric(18, 4) AS total_sales,
    coalesce(sum(order_sales) FILTER (WHERE is_late), 0)::numeric(18, 4) AS late_order_sales,
    sum(order_profit)::numeric(18, 4) AS total_profit,
    coalesce(sum(order_profit) FILTER (WHERE is_late), 0)::numeric(18, 4) AS late_order_profit,
    round((count(*) FILTER (WHERE is_success))::numeric / nullif(count(*), 0), 15) AS success_rate,
    round((count(*) FILTER (WHERE is_late))::numeric / nullif(count(*), 0), 15) AS late_order_rate
FROM scenario_orders
GROUP BY scenario, ship_mode;

CREATE TEMP TABLE summary_by_region AS
SELECT
    scenario,
    region,
    count(*)::integer AS orders,
    (count(*) FILTER (WHERE is_success))::integer AS successful_orders,
    (count(*) FILTER (WHERE is_late))::integer AS late_orders,
    sum(order_sales)::numeric(18, 4) AS total_sales,
    coalesce(sum(order_sales) FILTER (WHERE is_late), 0)::numeric(18, 4) AS late_order_sales,
    sum(order_profit)::numeric(18, 4) AS total_profit,
    coalesce(sum(order_profit) FILTER (WHERE is_late), 0)::numeric(18, 4) AS late_order_profit,
    round((count(*) FILTER (WHERE is_success))::numeric / nullif(count(*), 0), 15) AS success_rate,
    round((count(*) FILTER (WHERE is_late))::numeric / nullif(count(*), 0), 15) AS late_order_rate
FROM scenario_orders
GROUP BY scenario, region;

CREATE TEMP TABLE summary_by_month AS
SELECT
    scenario,
    order_month,
    count(*)::integer AS orders,
    (count(*) FILTER (WHERE is_success))::integer AS successful_orders,
    (count(*) FILTER (WHERE is_late))::integer AS late_orders,
    sum(order_sales)::numeric(18, 4) AS total_sales,
    coalesce(sum(order_sales) FILTER (WHERE is_late), 0)::numeric(18, 4) AS late_order_sales,
    sum(order_profit)::numeric(18, 4) AS total_profit,
    coalesce(sum(order_profit) FILTER (WHERE is_late), 0)::numeric(18, 4) AS late_order_profit,
    round((count(*) FILTER (WHERE is_success))::numeric / nullif(count(*), 0), 15) AS success_rate,
    round((count(*) FILTER (WHERE is_late))::numeric / nullif(count(*), 0), 15) AS late_order_rate
FROM scenario_orders
GROUP BY scenario, order_month;

-- ---------------------------------------------------------------------------
-- 6. Reconcile SQL results to the Python output files.
-- ---------------------------------------------------------------------------

-- The Python files are loaded only for comparison. The SQL summaries above
-- are independently calculated from the two processed fact CSVs.
CREATE TEMP TABLE python_overall (
    scenario text,
    orders integer,
    successful_orders integer,
    late_orders integer,
    total_sales numeric,
    late_order_sales numeric,
    total_profit numeric,
    late_order_profit numeric,
    success_rate double precision,
    late_order_rate double precision
);

\copy python_overall FROM 'data/processed/analysis/sla_summary_overall.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE TEMP TABLE python_by_ship_mode (
    scenario text,
    ship_mode text,
    orders integer,
    successful_orders integer,
    late_orders integer,
    total_sales numeric,
    late_order_sales numeric,
    total_profit numeric,
    late_order_profit numeric,
    success_rate double precision,
    late_order_rate double precision
);

\copy python_by_ship_mode FROM 'data/processed/analysis/sla_summary_by_ship_mode.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE TEMP TABLE python_by_region (
    scenario text,
    region text,
    orders integer,
    successful_orders integer,
    late_orders integer,
    total_sales numeric,
    late_order_sales numeric,
    total_profit numeric,
    late_order_profit numeric,
    success_rate double precision,
    late_order_rate double precision
);

\copy python_by_region FROM 'data/processed/analysis/sla_summary_by_region.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE TEMP TABLE python_by_month (
    scenario text,
    order_month text,
    orders integer,
    successful_orders integer,
    late_orders integer,
    total_sales numeric,
    late_order_sales numeric,
    total_profit numeric,
    late_order_profit numeric,
    success_rate double precision,
    late_order_rate double precision
);

\copy python_by_month FROM 'data/processed/analysis/sla_summary_by_month.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE TEMP TABLE reconciliation_overall AS
SELECT
    coalesce(s.scenario, p.scenario) AS scenario,
    coalesce(
        s.orders = p.orders
        AND s.successful_orders = p.successful_orders
        AND s.late_orders = p.late_orders
        AND abs(s.total_sales - p.total_sales) < 0.0000001
        AND abs(s.late_order_sales - p.late_order_sales) < 0.0000001
        AND abs(s.total_profit - p.total_profit) < 0.0000001
        AND abs(s.late_order_profit - p.late_order_profit) < 0.0000001
        AND abs(s.success_rate - p.success_rate::numeric) < 1e-12
        AND abs(s.late_order_rate - p.late_order_rate::numeric) < 1e-12,
        false
    ) AS matches_python,
    s.late_orders AS sql_late_orders,
    p.late_orders AS python_late_orders,
    s.late_order_rate AS sql_late_order_rate,
    p.late_order_rate AS python_late_order_rate
FROM summary_overall AS s
FULL JOIN python_overall AS p USING (scenario);

CREATE TEMP TABLE reconciliation_by_ship_mode AS
SELECT
    coalesce(s.scenario, p.scenario) AS scenario,
    coalesce(s.ship_mode, p.ship_mode) AS ship_mode,
    coalesce(
        s.orders = p.orders
        AND s.successful_orders = p.successful_orders
        AND s.late_orders = p.late_orders
        AND abs(s.total_sales - p.total_sales) < 0.0000001
        AND abs(s.late_order_sales - p.late_order_sales) < 0.0000001
        AND abs(s.total_profit - p.total_profit) < 0.0000001
        AND abs(s.late_order_profit - p.late_order_profit) < 0.0000001
        AND abs(s.success_rate - p.success_rate::numeric) < 1e-12
        AND abs(s.late_order_rate - p.late_order_rate::numeric) < 1e-12,
        false
    ) AS matches_python
FROM summary_by_ship_mode AS s
FULL JOIN python_by_ship_mode AS p USING (scenario, ship_mode);

CREATE TEMP TABLE reconciliation_by_region AS
SELECT
    coalesce(s.scenario, p.scenario) AS scenario,
    coalesce(s.region, p.region) AS region,
    coalesce(
        s.orders = p.orders
        AND s.successful_orders = p.successful_orders
        AND s.late_orders = p.late_orders
        AND abs(s.total_sales - p.total_sales) < 0.0000001
        AND abs(s.late_order_sales - p.late_order_sales) < 0.0000001
        AND abs(s.total_profit - p.total_profit) < 0.0000001
        AND abs(s.late_order_profit - p.late_order_profit) < 0.0000001
        AND abs(s.success_rate - p.success_rate::numeric) < 1e-12
        AND abs(s.late_order_rate - p.late_order_rate::numeric) < 1e-12,
        false
    ) AS matches_python
FROM summary_by_region AS s
FULL JOIN python_by_region AS p USING (scenario, region);

CREATE TEMP TABLE reconciliation_by_month AS
SELECT
    coalesce(s.scenario, p.scenario) AS scenario,
    coalesce(to_char(s.order_month, 'YYYY-MM'), p.order_month) AS order_month,
    coalesce(
        s.orders = p.orders
        AND s.successful_orders = p.successful_orders
        AND s.late_orders = p.late_orders
        AND abs(s.total_sales - p.total_sales) < 0.0000001
        AND abs(s.late_order_sales - p.late_order_sales) < 0.0000001
        AND abs(s.total_profit - p.total_profit) < 0.0000001
        AND abs(s.late_order_profit - p.late_order_profit) < 0.0000001
        AND abs(s.success_rate - p.success_rate::numeric) < 1e-12
        AND abs(s.late_order_rate - p.late_order_rate::numeric) < 1e-12,
        false
    ) AS matches_python
FROM summary_by_month AS s
FULL JOIN python_by_month AS p
  ON p.scenario = s.scenario
 AND p.order_month = to_char(s.order_month, 'YYYY-MM');

-- ---------------------------------------------------------------------------
-- 7. Print results and reconciliation status.
-- ---------------------------------------------------------------------------

\echo '=== overall SQL summary ==='
SELECT *
FROM summary_overall
ORDER BY array_position(ARRAY['base', 'calibrated', 'strict', 'lenient'], scenario);

\echo '=== SQL summary by ship mode ==='
SELECT *
FROM summary_by_ship_mode
ORDER BY array_position(ARRAY['base', 'calibrated', 'strict', 'lenient'], scenario), ship_mode;

\echo '=== SQL summary by region ==='
SELECT *
FROM summary_by_region
ORDER BY array_position(ARRAY['base', 'calibrated', 'strict', 'lenient'], scenario), region;

\echo '=== SQL summary by month ==='
SELECT *
FROM summary_by_month
ORDER BY array_position(ARRAY['base', 'calibrated', 'strict', 'lenient'], scenario), order_month;

\echo '=== overall reconciliation ==='
SELECT *
FROM reconciliation_overall
ORDER BY array_position(ARRAY['base', 'calibrated', 'strict', 'lenient'], scenario);

\echo '=== reconciliation failures by output ==='
SELECT 'overall' AS output, count(*) FILTER (WHERE NOT matches_python) AS failures FROM reconciliation_overall
UNION ALL
SELECT 'by_ship_mode', count(*) FILTER (WHERE NOT matches_python) FROM reconciliation_by_ship_mode
UNION ALL
SELECT 'by_region', count(*) FILTER (WHERE NOT matches_python) FROM reconciliation_by_region
UNION ALL
SELECT 'by_month', count(*) FILTER (WHERE NOT matches_python) FROM reconciliation_by_month;

ROLLBACK;

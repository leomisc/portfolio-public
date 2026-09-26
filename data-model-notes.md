# Data Model and Grain

This document describes the source grain, analysis facts, reporting dimensions, and key decisions used by the fulfillment-SLA project.

## Source and analysis facts

Time-to-ship classification is evaluated once per order. Sales, profit, discount, and product attributes remain on order lines.

### Observed source behavior

- `Row ID` is the unique identifier for an order line.
- One `Order ID` can contain multiple order lines.
- In this dataset, all lines for an `Order ID` share the same `Order Date`, `Ship Date`, `Ship Mode`, and location attributes.
- Empirical validation found no orders with different ship dates across their lines.

### Analysis model

`fact_orders` contains one row per `Order ID`. It holds the dates, ship mode, business days to ship, initial threshold, variance, and initial late flag. The scenario analysis applies other thresholds to this order-level input.

`fact_order_lines` contains one row per `Row ID` and retains `Order ID` for joining to orders. It includes `Product ID`, sales, quantity, discount, and profit. Sales and profit are aggregated to order grain before they are joined to scenario-level status.

The generated line fact retains the source columns only. SLA measures stay on `fact_orders` so order-level values are not duplicated across multiple order lines.

The transformation also writes a reporting star schema. The source-shaped `fact_order_lines.csv` remains the input to the Python and PostgreSQL analyses.

## Reporting star schema

The reporting model centers on `fact_order_lines_star`, with one row per `Row ID`. Each row references customer, location, product, ship mode, and two roles of the date dimension:

```text
dim_customer ────┐
dim_location ────┤
dim_product ─────┼── fact_order_lines_star
dim_ship_mode ───┤
dim_date ────────┘   (order_date_key and ship_date_key)
```

The fact contains:

- `row_id` and `order_id` as source identifiers;
- `order_date_key` and `ship_date_key` as role-playing date keys;
- surrogate keys for customer, location, product, and ship mode; and
- `sales`, `quantity`, `discount`, and `profit` as line-level measures.

The generated dimensions are `dim_date`, `dim_customer`, `dim_location`, `dim_product`, and `dim_ship_mode`.

### Dimension-key decisions

- `dim_location` uses a surrogate `location_key`. Its natural grain is a distinct Country/City/State/Postal Code/Region combination. Postal Code remains an attribute.
- `dim_date` contains a continuous calendar and is referenced by both `order_date_key` and `ship_date_key`.
- The source has 32 Product IDs with conflicting descriptions. `product_key` is assigned from the full Product ID/Product Name/Category/Sub-Category combination; Product ID alone is not treated as unique.
- `order_id` remains on the fact table as a source identifier. There is no separate order dimension.

The order-level `fact_orders` table remains separate because time-to-ship status is evaluated once per order. Repeating it on every line would make counts and financial joins prone to duplication.

`Sales`, `Quantity`, and `Profit` are additive at line grain. `Discount` is a rate and should not be summed.

### Validation rule

For every `Order ID`, all order lines must have consistent `Order Date`, `Ship Date`, `Ship Mode`, and location attributes before the order-level SLA model is used.

### Scope limitation

This order-centered model fits the observed Superstore data because each order's lines share a ship date. If an order can ship in parts, classification needs shipment-level or line-level dates and grain.

### Key design caution

`(Order ID, Product ID)` is not assumed to identify an order line. `Row ID` is the validated unique line key in this source.

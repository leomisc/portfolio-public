# Data Model Notes

## Source and analysis facts

The SLA analysis is centered on `Order`, while financial and product analysis remains at `Order Line` grain.

### Observed source behavior

- `Row ID` is the unique identifier for an order line.
- One `Order ID` can contain multiple order lines.
- In this dataset, all lines for an `Order ID` share the same `Order Date`, `Ship Date`, `Ship Mode`, and location attributes.
- Empirical validation found no orders with different ship dates across their lines.

### Proposed model

`fact_orders` contains one row per `Order ID` and is the primary SLA evaluation table. It includes order-level shipment fields and calculated SLA fields such as business days to ship, SLA days, SLA variance, and `is_late`.

`fact_order_lines` contains one row per `Row ID` and retains `Order ID` as a foreign key. It includes `Product ID`, sales, quantity, discount, and profit so financial impact can be analyzed and connected to products.

The generated line fact retains the source columns only. SLA measures stay on `fact_orders` so order-level values are not duplicated across multiple order lines.

Potential shared dimensions include customer, product, location, ship mode, and date.

The transformation also writes a reporting-oriented star schema alongside these
analysis facts. The existing `fact_order_lines.csv` remains source-shaped so the
Python and PostgreSQL SLA analysis keeps its existing contract.

## Reporting star schema

The reporting model is centered on `fact_order_lines_star`, at the grain of one
row per `Row ID` (one product line within one order). It connects directly to
these dimensions:

```text
                 dim_product
                      |
dim_customer | fact_order_lines_star | dim_location
                      |
                  dim_date
                      |
                dim_ship_mode
```

The fact contains:

- `row_id` and `order_id` as source identifiers;
- `order_date_key` and `ship_date_key` as role-playing date keys;
- surrogate keys for customer, location, product, and ship mode; and
- `sales`, `quantity`, `discount`, and `profit` as line-level measures.

The generated dimensions are `dim_date`, `dim_customer`, `dim_location`,
`dim_product`, and `dim_ship_mode`.

### Dimension-key decisions

- `dim_location` uses a surrogate `location_key`. Its natural grain is one
  distinct Country/City/State/Postal Code/Region combination. Postal Code is
  retained as an attribute, not used as the primary key.
- `dim_date` contains a continuous calendar and is referenced twice by the
  fact: once for order date and once for ship date.
- The source contains 32 Product IDs with conflicting product descriptions.
  Therefore, `product_key` is assigned from the full Product ID/Product
  Name/Category/Sub-Category combination. The original Product ID remains an
  attribute and is not assumed to be unique.
- `order_id` remains a degenerate fact attribute; a separate order dimension
  is intentionally out of scope.

The order-level `fact_orders` table remains separate because SLA status is
evaluated once per order. Repeating those measures on every order line would
make line-level joins prone to double counting.

`Sales`, `Quantity`, and `Profit` are additive at line grain. `Discount` is a
rate and should not be summed.

### Validation rule

For every `Order ID`, all order lines must have consistent `Order Date`, `Ship Date`, `Ship Mode`, and location attributes before the order-level SLA model is used.

### Scope limitation

This order-centered model is appropriate for the Superstore dataset because shipments are observed to move together. In a split-shipment environment, such as a vendor where different items ship at different times, SLA evaluation would need to remain at shipment or order-line grain.

### Key design caution

`(Order ID, Product ID)` may be a useful uniqueness check, but it should not be assumed to be a universal order-line key. `Row ID` is the safest primary key because it is provided as the unique line identifier.

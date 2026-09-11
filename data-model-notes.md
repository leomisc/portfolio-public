# Data Model Notes

## Order-centered SLA analysis

The SLA analysis is centered on `Order`, while financial and product analysis remains at `Order Line` grain.

### Observed source behavior

- `Row ID` is the unique identifier for an order line.
- One `Order ID` can contain multiple order lines.
- In this dataset, all lines for an `Order ID` share the same `Order Date`, `Ship Date`, `Ship Mode`, and location attributes.
- Empirical validation found no orders with different ship dates across their lines.

### Proposed model

`fact_orders` contains one row per `Order ID` and is the primary SLA evaluation table. It includes order-level shipment fields and calculated SLA fields such as business days to ship, SLA days, SLA variance, and `is_late`.

`fact_order_lines` contains one row per `Row ID` and retains `Order ID` as a foreign key. It includes `Product ID`, sales, quantity, discount, and profit so financial impact can be analyzed and connected to products.

Potential shared dimensions include customer, product, location, ship mode, and date.

### Validation rule

For every `Order ID`, all order lines must have consistent `Order Date`, `Ship Date`, `Ship Mode`, and location attributes before the order-level SLA model is used.

### Scope limitation

This order-centered model is appropriate for the Superstore dataset because shipments are observed to move together. In a split-shipment environment, such as a vendor where different items ship at different times, SLA evaluation would need to remain at shipment or order-line grain.

### Key design caution

`(Order ID, Product ID)` may be a useful uniqueness check, but it should not be assumed to be a universal order-line key. `Row ID` is the safest primary key because it is provided as the unique line identifier.

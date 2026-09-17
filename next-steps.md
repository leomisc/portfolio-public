# Next Steps: Fulfillment SLA Analysis

See [data-model-notes.md](data-model-notes.md) for the order-centered SLA design and its validation rule.

## Completed: source inspection and modeling decisions

- Extract `data/raw/superstore_dataset.zip`.
- Open `Sample - Superstore.csv` and review the first rows.
- Confirm the grain: one row per order line, identified by `Row ID`.
- Note the main fields: order/ship dates, ship mode, customer, location, product, sales, quantity, discount, and profit.
- Check a few multi-line orders and weekend dates.

The inspection confirmed 9,994 order-line rows, 9,994 unique `Row ID` values, 5,009 orders, one country, no missing values, and no inconsistent order-level fields. The tracked implementation is in `scripts/transform_superstore.py`, with tests in `tests/`.

## Completed: business rules

- Define the question: where does the shipping promise appear to break?
- Use an explicit, provisional SLA assumption:
  - Same Day: 0 business days
  - First Class: 1 business day
  - Second Class: 2 business days
  - Standard Class: 5 business days
- Decide and document that business days exclude weekends and the order date.
- State the limitation: the dataset has no official promised-delivery date, so this is modeled fulfillment performance.

## Completed: transformation

- Load with `encoding="cp1252"`.
- Parse dates explicitly as `%m/%d/%Y`.
- Preserve `Postal Code` as text.
- Validate required columns, `Row ID` uniqueness, dates, nulls, and row counts.
- Calculate calendar days, business days, SLA days, SLA variance, and an `is_late` flag.
- Keep the fact table at order-line grain.

The pipeline writes `fact_order_lines` at `Row ID` grain and `fact_orders` at `Order ID` grain. Order-level SLA fields are kept on `fact_orders` to avoid duplicating SLA measures across order lines.

## Completed: automated validation

- Reconcile input and output row counts.
- Confirm each `Order ID` has consistent dates and ship mode.

The exploratory notebook contains the manual spot checks for same-day, weekend, early, on-SLA, and late examples. The automated tests cover source profile, row count, keys, nulls, order consistency, holiday handling, SLA mapping, and fact-table grain.

One-day SLA sensitivity remains part of the analysis phase.

## Next: analyze and communicate

- Run analyses by ship mode, region, month, and SLA scenario.
- Decide whether results are counted by order, order line, or sales-weighted impact.
- Write the findings memo: where performance misses, operational impact, recommended action, and limitations.
- Write the defense document explaining data quality, joins, model design, SQL, and assumptions.

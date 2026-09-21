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

The pipeline writes `fact_order_lines` at `Row ID` grain and `fact_orders` at `Order ID` grain. Order-level SLA fields are kept on `fact_orders` to avoid duplicating SLA measures across order lines. It also writes a reporting star schema: `fact_order_lines_star` plus date, customer, location, product, and ship-mode dimensions. See [data-model-notes.md](data-model-notes.md).

## Completed: automated validation

- Reconcile input and output row counts.
- Confirm each `Order ID` has consistent dates and ship mode.

The exploratory notebook contains the manual spot checks for same-day, weekend, early, on-SLA, and late examples. The automated tests cover source profile, row count, keys, nulls, order consistency, holiday handling, SLA mapping, and fact-table grain.

SLA sensitivity remains part of the analysis phase. The analysis now includes the initial benchmark, strict and lenient one-day sensitivities, and a data-informed calibrated scenario.

## Completed: initial SLA analysis

The reproducible analysis is in `scripts/analyze_sla.py`, with tests in `tests/test_analyze_sla.py`. It reuses the holiday-aware business-day values from `fact_orders`, aggregates financials by `Order ID`, and writes initial, calibrated, strict, and lenient scenario summaries under `data/processed/analysis/`. See [analysis-notes.md](analysis-notes.md) for the results, comparison, and limitations.

## Completed: PostgreSQL reproduction

The PostgreSQL reproduction is in [sql/fulfillment_sla_analysis.sql](sql/fulfillment_sla_analysis.sql), with explanations in [sql/README.md](sql/README.md). It loads the processed facts with `\copy`, preserves their grains, aggregates financials to order grain, applies all four SLA scenarios, produces overall/ship-mode/region/month summaries, and reconciles the results to the Python output files.

The script has been structurally tested locally. A live PostgreSQL execution remains a supervised user step because `psql` is not installed on OmenLEO.

## Next: communication

- Review the PostgreSQL output on a machine with `psql` and confirm zero reconciliation failures.
- Review monthly results with order-volume context and challenge any unstable patterns.
- Lead with the calibrated scenario while showing the initial benchmark to make assumption sensitivity explicit.
- Write the findings memo: where performance misses, operational impact, recommended action, and limitations.
- Write the defense document explaining data quality, joins, model design, SQL, and assumptions.

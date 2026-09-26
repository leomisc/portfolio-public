# Superstore Fulfillment SLA Analysis

## Project question

How does time to shipment vary across service modes, regions, and product groups, and where should an operations team investigate further?

## Project summary

This project analyzes order-to-ship time in the public Superstore dataset. Because the source has no promised ship or delivery date, it applies explicit ship-mode thresholds and reports the sensitivity of the results to those assumptions.

Under the exploratory calibrated scenario, 826 of 5,009 orders (16.5%) exceed their time-to-ship threshold. Rates are 17.4% for First Class, 16.0% for Second Class, 17.6% for Standard Class, and 3.4% for Same Day. The thresholds were selected with reference to this dataset; these rates do not measure performance against an external promise.

The analysis compares regional volume and rates, annual ship-mode patterns, and selected product combinations. East has the lowest regional rate despite substantial volume. Among the selected cross-tab cells, Central × Standard Class × Binders has the largest sample: 46 of 200 orders (23.0%) exceed the threshold.

## What is included

- A validated Python transformation that preserves the source order-line grain and creates a separate one-row-per-order SLA fact.
- Holiday-aware business-day calculation with explicit endpoint rules.
- Four SLA scenarios: initial benchmark, calibrated, strict, and lenient.
- A reporting star schema with direct-key dimensions for dates, customers, locations, products, and ship modes.
- A PostgreSQL reproduction that aggregates financials at order grain before joining SLA status and reconciles its summaries to Python.
- Automated tests for source quality, grain, keys, dates, SLA logic, and star-schema foreign keys.
- Three reproducible SVG charts for regional volume, yearly ship-mode performance, and product hotspots.

## Approach

The project documents business rules, validates source data, separates order-level shipment measures from line-level financial measures, and presents rates with their order counts. The result is a reproducible starting point for an operational review.

## Documentation

- [README](README.md): public project overview and reproduction commands.
- [Findings memo](findings-memo.md): business findings, operational interpretation, recommendations, and limitations.
- [Technical defense](technical-defense.md): implementation choices, validation, SQL/Python responsibilities, and technical questions.
- [Analysis appendix](analysis-notes.md): definitions, calculations, cross-tab methodology, and interpretation limits.
- [Data model notes](data-model-notes.md): grain, keys, joins, dimensions, and scope constraints.
- [PostgreSQL reproduction notes](sql/README.md): SQL responsibilities and reconciliation approach.

## Data and scope

The dataset is public. The results describe shipment timing under modeled thresholds; they do not measure delivery to the customer or contractual SLA performance. The data does not establish causal financial loss or customer harm.

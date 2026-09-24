# Superstore Fulfillment SLA Analysis

> **Status:** Source inspection, validated transformation, SLA analysis, PostgreSQL reproduction, and reporting star-schema exports are implemented. Findings and final portfolio communication remain in progress.

## Project question

Where does a shipping promise break, what does it cost operationally, and what should change?

## What I built

I used the public Superstore dataset to model fulfillment performance from order placement through
shipment. Because the dataset contains no promised delivery date, I defined a transparent,
ship-mode-specific SLA and tested how the conclusions changed when that assumption moved by one
business day.

The implemented project includes:

- a Python transformation script that profiles the data, validates the grain, and produces the
  SLA facts plus a direct-key reporting star schema;
- documented business rules for SLA thresholds, business-day counting, holidays, lateness, and
  attainment targets;
- four SQL analyses covering baseline attainment, ship mode and region, monthly trends, and SLA
  sensitivity;
- automated tests covering source quality, grain, keys, dates, SLA logic, and star-schema foreign
  keys; and
- model documentation covering data quality, joins, grain, key choices, SQL choices, and
  limitations.

The reporting layer is centered on `fact_order_lines_star`, one row per product
line within an order, with direct links to `dim_date`, `dim_customer`,
`dim_location`, `dim_product`, and `dim_ship_mode`. The separate `fact_orders`
table remains at one row per order so SLA measures are not duplicated across
order lines. Generated reporting outputs are local ignored files under
`data/processed/`.

## Technical decisions

The reporting fact remains at order-line grain rather than being silently aggregated to orders. The
transformation asserts row counts, key uniqueness, foreign-key integrity, valid dates, and non-null
calculated fields. The SQL uses joins across validated facts, explicit scenario mappings, a date
spine, and sensitivity scenarios. The source contains repeated Product IDs with different product
descriptions, so the reporting layer uses a descriptor-based surrogate `product_key` and retains
the original Product ID as an attribute rather than assuming it is unique.

## Business value

The deliverable is designed to answer a practical operations question, not showcase tools in
isolation: identify where service performance misses the stated promise, distinguish robust findings
from assumption-sensitive ones, and recommend a concrete next action.

The remaining portfolio work is to write the findings memo and select the clearest charts or tables
for the final presentation.

## Data and confidentiality

This project uses public data. It demonstrates the same analysis pattern I use in production—turning
messy operational data into documented rules, validated transformations, and decision-ready
analysis—without exposing employer data or confidential figures.

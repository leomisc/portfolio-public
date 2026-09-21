# Superstore Fulfillment SLA Analysis

> **Status:** Source inspection, validated transformation, SLA analysis, PostgreSQL reproduction, and reporting star-schema exports are implemented. Findings and final portfolio communication remain in progress.

## Project question

Where does a shipping promise break, what does it cost operationally, and what should change?

## What I built

I used the public Superstore dataset to model fulfillment performance from order placement through
shipment. Because the dataset contains no promised delivery date, I defined a transparent,
ship-mode-specific SLA and tested how the conclusions changed when that assumption moved by one
business day.

The project includes:

- a Python transformation script that profiles the data, validates the grain, and produces a small
  star schema;
- documented business rules for SLA thresholds, business-day counting, holidays, lateness, and
  attainment targets;
- four SQL analyses covering baseline attainment, ship mode and region, monthly trends, and SLA
  sensitivity;
- a findings memo written for an operations manager; and
- a defense document covering data quality, joins, model design, SQL choices, and limitations.

## Technical decisions

The fact table remains at order-line grain rather than being silently aggregated to orders. The
transformation asserts row counts, key uniqueness, foreign-key integrity, valid dates, and non-null
calculated fields. The SQL uses joins across dimensions, window functions, a date spine, and
sensitivity scenarios.

## Business value

The deliverable is designed to answer a practical operations question, not showcase tools in
isolation: identify where service performance misses the stated promise, distinguish robust findings
from assumption-sensitive ones, and recommend a concrete next action.

## Data and confidentiality

This project uses public data. It demonstrates the same analysis pattern I use in production—turning
messy operational data into documented rules, validated transformations, and decision-ready
analysis—without exposing employer data or confidential figures.

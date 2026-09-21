# Fulfillment SLA Portfolio Status

Last verified: 2026-09-21

The reproducible Python and PostgreSQL analysis is implemented and the automated test suite passes. The remaining work is validation on a PostgreSQL-enabled machine, interpretation, and portfolio communication.

## Completed

### User

- Reviewed the raw Superstore CSV manually.
- Confirmed 9,994 order-line rows, 9,994 unique `Row ID` values, and 5,009 orders.
- Confirmed one country, no missing values, and consistent order-level fields.
- Approved order-level grain, holiday-aware business-day calculation, and SLA equality as success.
- Approved showing both the original and calibrated SLA assumptions.

### Agent

- Created the reproducible Python environment and documented dependencies.
- Built validated order-line and order-level fact tables.
- Added observed federal holidays for 2014–2017 and January 1, 2018.
- Implemented holiday-aware business-day calculations using the agreed endpoint rule: exclude the order date and include the ship date.
- Added automated validation and regression tests.
- Added SLA scenario analysis with order-level financial aggregation.
- Added a PostgreSQL reproduction with explicit scenario mappings, grain assertions, summaries, and Python reconciliation queries.
- Added four scenarios:
  - Initial benchmark: `0/1/2/5` for Same Day, First Class, Second Class, and Standard Class.
  - Calibrated: `0/2/3/4`.
  - Strict: one business day less, except Same Day remains zero.
  - Lenient: one business day more, except Same Day remains zero.
- Documented the results and limitations in [analysis-notes.md](analysis-notes.md).
- Added a direct-key reporting star schema with five dimensions and an order-line fact, while preserving the existing SLA fact-table contracts.
- Documented the source Product ID collision limitation and used a descriptor-based product key to preserve all line records.
- Verified 21 tests pass and regenerated the analysis outputs.

The calibrated scenario produces a more balanced comparison: First Class is 17.4% late, Second Class 16.0%, Standard Class 17.6%, and Same Day 3.4%.

## Remaining work

| Work item | Owner | Supervision needed |
|---|---|---|
| Run the PostgreSQL script and confirm zero reconciliation failures | User, on a PostgreSQL-enabled machine | Agent assists with diagnosis |
| Review SQL output and approve any unexplained differences | User | Agent assists with diagnosis |
| Review monthly results with order-volume context | Agent | User challenges unstable or misleading patterns |
| Draft the findings memo covering results, operational interpretation, financial context, and limitations | Agent | User edits wording and approves the final story |
| Draft the technical defense document covering data quality, grain, joins, dates, SQL, and assumptions | Agent | User reviews recruiter-facing explanations |
| Choose charts or tables for the portfolio presentation | User | Agent prepares alternatives if requested |
| Review and approve the final SLA interpretation | User | Required before publishing the portfolio work |
| Commit and push any new work, then pull it on the next workstation | User | Agent verifies repository alignment afterward |

## Working interpretation

Use the calibrated `0/2/3/4` scenario as the primary comparison because it produces similar late-rate ranges across the three non-Same-Day modes. Keep the initial `0/1/2/5` benchmark visible to show assumption sensitivity. Neither scenario is an official contractual SLA because the dataset does not contain promised-delivery fields.

## Current repository state

- Current branch: `main`, aligned with `origin/main` at `2f5a85f Fix SQL reconciliation tolerance`.
- The PostgreSQL reproduction is implemented and structurally tested locally; live execution is pending on a PostgreSQL-enabled workstation.
- Automated verification: `21 passed` with `pytest -q`.
- The latest analysis and star-schema outputs are local ignored artifacts under `data/processed/` and can be regenerated from the documented commands.
- The local untracked `AGENTS.md` instruction file was preserved and not modified.

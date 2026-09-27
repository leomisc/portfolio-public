# Superstore Fulfillment Timing — Portfolio Summary

## Question

Where does the time between order placement and shipment warrant closer operational review?

## Method

The public Superstore dataset contains 9,994 product-line records for 5,009 orders placed from 2014 through 2017. This project calculates holiday-aware business days from order date to ship date and compares orders with documented thresholds for each ship mode. Order-level shipment status is kept separate from line-level sales and profit to avoid double counting.

## Findings

Under the exploratory calibrated thresholds, 826 orders (16.5%) are classified as late. The result is sensitive to the assumption: the four scenarios produce overall rates from 0.7% to 47.2%. Regional volume alone does not explain the variation. In the product-level review, Central × Standard Class × Binders has the most classified-late orders of any eligible subcategory, mode, and region cell: 46 of 200 orders (23.0%). Smaller cells have higher rates, so both counts and percentages matter.

## Recommended next step

Record the actual promised ship or delivery date before using these results as a service scorecard. Until then, review the higher-volume combinations with their order counts alongside their modeled rates.

## Scope

The analysis measures time to shipment, not customer delivery. Its thresholds were selected for exploration and are not contractual promises. Sales and profit attached to classified-late orders are descriptive totals, not losses caused by shipment timing.

For methods, charts, and reproduction commands, see the [project README](README.md). The [findings memo](findings-memo.md) contains the full business interpretation.

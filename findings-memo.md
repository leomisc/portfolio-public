# Fulfillment SLA Findings

## Decision summary

The public Superstore dataset supports a review of time to shipment. It contains order and ship dates, ship mode, and financial measures, but no promised ship or delivery date. This analysis uses documented ship-mode thresholds and shows how the results change when those thresholds change.

The calibrated scenario uses `0/2/3/4` business days for Same Day, First Class, Second Class, and Standard Class. Under that scenario, 826 of 5,009 orders are late, for a 16.5% late-order rate. First Class, Second Class, and Standard Class fall into a similar range. Same Day is lower at 3.4%.

The calibrated thresholds were chosen after examining the observed distribution. Their similar rates across the three non-Same-Day modes should not be read as independent proof of similar service quality. The useful next steps are to establish an observed service promise and investigate higher-volume regional and product combinations.

## Calibrated scenario

| Ship mode | Orders | Late orders | Late-order rate |
|---|---:|---:|---:|
| Same Day | 264 | 9 | 3.4% |
| First Class | 787 | 137 | 17.4% |
| Second Class | 964 | 154 | 16.0% |
| Standard Class | 2,994 | 526 | 17.6% |
| Total | 5,009 | 826 | 16.5% |

The initial benchmark tells a different story. It assigns five business days to Standard Class, which is the maximum observed business-day shipment time. Standard Class therefore has no late orders under that assumption, while First Class is 46.6% late and Second Class is 40.0% late.

At a four-day threshold, the calibrated scenario classifies the 526 Standard Class orders that took exactly five business days as late. It provides a descriptive view of the modes, while the initial benchmark makes the sensitivity to the chosen thresholds clear.

## Sensitivity to the modeled SLA

| Scenario | SLA mapping | Late orders | Late-order rate | Late-order sales |
|---|---|---:|---:|---:|
| Lenient | `0/2/3/6` | 300 | 6.0% | $114,666.43 |
| Initial benchmark | `0/1/2/5` | 762 | 15.2% | $342,370.54 |
| Calibrated | `0/2/3/4` | 826 | 16.5% | $371,776.00 |
| Strict | `0/0/1/4` | 1,875 | 37.4% | $871,832.97 |

The sensitivity range is the reason to describe the SLA as modeled. The strict and lenient scenarios are useful stress tests, not recommended operating policies.

## Yearly and monthly results

The overall calibrated rate varies by about one percentage point across the four order years:

| Year | Late orders | Orders | Late-order rate |
|---|---:|---:|---:|
| 2014 | 162 | 969 | 16.7% |
| 2015 | 166 | 1,038 | 16.0% |
| 2016 | 211 | 1,315 | 16.0% |
| 2017 | 287 | 1,687 | 17.0% |

The largest monthly rates with at least 100 orders were September 2014 at 26.2% with 130 orders, August 2017 at 25.2% with 111 orders, and April 2017 at 24.1% with 116 orders. These are useful investigation points, but they are not enough to establish a recurring seasonal pattern.

## Regional volume and state context

The regional result is more useful when volume is shown beside the rate:

| Region | Orders | Late orders | Late-order rate |
|---|---:|---:|---:|
| Central | 1,175 | 212 | 18.0% |
| East | 1,401 | 208 | 14.8% |
| South | 822 | 137 | 16.7% |
| West | 1,611 | 269 | 16.7% |

![Regional volume and calibrated late rate](docs/assets/regional-volume-late-rate.svg)

East has the second-highest order volume and the lowest regional rate. West carries the largest workload and is close to the overall rate. Central has the highest rate despite fewer orders than East or West. These four regions do not show a consistent relationship between volume and the modeled late rate.

Across 16 region-year observations, the correlation between order volume and the modeled late rate is approximately `-0.06`. The four annual observations within each region are too few to support a reliable trend claim; the detailed calculations are in the [analysis appendix](analysis-notes.md).

State comparisons use a minimum of 100 orders. Among those states, Ohio was lowest at 12.3% and Pennsylvania was 13.9%. Illinois was highest at 18.8%, followed by Washington at 18.0%. States with very small order counts can produce more extreme percentages, but they are not strong evidence by themselves.

## Product and cross-tab findings

At category level, the rates are close: Office Supplies 16.7%, Technology 16.4%, and Furniture 16.1%. The category counts overlap because one order can contain products from more than one category, so they should not be added together.

Among subcategories with at least 50 orders, rates range from 13.2% for Copiers to 18.9% for Tables. The chart compares the nine highest-rate subcategory × ship mode × region cells with the eligible cell containing the most classified-late orders. Every cell has at least 30 distinct orders. Each bar shows classified-late and other orders; the label gives the rate.

![Stacked order counts for high-rate cells and the cell with the most classified-late orders](docs/assets/subcategory-hotspots.svg)

Central × Standard Class × Binders has the most classified-late orders among eligible cells: 46 of 200 orders (23.0%). Central × Second Class × Binders has a higher rate at 31.5%, based on 17 of 54 orders. The count difference explains why the first cell is a useful operational starting point, while the higher-rate cells remain investigation candidates. An order containing multiple subcategories can appear in more than one cell.

## Yearly ship-mode context

The annual pattern does not show a clean worsening or improvement across the non-Same-Day modes:

![Ship-mode trend by year](docs/assets/ship-mode-yearly-trend.svg)

Standard Class stays around 16%–18% under the calibrated thresholds; First Class moves between 14% and 19%. Same Day remains lower, with a smaller order count. The year-to-year variation points to specific mode and region combinations for review rather than a consistent overall trend.

## Financial interpretation

Under the calibrated scenario, $371,776.00 in sales and $46,153.31 in profit are associated with late orders. Those figures describe the orders classified as late. They are not estimates of lost sales, service penalties, or profit caused by lateness.

A sales-weighted order discount comparison shows late orders averaging 15.1% versus 15.5% for on-time orders. The correlation between late status and weighted discount is approximately `-0.008`, effectively zero.

Average order profit is $55.88 for late orders and $57.43 for on-time orders. The difference is small, and the correlation between late status and order profit is approximately `-0.002`. Within First Class and Second Class, late orders have lower average profit, but they do not have higher discounts. Standard Class moves in the opposite direction. The overall result is not a general discount or profit pattern.

## Recommended next action

1. Record the actual promised ship or delivery date and evaluate performance against the relevant promise.
2. Until that field exists, report time-to-ship rates by mode with one documented threshold set and a sensitivity range.
3. Review Central × Standard Class × Binders and compare similar orders across regions before changing a broad shipping policy.
4. Keep order volume beside monthly and cross-tab rates. Small groups can produce unstable percentages.
5. Treat sales and profit associated with classified-late orders as descriptive totals, not causal financial impact.

## Limitations

- The source has no observed service promise. The modeled thresholds are assumptions, not contract terms.
- The measured interval ends at shipment, not customer delivery.
- The data does not establish that lateness caused lost profit or customer harm.
- The monthly cohort uses order date. A ship-date cohort would answer a different question.
- The source shows orders moving together. A split-shipment environment would require shipment or order-line SLA evaluation.

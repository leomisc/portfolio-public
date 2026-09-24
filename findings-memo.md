# Fulfillment SLA Findings

## Decision summary

I used the public Superstore dataset to ask where a shipping promise appears to break, what the affected orders represent financially, and what an operations team should investigate next.

The source does not contain a promised delivery date. I therefore modeled a ship-mode-specific SLA instead of presenting the result as contractual performance. The calibrated scenario uses `0/2/3/4` business days for Same Day, First Class, Second Class, and Standard Class.

Under that scenario, 826 of 5,009 orders were late, for a 16.5% late-order rate. First Class, Second Class, and Standard Class fall into a similar range. Same Day is lower at 3.4%.

The practical conclusion is narrower than “the operation is late.” The data supports a ship-mode review and a better definition of the promise. It does not identify a causal cost or prove that discounting caused the late orders.

## What the calibrated scenario shows

| Ship mode | Orders | Late orders | Late-order rate |
|---|---:|---:|---:|
| First Class | 787 | 137 | 17.4% |
| Second Class | 964 | 154 | 16.0% |
| Standard Class | 2,994 | 526 | 17.6% |
| Same Day | 264 | 9 | 3.4% |
| Total | 5,009 | 826 | 16.5% |

The initial benchmark tells a different story. It assigns five business days to Standard Class, which is the maximum observed business-day shipment time. Standard Class therefore has no late orders under that assumption, while First Class is 46.6% late and Second Class is 40.0% late.

The calibrated scenario exposes the 526 Standard Class orders that took exactly five business days and gives a more balanced comparison across the non-Same-Day modes. That is why I use it as the primary presentation scenario while keeping the initial benchmark visible.

## Sensitivity to the modeled SLA

| Scenario | SLA mapping | Late orders | Late-order rate | Late-order sales |
|---|---|---:|---:|---:|
| Lenient | `0/2/3/6` | 300 | 6.0% | $114,666.43 |
| Initial benchmark | `0/1/2/5` | 762 | 15.2% | $342,370.54 |
| Calibrated | `0/2/3/4` | 826 | 16.5% | $371,776.00 |
| Strict | `0/0/1/4` | 1,875 | 37.4% | $871,832.97 |

The sensitivity range is the reason to describe the SLA as modeled. The strict and lenient scenarios are useful stress tests, not recommended operating policies.

## Monthly results

The calibrated late rate is stable at the annual level:

| Year | Late orders | Orders | Late-order rate |
|---|---:|---:|---:|
| 2014 | 162 | 969 | 16.7% |
| 2015 | 166 | 1,038 | 16.0% |
| 2016 | 211 | 1,315 | 16.0% |
| 2017 | 287 | 1,687 | 17.0% |

The largest monthly rates with at least 100 orders were September 2014 at 26.2% with 130 orders, August 2017 at 25.2% with 111 orders, and April 2017 at 24.1% with 116 orders. These are useful investigation points, but they are not enough to establish a recurring seasonal pattern.

## Financial interpretation

Under the calibrated scenario, $371,776.00 in sales and $46,153.31 in profit are associated with late orders. Those figures describe the orders classified as late. They are not estimates of lost sales, service penalties, or profit caused by lateness.

I also compared late and on-time orders using a sales-weighted order discount. Late orders averaged 15.1% versus 15.5% for on-time orders. The correlation between late status and weighted discount was approximately `-0.008`, which is effectively zero.

Average order profit was $55.88 for late orders and $57.43 for on-time orders. The difference was small, and the correlation between late status and order profit was approximately `-0.002`. Within First Class and Second Class, late orders had lower average profit, but they did not have higher discounts. Standard Class moved in the opposite direction. The overall result is therefore not a general discount or profit pattern.

## Recommended next action

1. Replace the modeled SLA with an observed promised-delivery field if the business has one.
2. Until that field exists, monitor late-order rates by ship mode using one documented threshold set.
3. Investigate the First Class and Second Class process separately from the Standard Class threshold question.
4. Keep order volume beside monthly rates. Small months can produce unstable percentages.
5. Treat late-order sales and profit as exposure measures, not causal financial impact.

## Limitations

- The source has no official promised-delivery date.
- The modeled SLA is a transparent assumption, not a contract.
- The data does not establish that lateness caused lost profit or customer harm.
- The monthly cohort uses order date. A ship-date cohort would answer a different question.
- The source shows orders moving together. A split-shipment environment would require shipment or order-line SLA evaluation.

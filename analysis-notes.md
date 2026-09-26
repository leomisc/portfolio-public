# SLA Analysis Appendix

This appendix records the definitions, calculations, and interpretation limits behind the fulfillment-SLA findings. It is a technical reference for the analysis rather than a project diary.

## Definitions

- `Business Days to Ship` comes from the holiday-aware transformation and excludes weekends, observed federal holidays in the source period, and the order date while including the ship date.
- Initial benchmark SLA: Same Day 0, First Class 1, Second Class 2, Standard Class 5 business days.
- Calibrated scenario: Same Day 0, First Class 2, Second Class 3, Standard Class 4 business days. These values were selected using the observed distribution and are not independent service targets.
- A result is successful when `Business Days to Ship <= Scenario SLA Days`.
- A result is late when `Business Days to Ship > Scenario SLA Days`.
- Sales and profit associated with classified-late orders are descriptive totals, not estimated costs caused by lateness.
- Sensitivity exception: Same Day remains at a zero-business-day threshold in the strict and lenient scenarios. The one-day shift applies only to modes with a positive initial threshold.

The observed federal holiday dates are defined in `scripts/transform_superstore.py`. The calendar covers the 2014–2017 source period and January 1, 2018, which is needed for the source's early-January 2018 shipments.

## Initial benchmark results

| Measure | Result |
|---|---:|
| Orders | 5,009 |
| Successful orders | 4,247 |
| Late orders | 762 |
| Late-order rate | 15.2% |
| Sales associated with late orders | $342,370.54 |
| Profit associated with late orders | $44,242.06 |

By ship mode, the initial benchmark is:

| Ship mode | Orders | Late orders | Late-order rate |
|---|---:|---:|---:|
| Same Day | 264 | 9 | 3.4% |
| First Class | 787 | 367 | 46.6% |
| Second Class | 964 | 386 | 40.0% |
| Standard Class | 2,994 | 0 | 0.0% |

The initial benchmark result is concentrated in First Class and Second Class. Regional rates are relatively close, ranging from 14.7% in the West to 15.8% in the Central region, so the current evidence does not support a strong regional conclusion under that scenario.

## Calibrated scenario results

The calibrated thresholds put the three non-Same-Day modes in a similar observed range by design:

| Ship mode | Orders | Late orders | Late-order rate |
|---|---:|---:|---:|
| Same Day | 264 | 9 | 3.4% |
| First Class | 787 | 137 | 17.4% |
| Second Class | 964 | 154 | 16.0% |
| Standard Class | 2,994 | 526 | 17.6% |

Standard Class has no late orders under the five-day initial benchmark because five days is the maximum observed business-day shipment time. A four-day scenario exposes the 526 orders that took exactly five business days.

## SLA sensitivity

| Scenario | Late orders | Late-order rate | Late-order sales |
|---|---:|---:|---:|
| Initial benchmark, 0/1/2/5 | 762 | 15.2% | $342,370.54 |
| Calibrated, 0/2/3/4 | 826 | 16.5% | $371,776.00 |
| Strict, one day less | 1,875 | 37.4% | $871,832.97 |
| Lenient, one day more | 300 | 6.0% | $114,666.43 |

The classifications are sensitive to the thresholds. Under the initial benchmark, First and Second Class have much higher modeled late rates than Standard Class. Under the calibrated scenario, the three non-Same-Day modes range from 16.0% to 17.6%. That convergence is partly a result of choosing thresholds from the observed data. Neither scenario measures an official contractual SLA.

## Order-level discount and profit diagnostic

Late and on-time orders are compared under the calibrated scenario after aggregating line-level values to `Order ID`. Discount is measured as a sales-weighted order rate because discount is not additive.

| Measure | Late orders | On-time orders |
|---|---:|---:|
| Sales-weighted discount | 15.1% | 15.5% |
| Average order profit | $55.88 | $57.43 |
| Average profit margin | 11.9% | 11.2% |

The correlation between late status and weighted discount is approximately `-0.008`. The correlation between late status and order profit is approximately `-0.002`. These values do not support a general relationship between lateness, higher discounting, or lower profit. First Class and Second Class show lower average profit among late orders, but the pattern changes by ship mode and is not explained by higher discounts.

## Regional volume and state diagnostics

The calibrated regional summary is:

| Region | Orders | Late orders | Late-order rate |
|---|---:|---:|---:|
| Central | 1,175 | 212 | 18.0% |
| East | 1,401 | 208 | 14.8% |
| South | 822 | 137 | 16.7% |
| West | 1,611 | 269 | 16.7% |

The correlation between region-year order volume and late rate is approximately `-0.06` across all 16 region-year observations. Within-region correlations, using four annual observations each, are Central `-0.02`, East `+0.81`, South `+0.35`, and West `+0.30`. These values are exploratory only.

For state comparisons, the minimum is 100 orders. The lower-rate large samples were Ohio at 12.3% (29 of 236) and Pennsylvania at 13.9% (40 of 288). The higher-rate large samples were Illinois at 18.8% (52 of 276) and Washington at 18.0% (46 of 256). Small states were not used to make portfolio-level claims.

## Category and subcategory diagnostics

Category rates were close: Office Supplies 16.7% (624 late of 3,742 orders containing the category), Technology 16.4% (253 of 1,544), and Furniture 16.1% (284 of 1,764). These category counts overlap because an order can contain more than one category.

Among subcategories with at least 50 orders, the highest rates were Tables 18.9% (58 of 307), Phones 18.4% (150 of 814), Binders 18.4% (242 of 1,316), Supplies 18.2% (34 of 187), and Art 17.9% (131 of 731). The lowest were Copiers 13.2% (9 of 68), Bookcases 13.8% (31 of 224), and Chairs 14.1% (81 of 576).

For three-way combinations, the line data is reduced to distinct `(Order ID, Sub-Category)` pairs, joined to order-level mode, region, and late status, and filtered to cells with at least 30 orders. The chart includes the nine highest-rate eligible cells and the eligible cell with the most classified-late orders, then sorts them by late-order count. Central × Standard Class × Binders leads by count at 46 of 200 (23.0%). Central × Second Class × Binders has the highest rate at 31.5% (17 of 54). Counts across subcategories overlap because an order may contain more than one subcategory.

The [project README](README.md) gives the commands for regenerating the analysis and charts.

## Interpretation limits

- The source contains no promised ship or delivery date. The thresholds are modeling assumptions.
- The measured interval ends at shipment, not delivery to the customer.
- The dataset does not establish that late shipment caused lost profit or customer harm.
- Small monthly and cross-tab groups can produce unstable rates and need volume context.
- The output uses order date as the monthly cohort. A ship-date cohort could answer a different operational question.
- The order-centered model is appropriate because the source shows orders moving together. Split shipments would require shipment or order-line SLA evaluation.

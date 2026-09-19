# SLA Analysis Notes

## Definitions

- `Business Days to Ship` comes from the holiday-aware transformation and excludes weekends, observed federal holidays in the source period, and the order date while including the ship date.
- Initial benchmark SLA: Same Day 0, First Class 1, Second Class 2, Standard Class 5 business days.
- Calibrated SLA scenario: Same Day 0, First Class 2, Second Class 3, Standard Class 4 business days. These values reflect the observed distribution and are not confirmed contractual promises.
- A result is successful when `Business Days to Ship <= Scenario SLA Days`.
- A result is late when `Business Days to Ship > Scenario SLA Days`.
- Financial impact is associated with late orders. It is not a causal estimate of cost.
- Sensitivity exception: Same Day remains a zero-business-day promise in the strict and lenient scenarios. The one-day shift applies only to modes with a positive base SLA.

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

By ship mode, the base scenario is:

| Ship mode | Orders | Late orders | Late-order rate |
|---|---:|---:|---:|
| First Class | 787 | 367 | 46.6% |
| Second Class | 964 | 386 | 40.0% |
| Same Day | 264 | 9 | 3.4% |
| Standard Class | 2,994 | 0 | 0.0% |

The initial benchmark result is therefore concentrated in First Class and Second Class. Regional rates are relatively close, ranging from 14.7% in the West to 15.8% in the Central region, so the current evidence does not support a strong regional conclusion.

## Calibrated scenario results

The calibrated scenario moves each non-Same-Day mode toward a similar observed service band:

| Ship mode | Orders | Late orders | Late-order rate |
|---|---:|---:|---:|
| First Class | 787 | 137 | 17.4% |
| Second Class | 964 | 154 | 16.0% |
| Same Day | 264 | 9 | 3.4% |
| Standard Class | 2,994 | 526 | 17.6% |

Standard Class has no late orders under the five-day initial benchmark because five days is the maximum observed business-day shipment time. A four-day scenario exposes the 526 orders that took exactly five business days.

## SLA sensitivity

| Scenario | Late orders | Late-order rate | Late-order sales |
|---|---:|---:|---:|
| Initial benchmark, 0/1/2/5 | 762 | 15.2% | $342,370.54 |
| Calibrated, 0/2/3/4 | 826 | 16.5% | $371,776.00 |
| Strict, one day less | 1,875 | 37.4% | $871,832.97 |
| Lenient, one day more | 300 | 6.0% | $114,666.43 |

The conclusion is assumption-sensitive. Under the initial benchmark, First and Second Class appear to perform much worse than Standard Class. Under the calibrated scenario, all three non-Same-Day modes have late rates between 16.0% and 17.6%, which is a more balanced comparison. The overall late rate rises slightly because the calibrated scenario adds 526 Standard Class late orders while removing 230 First Class and 232 Second Class late orders.

The calibrated scenario should be the primary presentation scenario for comparing ship modes, while the initial benchmark should remain visible as an assumption-sensitivity comparison. Neither should be described as the official contractual SLA because the source does not contain promised-delivery fields.

## Interpretation limits

- The source contains no official promised-delivery date. The SLA is a transparent modeling assumption.
- The dataset does not establish that late shipment caused lost profit or customer harm.
- Small monthly groups can produce unstable rates and need volume context.
- The output uses order date as the monthly cohort. A ship-date cohort could answer a different operational question.

Generated detail and summaries are local ignored outputs under `data/processed/analysis/`. The reproducible entry point is:

```powershell
.\.venv\Scripts\python.exe -m scripts.analyze_sla
```

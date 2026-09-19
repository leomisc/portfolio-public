# SLA Analysis Notes

## Definitions

- `Business Days to Ship` comes from the holiday-aware transformation and excludes weekends, observed federal holidays in the source period, and the order date while including the ship date.
- Base SLA: Same Day 0, First Class 1, Second Class 2, Standard Class 5 business days.
- A result is successful when `Business Days to Ship <= Scenario SLA Days`.
- A result is late when `Business Days to Ship > Scenario SLA Days`.
- Financial impact is associated with late orders. It is not a causal estimate of cost.

The observed federal holiday dates are defined in `scripts/transform_superstore.py`. The calendar covers the 2014–2017 source period and January 1, 2018, which is needed for the source's early-January 2018 shipments.

## Base scenario results

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

The base result is therefore concentrated in First Class and Second Class. Regional rates are relatively close, ranging from 14.7% in the West to 15.8% in the Central region, so the current evidence does not support a strong regional conclusion.

## SLA sensitivity

| Scenario | Late orders | Late-order rate | Late-order sales |
|---|---:|---:|---:|
| Base | 762 | 15.2% | $342,370.54 |
| Strict, one day less | 1,875 | 37.4% | $871,832.97 |
| Lenient, one day more | 300 | 6.0% | $114,666.43 |

The conclusion that First Class and Second Class have the most misses remains visible across the scenarios, but the absolute late rate is assumption-sensitive. Standard Class has no misses under the base and lenient assumptions, but 17.6% under the strict assumption.

## Interpretation limits

- The source contains no official promised-delivery date. The SLA is a transparent modeling assumption.
- The dataset does not establish that late shipment caused lost profit or customer harm.
- Small monthly groups can produce unstable rates and need volume context.
- The output uses order date as the monthly cohort. A ship-date cohort could answer a different operational question.

Generated detail and summaries are local ignored outputs under `data/processed/analysis/`. The reproducible entry point is:

```powershell
.\.venv\Scripts\python.exe -m scripts.analyze_sla
```

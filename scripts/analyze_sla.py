"""Analyze order-level SLA performance and financial impact."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd


SCENARIO_SHIFTS = {
    "base": 0,
    "strict": -1,
    "lenient": 1,
}


def aggregate_order_financials(lines: pd.DataFrame) -> pd.DataFrame:
    """Aggregate line-level financial measures to one row per order."""
    return (
        lines.groupby("Order ID", as_index=False)
        .agg(
            **{
                "Order Sales": ("Sales", "sum"),
                "Order Profit": ("Profit", "sum"),
                "Order Line Count": ("Row ID", "size"),
            }
        )
    )


def _scenario_sla_days(
    base_sla_days: pd.Series,
    ship_modes: pd.Series,
    shift: int,
) -> pd.Series:
    """Shift SLA days while keeping Same Day at zero."""
    shifted = (base_sla_days + shift).clip(lower=0)
    return shifted.where(ship_modes != "Same Day", 0).astype("int64")


def build_scenario_orders(
    orders: pd.DataFrame,
    lines: pd.DataFrame,
) -> pd.DataFrame:
    """Create one row per order and SLA scenario."""
    financials = aggregate_order_financials(lines)
    base_orders = orders.merge(
        financials,
        on="Order ID",
        how="left",
        validate="one_to_one",
    )
    if base_orders[["Order Sales", "Order Profit"]].isna().any().any():
        raise ValueError("Every order must have matching order-line financials")

    scenarios: list[pd.DataFrame] = []
    for scenario, shift in SCENARIO_SHIFTS.items():
        current = base_orders.copy()
        current["Scenario"] = scenario
        current["Scenario SLA Days"] = _scenario_sla_days(
            current["SLA Days"],
            current["Ship Mode"],
            shift,
        )
        current["Is Late"] = (
            current["Business Days to Ship"] > current["Scenario SLA Days"]
        )
        current["Is Success"] = ~current["Is Late"]
        current["Late Order Sales"] = current["Order Sales"].where(
            current["Is Late"],
            0.0,
        )
        current["Late Order Profit"] = current["Order Profit"].where(
            current["Is Late"],
            0.0,
        )
        current["Order Month"] = (
            pd.to_datetime(current["Order Date"])
            .dt.to_period("M")
            .astype(str)
        )
        scenarios.append(current)

    return pd.concat(scenarios, ignore_index=True)


def summarize_sla(
    scenario_orders: pd.DataFrame,
    group_by: Sequence[str] = (),
) -> pd.DataFrame:
    """Summarize order-level SLA results by scenario and dimensions."""
    group_fields = ["Scenario", *group_by]
    summary = (
        scenario_orders.groupby(group_fields, dropna=False, as_index=False)
        .agg(
            **{
                "Orders": ("Order ID", "nunique"),
                "Successful Orders": ("Is Success", "sum"),
                "Late Orders": ("Is Late", "sum"),
                "Total Sales": ("Order Sales", "sum"),
                "Late Order Sales": ("Late Order Sales", "sum"),
                "Total Profit": ("Order Profit", "sum"),
                "Late Order Profit": ("Late Order Profit", "sum"),
            }
        )
    )
    summary["Success Rate"] = (
        summary["Successful Orders"] / summary["Orders"]
    )
    summary["Late Order Rate"] = summary["Late Orders"] / summary["Orders"]
    summary["Scenario"] = pd.Categorical(
        summary["Scenario"],
        categories=list(SCENARIO_SHIFTS),
        ordered=True,
    )
    return summary.sort_values(group_fields).reset_index(drop=True)


def build_analysis(
    orders: pd.DataFrame,
    lines: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build scenario-level detail and the requested summary tables."""
    scenario_orders = build_scenario_orders(orders, lines)
    return {
        "scenario_orders": scenario_orders,
        "overall": summarize_sla(scenario_orders),
        "by_ship_mode": summarize_sla(scenario_orders, ["Ship Mode"]),
        "by_region": summarize_sla(scenario_orders, ["Region"]),
        "by_month": summarize_sla(scenario_orders, ["Order Month"]),
    }


def _read_inputs(
    orders_path: Path,
    lines_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    orders = pd.read_csv(orders_path, parse_dates=["Order Date"])
    lines = pd.read_csv(lines_path)
    return orders, lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--orders",
        type=Path,
        default=Path("data/processed/fact_orders.csv"),
    )
    parser.add_argument(
        "--lines",
        type=Path,
        default=Path("data/processed/fact_order_lines.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/analysis"),
    )
    args = parser.parse_args(argv)

    orders, lines = _read_inputs(args.orders, args.lines)
    outputs = build_analysis(orders, lines)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_names = {
        "scenario_orders": "scenario_orders.csv",
        "overall": "sla_summary_overall.csv",
        "by_ship_mode": "sla_summary_by_ship_mode.csv",
        "by_region": "sla_summary_by_region.csv",
        "by_month": "sla_summary_by_month.csv",
    }
    for key, filename in output_names.items():
        outputs[key].to_csv(args.output_dir / filename, index=False)

    print(outputs["overall"].to_string(index=False))
    print(f"Wrote analysis outputs to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

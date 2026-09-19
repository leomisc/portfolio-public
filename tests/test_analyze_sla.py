import pandas as pd

from scripts.analyze_sla import (
    aggregate_order_financials,
    build_scenario_orders,
    summarize_sla,
)


def make_orders():
    return pd.DataFrame({
        "Order ID": ["A", "B", "C"],
        "Order Date": pd.to_datetime(["2017-01-02", "2017-02-03", "2017-02-04"]),
        "Ship Mode": ["Standard Class", "First Class", "Same Day"],
        "Region": ["West", "East", "West"],
        "Business Days to Ship": [5, 2, 0],
        "SLA Days": [5, 1, 0],
        "SLA Variance": [0, 1, 0],
        "Is Late": [False, True, False],
    })


def make_lines():
    return pd.DataFrame({
        "Row ID": ["1", "2", "3", "4"],
        "Order ID": ["A", "A", "B", "C"],
        "Sales": [10.0, 5.0, 20.0, 7.0],
        "Profit": [1.0, 2.0, -3.0, 1.0],
    })


def test_financials_are_aggregated_once_per_order():
    result = aggregate_order_financials(make_lines())

    row_a = result.loc[result["Order ID"] == "A"].iloc[0]
    assert row_a["Order Sales"] == 15.0
    assert row_a["Order Profit"] == 3.0
    assert row_a["Order Line Count"] == 2


def test_scenarios_treat_sla_equality_as_success_and_keep_same_day_zero():
    result = build_scenario_orders(make_orders(), make_lines())

    base_a = result[(result["Scenario"] == "base") & (result["Order ID"] == "A")].iloc[0]
    strict_a = result[(result["Scenario"] == "strict") & (result["Order ID"] == "A")].iloc[0]
    lenient_c = result[
        (result["Scenario"] == "lenient") & (result["Order ID"] == "C")
    ].iloc[0]

    assert not bool(base_a["Is Late"])
    assert strict_a["Scenario SLA Days"] == 4
    assert bool(strict_a["Is Late"])
    assert lenient_c["Scenario SLA Days"] == 0
    assert not bool(lenient_c["Is Late"])


def test_calibrated_scenario_uses_observed_sla_mapping():
    result = build_scenario_orders(make_orders(), make_lines())

    calibrated = result[result["Scenario"] == "calibrated"].set_index("Order ID")

    assert calibrated.loc["A", "Scenario SLA Days"] == 4
    assert bool(calibrated.loc["A", "Is Late"])
    assert calibrated.loc["B", "Scenario SLA Days"] == 2
    assert not bool(calibrated.loc["B", "Is Late"])
    assert calibrated.loc["C", "Scenario SLA Days"] == 0


def test_lenient_scenario_keeps_same_day_at_zero_by_design():
    orders = make_orders()
    orders.loc[orders["Order ID"] == "C", "Business Days to Ship"] = 1

    result = build_scenario_orders(orders, make_lines())
    same_day = result[result["Order ID"] == "C"]

    assert same_day["Scenario SLA Days"].tolist() == [0, 0, 0, 0]
    assert same_day["Is Late"].tolist() == [True, True, True, True]


def test_summary_calculates_order_rate_and_late_financial_impact():
    scenarios = build_scenario_orders(make_orders(), make_lines())
    result = summarize_sla(scenarios, group_by=["Ship Mode"])

    assert result["Scenario"].drop_duplicates().tolist() == [
        "base",
        "calibrated",
        "strict",
        "lenient",
    ]

    base_first_class = result[
        (result["Scenario"] == "base")
        & (result["Ship Mode"] == "First Class")
    ].iloc[0]

    assert base_first_class["Orders"] == 1
    assert base_first_class["Late Orders"] == 1
    assert base_first_class["Late Order Rate"] == 1.0
    assert base_first_class["Late Order Sales"] == 20.0
    assert base_first_class["Late Order Profit"] == -3.0

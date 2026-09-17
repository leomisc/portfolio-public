import pandas as pd
import pytest

from scripts.transform_superstore import (
    add_sla_fields,
    build_fact_orders,
    calculate_business_days,
)


def test_business_days_excludes_order_date_and_includes_ship_date():
    order_dates = pd.Series(
        pd.to_datetime(["2024-01-05", "2024-01-08", "2024-01-08"])
    )
    ship_dates = pd.Series(
        pd.to_datetime(["2024-01-08", "2024-01-09", "2024-01-08"])
    )

    result = calculate_business_days(order_dates, ship_dates, holidays=[])

    assert result.tolist() == [1, 1, 0]


def test_business_days_excludes_supplied_holiday():
    order_dates = pd.Series(pd.to_datetime(["2024-07-03"]))
    ship_dates = pd.Series(pd.to_datetime(["2024-07-05"]))

    result = calculate_business_days(
        order_dates,
        ship_dates,
        holidays=["2024-07-04"],
    )

    assert result.tolist() == [1]


def test_add_sla_fields_maps_modes_and_flags_late_rows():
    frame = pd.DataFrame({
        "Ship Mode": ["Same Day", "First Class", "Standard Class"],
        "Business Days to Ship": [0, 2, 5],
    })

    result = add_sla_fields(frame)

    assert result["SLA Days"].tolist() == [0, 1, 5]
    assert result["SLA Variance"].tolist() == [0, 1, 0]
    assert result["Is Late"].tolist() == [False, True, False]


def test_build_fact_orders_collapses_consistent_order_lines():
    frame = pd.DataFrame({
        "Row ID": ["1", "2"],
        "Order ID": ["A", "A"],
        "Order Date": pd.to_datetime(["2017-01-03", "2017-01-03"]),
        "Ship Date": pd.to_datetime(["2017-01-05", "2017-01-05"]),
        "Ship Mode": ["Second Class", "Second Class"],
        "Customer ID": ["C1", "C1"],
        "Country": ["United States", "United States"],
        "City": ["Test City", "Test City"],
        "State": ["Test State", "Test State"],
        "Postal Code": ["12345", "12345"],
        "Region": ["West", "West"],
        "Business Days to Ship": [2, 2],
        "SLA Days": [2, 2],
        "SLA Variance": [0, 0],
        "Is Late": [False, False],
    })

    result = build_fact_orders(frame)

    assert len(result) == 1
    assert result.loc[0, "Order ID"] == "A"
    assert result.loc[0, "Business Days to Ship"] == 2


def test_unknown_ship_mode_is_rejected():
    frame = pd.DataFrame({
        "Ship Mode": ["Unknown Mode"],
        "Business Days to Ship": [1],
    })

    with pytest.raises(ValueError, match="Unknown ship modes"):
        add_sla_fields(frame)

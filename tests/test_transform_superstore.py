import pandas as pd
import pytest

from scripts.transform_superstore import (
    add_sla_fields,
    build_fact_orders,
    build_star_schema,
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


def test_default_federal_holiday_calendar_excludes_observed_holiday():
    order_dates = pd.Series(pd.to_datetime(["2015-07-02"]))
    ship_dates = pd.Series(pd.to_datetime(["2015-07-06"]))

    result = calculate_business_days(order_dates, ship_dates)

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
        "Calendar Days to Ship": [2, 2],
        "Business Days to Ship": [2, 2],
        "SLA Days": [2, 2],
        "SLA Variance": [0, 0],
        "Is Late": [False, False],
    })

    result = build_fact_orders(frame)

    assert len(result) == 1
    assert result.loc[0, "Order ID"] == "A"
    assert result.loc[0, "Calendar Days to Ship"] == 2
    assert result.loc[0, "Business Days to Ship"] == 2


def test_build_fact_orders_rejects_inconsistent_order_fields():
    frame = pd.DataFrame({
        "Order ID": ["A", "A"],
        "Order Date": pd.to_datetime(["2017-01-03", "2017-01-04"]),
        "Ship Date": pd.to_datetime(["2017-01-05", "2017-01-05"]),
        "Ship Mode": ["Second Class", "Second Class"],
        "Customer ID": ["C1", "C1"],
        "Country": ["United States", "United States"],
        "City": ["Test City", "Test City"],
        "State": ["Test State", "Test State"],
        "Postal Code": ["12345", "12345"],
        "Region": ["West", "West"],
        "Calendar Days to Ship": [2, 1],
        "Business Days to Ship": [2, 2],
        "SLA Days": [2, 2],
        "SLA Variance": [0, 0],
        "Is Late": [False, False],
    })

    with pytest.raises(ValueError, match="inconsistent"):
        build_fact_orders(frame)


def test_unknown_ship_mode_is_rejected():
    frame = pd.DataFrame({
        "Ship Mode": ["Unknown Mode"],
        "Business Days to Ship": [1],
    })

    with pytest.raises(ValueError, match="Unknown ship modes"):
        add_sla_fields(frame)


def test_build_star_schema_connects_line_fact_directly_to_dimensions():
    frame = pd.DataFrame({
        "Row ID": ["1", "2"],
        "Order ID": ["A", "A"],
        "Order Date": pd.to_datetime(["2017-01-03", "2017-01-03"]),
        "Ship Date": pd.to_datetime(["2017-01-05", "2017-01-05"]),
        "Ship Mode": ["Second Class", "Second Class"],
        "Customer ID": ["C1", "C1"],
        "Customer Name": ["Customer One", "Customer One"],
        "Segment": ["Consumer", "Consumer"],
        "Country": ["United States", "United States"],
        "City": ["Test City", "Test City"],
        "State": ["Test State", "Test State"],
        "Postal Code": ["12345", "12345"],
        "Region": ["West", "West"],
        "Product ID": ["P1", "P2"],
        "Product Name": ["Product One", "Product Two"],
        "Category": ["Technology", "Office Supplies"],
        "Sub-Category": ["Phones", "Paper"],
        "Sales": [10.0, 20.0],
        "Quantity": [1, 2],
        "Discount": [0.0, 0.1],
        "Profit": [2.0, 4.0],
    })

    tables = build_star_schema(frame)

    assert set(tables) == {
        "dim_date",
        "dim_customer",
        "dim_location",
        "dim_product",
        "dim_ship_mode",
        "fact_order_lines_star",
    }
    fact = tables["fact_order_lines_star"]
    assert len(fact) == 2
    assert fact["row_id"].is_unique
    assert fact["customer_key"].nunique() == 1
    assert fact["product_key"].nunique() == 2
    assert fact["order_date_key"].eq(20170103).all()
    assert fact["ship_date_key"].eq(20170105).all()
    assert set(fact["product_key"]).issubset(tables["dim_product"]["product_key"])
    assert set(fact["location_key"]).issubset(tables["dim_location"]["location_key"])
    assert set(fact["ship_mode_key"]).issubset(tables["dim_ship_mode"]["ship_mode_key"])


def test_build_star_schema_preserves_product_id_collisions():
    frame = pd.DataFrame({
        "Row ID": ["1", "2"],
        "Order ID": ["A", "B"],
        "Order Date": pd.to_datetime(["2017-01-03", "2017-01-04"]),
        "Ship Date": pd.to_datetime(["2017-01-05", "2017-01-06"]),
        "Ship Mode": ["Second Class", "Second Class"],
        "Customer ID": ["C1", "C1"],
        "Customer Name": ["Customer One", "Customer One"],
        "Segment": ["Consumer", "Consumer"],
        "Country": ["United States", "United States"],
        "City": ["Test City", "Test City"],
        "State": ["Test State", "Test State"],
        "Postal Code": ["12345", "12345"],
        "Region": ["West", "West"],
        "Product ID": ["P1", "P1"],
        "Product Name": ["Product One", "Product Two"],
        "Category": ["Technology", "Technology"],
        "Sub-Category": ["Phones", "Phones"],
        "Sales": [10.0, 20.0],
        "Quantity": [1, 2],
        "Discount": [0.0, 0.1],
        "Profit": [2.0, 4.0],
    })

    tables = build_star_schema(frame)

    assert len(tables["dim_product"]) == 2
    assert tables["dim_product"]["product_id"].nunique() == 1
    assert tables["fact_order_lines_star"]["product_key"].nunique() == 2

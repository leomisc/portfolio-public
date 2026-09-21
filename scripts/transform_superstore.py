"""Transform the public Superstore source into SLA analysis fact tables."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd


SLA_DAYS: dict[str, int] = {
    "Same Day": 0,
    "First Class": 1,
    "Second Class": 2,
    "Standard Class": 5,
}

EXPECTED_SOURCE_ROWS = 9994

FEDERAL_HOLIDAYS = np.array(
    [
        # 2014
        "2014-01-01",
        "2014-01-20",
        "2014-02-17",
        "2014-05-26",
        "2014-07-04",
        "2014-09-01",
        "2014-10-13",
        "2014-11-11",
        "2014-11-27",
        "2014-12-25",
        # 2015
        "2015-01-01",
        "2015-01-19",
        "2015-02-16",
        "2015-05-25",
        "2015-07-03",
        "2015-09-07",
        "2015-10-12",
        "2015-11-11",
        "2015-11-26",
        "2015-12-25",
        # 2016
        "2016-01-01",
        "2016-01-18",
        "2016-02-15",
        "2016-05-30",
        "2016-07-04",
        "2016-09-05",
        "2016-10-10",
        "2016-11-11",
        "2016-11-24",
        "2016-12-26",
        # 2017
        "2017-01-02",
        "2017-01-16",
        "2017-02-20",
        "2017-05-29",
        "2017-07-04",
        "2017-09-04",
        "2017-10-09",
        "2017-11-10",
        "2017-11-23",
        "2017-12-25",
        # The source contains shipments in early 2018.
        "2018-01-01",
    ],
    dtype="datetime64[D]",
)

REQUIRED_COLUMNS = {
    "Row ID",
    "Order ID",
    "Order Date",
    "Ship Date",
    "Ship Mode",
    "Customer ID",
    "Country",
    "City",
    "State",
    "Postal Code",
    "Region",
    "Product ID",
    "Category",
    "Sub-Category",
    "Product Name",
    "Sales",
    "Quantity",
    "Discount",
    "Profit",
}

ORDER_LEVEL_FIELDS = [
    "Order Date",
    "Ship Date",
    "Ship Mode",
    "Customer ID",
    "Country",
    "City",
    "State",
    "Postal Code",
    "Region",
]

FACT_ORDER_FIELDS = [
    "Order ID",
    *ORDER_LEVEL_FIELDS,
    "Calendar Days to Ship",
    "Business Days to Ship",
    "SLA Days",
    "SLA Variance",
    "Is Late",
]

STAR_LOCATION_FIELDS = [
    "Country",
    "City",
    "State",
    "Postal Code",
    "Region",
]

STAR_LOCATION_FIELDS_TO_SNAKE = [
    "country",
    "city",
    "state",
    "postal_code",
    "region",
]

STAR_PRODUCT_FIELDS = [
    "Product ID",
    "Product Name",
    "Category",
    "Sub-Category",
]

STAR_PRODUCT_FIELDS_TO_SNAKE = [
    "product_id",
    "product_name",
    "category",
    "sub_category",
]

STAR_FACT_FIELDS = [
    "row_id",
    "order_id",
    "order_date_key",
    "ship_date_key",
    "customer_key",
    "location_key",
    "product_key",
    "ship_mode_key",
    "sales",
    "quantity",
    "discount",
    "profit",
]


def load_source(path: str | Path) -> pd.DataFrame:
    """Load the raw CSV with the project's required encoding and types."""
    frame = pd.read_csv(
        path,
        encoding="cp1252",
        dtype={
            "Row ID": "string",
            "Order ID": "string",
            "Customer ID": "string",
            "Postal Code": "string",
            "Product ID": "string",
        },
    )
    frame["Order Date"] = pd.to_datetime(
        frame["Order Date"],
        format="%m/%d/%Y",
    ).dt.normalize()
    frame["Ship Date"] = pd.to_datetime(
        frame["Ship Date"],
        format="%m/%d/%Y",
    ).dt.normalize()
    return frame


def validate_source(
    frame: pd.DataFrame,
    expected_rows: int | None = EXPECTED_SOURCE_ROWS,
) -> None:
    """Raise ValueError when the source violates the analysis contract."""
    missing_columns = REQUIRED_COLUMNS - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    if expected_rows is not None and len(frame) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, found {len(frame)}"
        )

    if frame["Row ID"].isna().any():
        raise ValueError("Row ID contains null values")
    if not frame["Row ID"].is_unique:
        raise ValueError("Row ID must be unique")
    if frame.isna().any().any():
        raise ValueError("Source contains null values")

    if (frame["Ship Date"] < frame["Order Date"]).any():
        raise ValueError("Ship Date cannot precede Order Date")
    if (frame["Sales"] < 0).any():
        raise ValueError("Sales cannot be negative")
    if (frame["Quantity"] <= 0).any():
        raise ValueError("Quantity must be positive")
    if not frame["Discount"].between(0, 1).all():
        raise ValueError("Discount must be between 0 and 1")

    unknown_modes = sorted(set(frame["Ship Mode"]) - set(SLA_DAYS))
    if unknown_modes:
        raise ValueError(f"Unknown ship modes: {unknown_modes}")

    variation = frame.groupby("Order ID")[ORDER_LEVEL_FIELDS].nunique(
        dropna=False
    )
    inconsistent_orders = variation[variation.gt(1).any(axis=1)]
    if not inconsistent_orders.empty:
        order_ids = inconsistent_orders.index.tolist()
        raise ValueError(
            f"Order-level fields are inconsistent for orders: {order_ids}"
        )


def calculate_business_days(
    order_dates: pd.Series,
    ship_dates: pd.Series,
    holidays: Sequence[str] | np.ndarray = FEDERAL_HOLIDAYS,
) -> pd.Series:
    """Count business days in the interval (order date, ship date]."""
    starts = pd.to_datetime(order_dates).dt.normalize() + pd.Timedelta(days=1)
    ends = pd.to_datetime(ship_dates).dt.normalize() + pd.Timedelta(days=1)
    holiday_values = np.asarray(holidays, dtype="datetime64[D]")
    values = np.busday_count(
        starts.to_numpy(dtype="datetime64[D]"),
        ends.to_numpy(dtype="datetime64[D]"),
        holidays=holiday_values,
    )
    return pd.Series(values, index=order_dates.index, name="Business Days to Ship")


def add_sla_fields(frame: pd.DataFrame) -> pd.DataFrame:
    """Add SLA days, variance, and late-status fields."""
    result = frame.copy()
    unknown_modes = sorted(set(result["Ship Mode"]) - set(SLA_DAYS))
    if unknown_modes:
        raise ValueError(f"Unknown ship modes: {unknown_modes}")

    result["SLA Days"] = result["Ship Mode"].map(SLA_DAYS).astype("int64")
    result["SLA Variance"] = (
        result["Business Days to Ship"] - result["SLA Days"]
    )
    result["Is Late"] = result["SLA Variance"] > 0
    return result


def build_fact_orders(frame: pd.DataFrame) -> pd.DataFrame:
    """Collapse validated order-line data to one row per order."""
    fields_to_check = [field for field in FACT_ORDER_FIELDS if field != "Order ID"]
    variation = frame.groupby("Order ID")[fields_to_check].nunique(
        dropna=False
    )
    inconsistent_orders = variation[variation.gt(1).any(axis=1)]
    if not inconsistent_orders.empty:
        order_ids = inconsistent_orders.index.tolist()
        raise ValueError(
            f"Order-level fields are inconsistent for orders: {order_ids}"
        )

    return (
        frame[FACT_ORDER_FIELDS]
        .drop_duplicates(subset=["Order ID"], keep="first")
        .reset_index(drop=True)
    )


def _build_dimension(
    frame: pd.DataFrame,
    natural_columns: list[str],
    attribute_columns: list[str],
    rename_map: dict[str, str],
    key_column: str,
    label: str,
) -> pd.DataFrame:
    """Build a deterministic dimension and reject conflicting attributes."""
    if attribute_columns:
        variation = frame.groupby(natural_columns, dropna=False)[
            attribute_columns
        ].nunique(dropna=False)
        if variation.gt(1).any(axis=1).any():
            raise ValueError(f"{label} attributes are inconsistent")

    columns = [*natural_columns, *attribute_columns]
    dimension = (
        frame[columns]
        .drop_duplicates()
        .sort_values(natural_columns)
        .drop_duplicates(subset=natural_columns, keep="first")
        .reset_index(drop=True)
        .rename(columns=rename_map)
    )
    dimension.insert(0, key_column, range(1, len(dimension) + 1))
    return dimension


def build_star_schema(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build direct-key dimensions and an order-line star-schema fact."""
    dimensions = {
        "dim_customer": _build_dimension(
            frame,
            ["Customer ID"],
            ["Customer Name", "Segment"],
            {
                "Customer ID": "customer_id",
                "Customer Name": "customer_name",
                "Segment": "segment",
            },
            "customer_key",
            "Customer",
        ),
        "dim_location": _build_dimension(
            frame,
            STAR_LOCATION_FIELDS,
            [],
            {
                "Country": "country",
                "City": "city",
                "State": "state",
                "Postal Code": "postal_code",
                "Region": "region",
            },
            "location_key",
            "Location",
        ),
        "dim_product": _build_dimension(
            frame,
            STAR_PRODUCT_FIELDS,
            [],
            {
                "Product ID": "product_id",
                "Product Name": "product_name",
                "Category": "category",
                "Sub-Category": "sub_category",
            },
            "product_key",
            "Product",
        ),
        "dim_ship_mode": _build_dimension(
            frame,
            ["Ship Mode"],
            [],
            {"Ship Mode": "ship_mode"},
            "ship_mode_key",
            "Ship mode",
        ),
    }

    min_date = min(frame["Order Date"].min(), frame["Ship Date"].min())
    max_date = max(frame["Order Date"].max(), frame["Ship Date"].max())
    dates = pd.date_range(min_date, max_date, freq="D")
    dim_date = pd.DataFrame({"date": dates})
    dim_date.insert(
        0,
        "date_key",
        dim_date["date"].dt.strftime("%Y%m%d").astype("int64"),
    )
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.month_name()
    dim_date["day_of_week"] = dim_date["date"].dt.day_name()
    dim_date["is_weekend"] = dim_date["date"].dt.dayofweek >= 5
    dimensions["dim_date"] = dim_date

    fact = frame[
        [
            "Row ID",
            "Order ID",
            "Order Date",
            "Ship Date",
            "Customer ID",
            *STAR_PRODUCT_FIELDS,
            "Ship Mode",
            *STAR_LOCATION_FIELDS,
            "Sales",
            "Quantity",
            "Discount",
            "Profit",
        ]
    ].rename(
        columns={
            "Row ID": "row_id",
            "Order ID": "order_id",
            "Order Date": "order_date",
            "Ship Date": "ship_date",
            "Customer ID": "customer_id",
            "Product ID": "product_id",
            "Product Name": "product_name",
            "Category": "category",
            "Sub-Category": "sub_category",
            "Ship Mode": "ship_mode",
            "Country": "country",
            "City": "city",
            "State": "state",
            "Postal Code": "postal_code",
            "Region": "region",
            "Sales": "sales",
            "Quantity": "quantity",
            "Discount": "discount",
            "Profit": "profit",
        }
    )

    date_lookup = dimensions["dim_date"][["date", "date_key"]]
    fact = fact.merge(
        date_lookup.rename(columns={"date": "order_date", "date_key": "order_date_key"}),
        on="order_date",
        how="left",
        validate="many_to_one",
    ).merge(
        date_lookup.rename(columns={"date": "ship_date", "date_key": "ship_date_key"}),
        on="ship_date",
        how="left",
        validate="many_to_one",
    )
    fact = fact.merge(
        dimensions["dim_customer"][["customer_id", "customer_key"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
    ).merge(
        dimensions["dim_product"][
            [*STAR_PRODUCT_FIELDS_TO_SNAKE, "product_key"]
        ],
        on=STAR_PRODUCT_FIELDS_TO_SNAKE,
        how="left",
        validate="many_to_one",
    ).merge(
        dimensions["dim_ship_mode"][["ship_mode", "ship_mode_key"]],
        on="ship_mode",
        how="left",
        validate="many_to_one",
    ).merge(
        dimensions["dim_location"][
            ["country", "city", "state", "postal_code", "region", "location_key"]
        ],
        on=STAR_LOCATION_FIELDS_TO_SNAKE,
        how="left",
        validate="many_to_one",
    )

    fact = fact[STAR_FACT_FIELDS]
    if fact.isna().any().any():
        raise ValueError("Star fact contains null dimension keys")
    return {
        "dim_date": dimensions["dim_date"],
        "dim_customer": dimensions["dim_customer"],
        "dim_location": dimensions["dim_location"],
        "dim_product": dimensions["dim_product"],
        "dim_ship_mode": dimensions["dim_ship_mode"],
        "fact_order_lines_star": fact,
    }


def transform_source(
    source_path: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load, validate, enrich, and split the source into two fact tables."""
    frame = load_source(source_path)
    validate_source(frame)
    fact_order_lines = frame.copy()

    order_sla = frame.copy()
    order_sla["Calendar Days to Ship"] = (
        order_sla["Ship Date"] - order_sla["Order Date"]
    ).dt.days
    order_sla["Business Days to Ship"] = calculate_business_days(
        order_sla["Order Date"],
        order_sla["Ship Date"],
    )
    fact_orders = build_fact_orders(add_sla_fields(order_sla))
    return fact_order_lines, fact_orders


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/raw/Sample - Superstore.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
    )
    args = parser.parse_args(argv)

    fact_order_lines, fact_orders = transform_source(args.source)
    star_schema = build_star_schema(fact_order_lines)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fact_order_lines.to_csv(
        args.output_dir / "fact_order_lines.csv",
        index=False,
        date_format="%Y-%m-%d",
    )
    fact_orders.to_csv(
        args.output_dir / "fact_orders.csv",
        index=False,
        date_format="%Y-%m-%d",
    )
    for table_name, table in star_schema.items():
        table.to_csv(
            args.output_dir / f"{table_name}.csv",
            index=False,
            date_format="%Y-%m-%d",
        )
    print(f"Wrote {len(fact_order_lines):,} order lines")
    print(f"Wrote {len(fact_orders):,} orders")
    print("Wrote star-schema dimensions and order-line fact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

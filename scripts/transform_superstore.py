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
    print(f"Wrote {len(fact_order_lines):,} order lines")
    print(f"Wrote {len(fact_orders):,} orders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from pathlib import Path

import pytest

from scripts.transform_superstore import (
    FACT_ORDER_FIELDS,
    ORDER_LEVEL_FIELDS,
    load_source,
    transform_source,
)


SOURCE_PATH = Path("data/raw/Sample - Superstore.csv")

pytestmark = pytest.mark.skipif(
    not SOURCE_PATH.exists(),
    reason="Extract the public source archive before running real-source checks",
)


def test_real_source_matches_documented_profile():
    frame = load_source(SOURCE_PATH)

    assert frame.shape == (9994, 21)
    assert frame["Row ID"].is_unique
    assert frame["Order ID"].nunique() == 5009
    assert frame.isna().sum().sum() == 0
    assert frame["Country"].unique().tolist() == ["United States"]


def test_real_source_has_consistent_order_level_fields():
    frame = load_source(SOURCE_PATH)
    variation = frame.groupby("Order ID")[ORDER_LEVEL_FIELDS].nunique(
        dropna=False
    )

    assert not variation.gt(1).any(axis=1).any()


def test_transformed_fact_tables_have_expected_grain():
    fact_order_lines, fact_orders = transform_source(SOURCE_PATH)

    assert len(fact_order_lines) == 9994
    assert len(fact_orders) == 5009
    assert fact_order_lines["Row ID"].is_unique
    assert fact_orders["Order ID"].is_unique
    assert set(FACT_ORDER_FIELDS).issubset(fact_orders.columns)

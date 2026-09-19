from pathlib import Path


SQL_PATH = Path("sql/fulfillment_sla_analysis.sql")


def test_sql_reproduction_has_explicit_sla_scenarios_and_grain_controls():
    sql = SQL_PATH.read_text(encoding="utf-8")

    expected_mappings = [
        "('base', 'Same Day', 0)",
        "('base', 'First Class', 1)",
        "('base', 'Second Class', 2)",
        "('base', 'Standard Class', 5)",
        "('calibrated', 'Same Day', 0)",
        "('calibrated', 'First Class', 2)",
        "('calibrated', 'Second Class', 3)",
        "('calibrated', 'Standard Class', 4)",
    ]

    for mapping in expected_mappings:
        assert mapping in sql

    assert "CREATE TEMP TABLE order_financials" in sql
    assert "CREATE TEMP TABLE scenario_orders" in sql
    assert "(o.business_days_to_ship > s.scenario_sla_days) AS is_late" in sql
    assert "count(*) FILTER (WHERE is_late)" in sql
    assert "reconciliation_overall" in sql

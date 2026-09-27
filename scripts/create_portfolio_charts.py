"""Create the small set of portfolio charts used in the written analysis.

The script deliberately writes SVG directly so the repository does not need a
plotting dependency just to regenerate its documentation assets. The numbers
come from the local processed outputs produced by ``transform_superstore.py``
and ``analyze_sla.py``.
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path

import pandas as pd


BACKGROUND = "#ffffff"
TEXT = "#1f2937"
MUTED = "#6b7280"
GRID = "#d1d5db"
BLUE = "#2563eb"
ORANGE = "#d97706"
GREEN = "#059669"
PURPLE = "#7c3aed"
RED = "#dc2626"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(x: float, y: float, value: object, *, size: int = 13, fill: str = TEXT,
         anchor: str = "start", weight: str = "400", rotate: float | None = None) -> str:
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}px" fill="{fill}" text-anchor="{anchor}" '
        f'font-weight="{weight}"{transform}>{esc(value)}</text>'
    )


def line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = GRID,
         width: float = 1, dash: str | None = None) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{extra}/>'


def rect(x: float, y: float, width: float, height: float, *, fill: str = "none",
         stroke: str = "none", radius: float = 0) -> str:
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" fill="{fill}" stroke="{stroke}" rx="{radius:.1f}"/>'


def svg_document(width: int, height: int, body: str, *, title: str, description: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="chart-title chart-description">'
        f'<title id="chart-title">{esc(title)}</title>'
        f'<desc id="chart-description">{esc(description)}</desc>'
        f'{rect(0, 0, width, height, fill=BACKGROUND)}{body}</svg>\n'
    )


def save(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_inputs(project_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    processed = project_root / "data" / "processed"
    scenario = pd.read_csv(processed / "analysis" / "scenario_orders.csv")
    lines = pd.read_csv(processed / "fact_order_lines.csv")
    scenario["Order Date"] = pd.to_datetime(scenario["Order Date"])
    scenario = scenario[scenario["Scenario"] == "calibrated"].copy()
    return scenario, lines


def regional_volume_chart(scenario: pd.DataFrame) -> str:
    data = (
        scenario.groupby("Region", as_index=False)
        .agg(orders=("Order ID", "nunique"), late_orders=("Is Late", "sum"))
    )
    data["late_rate"] = data["late_orders"] / data["orders"]
    data = data.set_index("Region").loc[["Central", "East", "South", "West"]].reset_index()

    width, height = 900, 470
    left, right, top, bottom = 78, 250, 78, 78
    plot_w, plot_h = width - left - right, height - top - bottom
    x_min, x_max = 700, 1800
    y_min, y_max = 0.13, 0.20
    x_map = lambda value: left + (value - x_min) / (x_max - x_min) * plot_w
    y_map = lambda value: top + (y_max - value) / (y_max - y_min) * plot_h

    parts = [
        text(left, 31, "Regional volume vs. calibrated late-order rate", size=21, weight="700"),
        text(left, 53, "Each point is a region; a higher point means a higher share of orders shipped late.", size=12, fill=MUTED),
    ]
    for tick in [800, 1000, 1200, 1400, 1600, 1800]:
        x = x_map(tick)
        parts.append(line(x, top, x, top + plot_h, stroke=GRID, width=0.8))
        parts.append(text(x, top + plot_h + 24, f"{tick:,}", size=11, fill=MUTED, anchor="middle"))
    for tick in [0.14, 0.16, 0.18, 0.20]:
        y = y_map(tick)
        parts.append(line(left, y, left + plot_w, y, stroke=GRID, width=0.8))
        parts.append(text(left - 12, y + 4, f"{tick:.0%}", size=11, fill=MUTED, anchor="end"))
    overall = scenario["Is Late"].mean()
    parts.append(line(left, y_map(overall), left + plot_w, y_map(overall), stroke=ORANGE, width=1.4, dash="5 5"))
    colors = {"Central": RED, "East": BLUE, "South": GREEN, "West": PURPLE}
    for row in data.itertuples(index=False):
        x, y = x_map(row.orders), y_map(row.late_rate)
        radius = 10 + row.late_orders / 55
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{colors[row.Region]}" fill-opacity="0.82"/>')
    legend_x = left + plot_w + 30
    parts.append(text(legend_x, top + 4, "REGION", size=11, fill=MUTED, weight="700"))
    for index, row in enumerate(data.itertuples(index=False)):
        legend_y = top + 34 + index * 61
        parts.append(f'<circle cx="{legend_x + 8:.1f}" cy="{legend_y - 4:.1f}" r="6" fill="{colors[row.Region]}"/>')
        parts.append(text(legend_x + 22, legend_y, f"{row.Region} · {row.late_rate:.1%}", size=12, weight="700"))
        parts.append(text(legend_x + 22, legend_y + 18, f"{row.orders:,} orders · {row.late_orders} late", size=11, fill=MUTED))
    parts.append(line(legend_x, top + 302, legend_x + 23, top + 302, stroke=ORANGE, width=1.4, dash="5 5"))
    parts.append(text(legend_x + 31, top + 306, f"Overall: {overall:.1%}", size=11, fill=MUTED))

    parts.extend([
        line(left, top + plot_h, left + plot_w, top + plot_h, stroke=TEXT, width=1.1),
        line(left, top, left, top + plot_h, stroke=TEXT, width=1.1),
        text(left + plot_w / 2, height - 25, "Distinct orders", size=12, fill=MUTED, anchor="middle"),
        text(20, top + plot_h / 2, "Late-order rate", size=12, fill=MUTED, anchor="middle", rotate=-90),
        text(width - 35, height - 25, "Bubble size = late orders", size=11, fill=MUTED, anchor="end"),
    ])
    return svg_document(
        width,
        height,
        "".join(parts),
        title="Regional volume versus calibrated late-order rate",
        description="A scatter plot comparing distinct orders and calibrated late-order rate across Central, East, South, and West.",
    )


def ship_mode_trend_chart(scenario: pd.DataFrame) -> str:
    grouped = (
        scenario.assign(Year=scenario["Order Date"].dt.year)
        .groupby(["Ship Mode", "Year"], as_index=False)
        .agg(orders=("Order ID", "nunique"), late_orders=("Is Late", "sum"))
    )
    grouped["late_rate"] = grouped["late_orders"] / grouped["orders"]
    modes = ["Same Day", "First Class", "Second Class", "Standard Class"]
    colors = {"Same Day": GREEN, "First Class": BLUE, "Second Class": ORANGE, "Standard Class": PURPLE}

    width, height = 960, 500
    left, right, top, bottom = 78, 220, 86, 78
    plot_w, plot_h = width - left - right, height - top - bottom
    years = [2014, 2015, 2016, 2017]
    x_map = lambda year: left + (year - years[0]) / (years[-1] - years[0]) * plot_w
    y_map = lambda value: top + (0.22 - value) / 0.22 * plot_h
    parts = [
        text(left, 31, "Calibrated late-order rate by ship mode", size=21, weight="700"),
        text(left, 53, "The mode gap is mostly Same Day versus the other three modes; the annual pattern is not a clean trend.", size=12, fill=MUTED),
    ]
    for tick in [0.00, 0.05, 0.10, 0.15, 0.20]:
        y = y_map(tick)
        parts.append(line(left, y, left + plot_w, y, stroke=GRID, width=0.8))
        parts.append(text(left - 12, y + 4, f"{tick:.0%}", size=11, fill=MUTED, anchor="end"))
    for year in years:
        x = x_map(year)
        parts.append(line(x, top, x, top + plot_h, stroke=GRID, width=0.8))
        parts.append(text(x, top + plot_h + 24, str(year), size=11, fill=MUTED, anchor="middle"))

    for mode in modes:
        rows = grouped[grouped["Ship Mode"] == mode].sort_values("Year")
        points = [(x_map(row.Year), y_map(row.late_rate), row.late_rate) for row in rows.itertuples()]
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points)
        parts.append(f'<polyline points="{path}" fill="none" stroke="{colors[mode]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
        for x, y, rate in points:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{colors[mode]}"/>')
    legend_x = left + plot_w + 23
    parts.append(text(legend_x, top - 18, "2017 rate", size=11, fill=MUTED, weight="700"))
    for index, mode in enumerate(modes):
        row = grouped[(grouped["Ship Mode"] == mode) & (grouped["Year"] == 2017)].iloc[0]
        legend_y = top + index * 28
        parts.append(line(legend_x, legend_y, legend_x + 18, legend_y, stroke=colors[mode], width=3))
        parts.append(text(legend_x + 27, legend_y + 4, f"{mode}: {row.late_rate:.1%}", size=11, fill=colors[mode], weight="700"))

    parts.extend([
        line(left, top + plot_h, left + plot_w, top + plot_h, stroke=TEXT, width=1.1),
        line(left, top, left, top + plot_h, stroke=TEXT, width=1.1),
        text(left + plot_w / 2, height - 25, "Order year", size=12, fill=MUTED, anchor="middle"),
        text(20, top + plot_h / 2, "Late-order rate", size=12, fill=MUTED, anchor="middle", rotate=-90),
    ])
    return svg_document(
        width,
        height,
        "".join(parts),
        title="Calibrated late-order rate by ship mode and year",
        description="A line chart showing annual calibrated late-order rates for Same Day, First Class, Second Class, and Standard Class from 2014 through 2017.",
    )


def hotspot_chart(scenario: pd.DataFrame, lines: pd.DataFrame) -> str:
    order_attributes = scenario[["Order ID", "Ship Mode", "Region", "Is Late"]].drop_duplicates("Order ID")
    order_subcategories = lines[["Order ID", "Sub-Category"]].drop_duplicates()
    combo = order_subcategories.merge(order_attributes, on="Order ID", validate="many_to_one")
    data = (
        combo.groupby(["Sub-Category", "Ship Mode", "Region"], as_index=False)
        .agg(orders=("Order ID", "nunique"), late_orders=("Is Late", "sum"))
    )
    data["late_rate"] = data["late_orders"] / data["orders"]
    eligible = data[data["orders"] >= 30]
    highest_rates = eligible.sort_values(["late_rate", "orders"], ascending=[False, False]).head(9)
    highest_late_count = eligible.sort_values(["late_orders", "orders"], ascending=[False, False]).head(1)
    data = pd.concat([highest_rates, highest_late_count]).drop_duplicates(
        ["Sub-Category", "Ship Mode", "Region"]
    ).sort_values(["late_orders", "orders"], ascending=[False, False]).copy()
    data["label"] = data.apply(lambda r: f"{r['Sub-Category']} · {r['Ship Mode']} · {r['Region']}", axis=1)
    leader_key = tuple(highest_late_count.iloc[0][["Sub-Category", "Ship Mode", "Region"]])

    width, height = 1040, 560
    left, right, top, bottom = 280, 245, 118, 80
    plot_w, plot_h = width - left - right, height - top - bottom
    x_map = lambda value: left + value / 250 * plot_w
    row_h = plot_h / len(data)
    parts = [
        text(left, 31, "High rates and late-order volume", size=21, weight="700"),
        text(left, 53, "Calibrated scenario: nine highest-rate cells plus the cell with most late orders; minimum 30 orders.", size=12, fill=MUTED),
        rect(left, 75, 13, 13, fill=BLUE),
        text(left + 19, 86, "Late orders", size=11, fill=MUTED),
        rect(left + 118, 75, 13, 13, fill="#cbd5e1"),
        text(left + 137, 86, "Other orders", size=11, fill=MUTED),
        rect(left + 263, 75, 13, 13, fill=ORANGE),
        text(left + 282, 86, "Highest late-order count", size=11, fill=MUTED),
    ]
    for tick in [0, 50, 100, 150, 200, 250]:
        x = x_map(tick)
        parts.append(line(x, top, x, top + plot_h, stroke=GRID, width=0.8))
        parts.append(text(x, top + plot_h + 23, str(tick), size=11, fill=MUTED, anchor="middle"))

    for index, (_, row) in enumerate(data.iterrows()):
        y = top + index * row_h + row_h * 0.19
        bar_h = row_h * 0.62
        key = (row["Sub-Category"], row["Ship Mode"], row["Region"])
        color = ORANGE if key == leader_key else BLUE
        parts.append(text(left - 12, y + bar_h * 0.72, row["label"], size=12, fill=TEXT, anchor="end"))
        parts.append(rect(left, y, x_map(row["late_orders"]) - left, bar_h, fill=color))
        parts.append(rect(x_map(row["late_orders"]), y,
                          x_map(row["orders"]) - x_map(row["late_orders"]), bar_h, fill="#cbd5e1"))
        parts.append(text(left + plot_w + 18, y + bar_h * 0.72,
                          f"{int(row['late_orders'])} late / {int(row['orders'])} orders · {row['late_rate']:.1%}",
                          size=12, fill=color, weight="700"))

    parts.extend([
        line(left, top + plot_h, left + plot_w, top + plot_h, stroke=TEXT, width=1.1),
        text(left + plot_w / 2, height - 25, "Distinct orders in each cell", size=12, fill=MUTED, anchor="middle"),
    ])
    return svg_document(
        width,
        height,
        "".join(parts),
        title="High rates and late-order volume by subcategory, ship mode, and region",
        description="Stacked bars show classified-late and other order counts for the nine highest-rate cells and the cell with the most late orders, each with at least 30 distinct orders. Rates are printed beside the bars.",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    output_dir = args.output_dir or args.project_root / "docs" / "assets"
    scenario, lines = read_inputs(args.project_root)
    save(output_dir / "regional-volume-late-rate.svg", regional_volume_chart(scenario))
    save(output_dir / "ship-mode-yearly-trend.svg", ship_mode_trend_chart(scenario))
    save(output_dir / "subcategory-hotspots.svg", hotspot_chart(scenario, lines))
    print(f"Wrote charts to {output_dir}")


if __name__ == "__main__":
    main()

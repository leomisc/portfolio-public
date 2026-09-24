# Superstore Fulfillment SLA Analysis

This repository is the working home for a portfolio project about one practical operations question:

> Where does a shipping promise break, what does it cost operationally, and what should change?

The project uses the public Superstore dataset. The source data contains no promised delivery date or SLA, so the project defines a transparent ship-mode-specific SLA and tests how the conclusions change when that assumption moves by one business day.

## Current status

The source inspection, Python transformation, and live PostgreSQL reproduction are complete for the documented public source. The transformation validates the source, preserves order-line grain, derives a one-row-per-order SLA table, and writes local processed outputs. The findings memo and defense document are the next build phase.

## Repository files

- [Project overview](portfolio-project-overview.md): intended audience, business value, technical direction, and confidentiality framing.
- [Source archive](data/raw/superstore_dataset.zip): public Superstore CSV archive.
- [Inspection notebook](inspection.ipynb): exploratory source inspection and documented assumptions.
- [Transformation module](scripts/transform_superstore.py): repeatable validation, SLA facts, and star-schema generation.
- [Practice notebook](inspection - practice.ipynb): pandas refresher exercises.

## Local setup

The archive contains `Sample - Superstore.csv`. Extract it to `data/raw/` when you begin the build. The extracted CSV is intentionally ignored by Git; the portable source archive remains tracked.

The source is Windows-1252 encoded. Load it with `encoding="cp1252"` and preserve `Postal Code` as a string. The fact table remains at order-line grain and uses `Row ID` as its unique line key.

Run the automated checks and transformation from the repository root with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.transform_superstore
```

The generated files under `data/processed/` are local ignored outputs. They include:

- `fact_order_lines.csv`: validated source-shaped line fact used by the current SLA analysis;
- `fact_orders.csv`: one-row-per-order SLA fact;
- `fact_order_lines_star.csv`: direct-key reporting fact at order-line grain; and
- `dim_date.csv`, `dim_customer.csv`, `dim_location.csv`, `dim_product.csv`, and `dim_ship_mode.csv`.

See [Data Model Notes](data-model-notes.md) for the grain, key choices, and
the source Product ID quality limitation.

## Work-laptop workflow

Clone only this repository into a dedicated folder outside OneDrive, Dropbox, or a home-directory sync root:

```powershell
git clone https://github.com/leomisc/portfolio-public.git portfolio
cd portfolio
git pull
git push
```

This project uses GitHub as its only cross-device sync channel. It does not configure a broad cloud-sync service. Future phone-accessible file links use the repository URL, for example:

<https://github.com/leomisc/portfolio-public/blob/main/README.md>

## Data and confidentiality

This uses a public dataset. It demonstrates the same analysis pattern built in production—turning operational data into documented rules, validated transformations, and decision-ready analysis—without exposing employer data or confidential figures.

# Brazilian Public Indicators Dashboard

A data engineering and analytics project that integrates Brazilian public data
from multiple APIs into a centralized Power BI dashboard.

> [!WARNING]
> **The GitHub repository does not contain the generated datasets.** Files under
> `data/raw` (`.json`) and `data/processed` (`.csv` and `.parquet`) are excluded
> by `.gitignore`. Cloning or downloading this repository therefore provides
> the ETL code and Power BI files, but not the local data used during development.
>
> The `.pbix` file may open with the last data snapshot embedded when it was
> saved. However, refreshing the model—and any visual that depends on a missing
> local source—can fail until the IBGE and BACEN pipelines are executed and the
> expected files are recreated. Downloading the repository alone does not
> recreate these ignored datasets.

## Data Sources

- **IBGE** — population, GDP, age distribution, and labor market indicators.
- **BACEN** — financial and macroeconomic indicators from the Central Bank of Brazil.
- **Weather services** — weather observations and forecasts.

## Architecture

1. Extract data from public APIs.
2. Preserve API responses in a raw data layer.
3. Transform and standardize the data with Python and PySpark.
4. Publish analytics-ready CSV datasets.
5. Build the semantic model and interactive reports in Power BI.

## Project Structure

- `APIs/IBGE` — integrations and ETL pipelines for IBGE SIDRA data.
- `APIs/BACEN` — integrations with the Central Bank of Brazil.
- `APIs/CLIMA_TEMPO` — integrations with weather data services.
- `power-bi` — Power BI reports and semantic models.
- `documentacao` — architecture notes and data dictionaries.
- `Imagens` — images and visual assets used by the reports.

## Current IBGE Datasets

The IBGE pipeline currently publishes:

- Municipal population estimates.
- Brazilian GDP and national accounts.
- Population by age group, sex, and state.
- Quarterly unemployment and labor underutilization rates.
- Monthly IPCA inflation indicators by surveyed area and consumption group.

## Technology Stack

- Python
- PySpark
- Pandas
- REST APIs
- Power BI
- Git and GitHub

## Running the IBGE Pipeline

Open `APIs/IBGE/src/ETL_IBGE.ipynb` and run the cells in order.

By default, the notebook reuses the latest JSON files available in
`APIs/IBGE/data/raw`. Set `ATUALIZAR_DADOS = True` only when you want to
request fresh data from the IBGE API.

Processed datasets are written to:

```text
APIs/IBGE/data/processed
```

## Running the BACEN Pipeline

On the first run, the pipeline automatically fetches the SGS series because
the raw layer does not exist yet:

```powershell
python APIs/BACEN/src/etl_bacen.py
```

Subsequent runs reuse the latest raw files. Use `--update` to fetch fresh data
and add `--publish-postgres` to upsert the result into
`analytics.bacen_serie_historica`. See `APIs/BACEN/README.MD` for parameters.

## Data Modeling

The processed datasets are designed for a star-schema model in Power BI.
Shared dimensions, such as state and calendar tables, can filter multiple fact
tables without duplicating descriptive attributes.

## Security

API keys, tokens, credentials, and local environment files must not be committed
to the repository. Store local configuration in a `.env` file and use
`.env.example` as the public template.

## Data availability and historical snapshots

The repository intentionally versions source code, documentation, database DDL,
and Power BI artifacts—not continuously generated API responses or processed
datasets. Empty data directories are preserved with `.gitkeep` files.

To refresh the Power BI model after cloning the project:

1. Install the dependencies listed in each API directory.
2. Run the IBGE pipeline in `APIs/IBGE/src/ETL_IBGE.ipynb`.
3. Run the BACEN pipeline in `APIs/BACEN/src/ETL_BACEN.ipynb`.
4. Confirm that the expected CSV files exist under each `data/processed` folder.
5. Update the Power BI source paths if the project was cloned to another folder.

If a one-time historical dataset needs to be distributed, publish it as a
versioned GitHub Release asset (for example, a ZIP containing the processed
CSVs) and link it from this README. This keeps generated files out of normal Git
history while giving Power BI users a reproducible snapshot to download.

# Brazilian Public Indicators Dashboard

A data engineering and analytics project that integrates Brazilian public data
from multiple APIs into a centralized Power BI dashboard.

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

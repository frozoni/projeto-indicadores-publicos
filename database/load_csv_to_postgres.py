import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text


PROJECT_DIR = Path(__file__).resolve().parents[1]
DDL_PATH = PROJECT_DIR / "database" / "01_create_analytics_tables.sql"

load_dotenv(PROJECT_DIR / ".env")

required_settings = [
    "POSTGRES_HOST",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
]
missing_settings = [
    setting
    for setting in required_settings
    if not os.getenv(setting)
]
if missing_settings:
    raise RuntimeError(
        "Missing PostgreSQL settings in .env: "
        + ", ".join(missing_settings)
    )

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host=os.environ["POSTGRES_HOST"],
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    database=os.environ["POSTGRES_DB"],
)

engine = create_engine(database_url, pool_pre_ping=True)

tables = [
    {
        "name": "dim_uf",
        "source": "IBGE",
        "file": "dim_uf.csv",
        "date_columns": [],
    },
    {
        "name": "populacao_municipio",
        "source": "IBGE",
        "file": "populacao_municipio.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "pib_pessoas",
        "source": "IBGE",
        "file": "PIB_pessoas.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "pib_financeiro",
        "source": "IBGE",
        "file": "PIB_financeiro.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "pib_percentual",
        "source": "IBGE",
        "file": "PIB_percentual.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "faixa_etaria_uf",
        "source": "IBGE",
        "file": "faixa_etaria_uf.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "desemprego_uf_trimestre",
        "source": "IBGE",
        "file": "desemprego_uf_trimestre.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "ipca_area_mes",
        "source": "IBGE",
        "file": "ipca_area_mes.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "bacen_serie_historica",
        "source": "BACEN",
        "file": "bacen_serie_historica.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "bacen_selic_meta",
        "source": "BACEN",
        "file": "selic_meta.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "bacen_selic_efetiva",
        "source": "BACEN",
        "file": "selic_efetiva.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "bacen_cdi",
        "source": "BACEN",
        "file": "cdi.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "bacen_dolar_venda",
        "source": "BACEN",
        "file": "dolar_venda.csv",
        "date_columns": ["data_referencia"],
    },
]


def execute_ddl(connection):
    ddl = DDL_PATH.read_text(encoding="utf-8")
    statements = [
        statement.strip()
        for statement in ddl.split(";")
        if statement.strip()
    ]
    for statement in statements:
        connection.exec_driver_sql(statement)


def read_csv(config):
    path = (
        PROJECT_DIR / "APIs" / config["source"]
        / "data" / "processed" / config["file"]
    )
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(
        path,
        encoding="utf-8-sig",
        parse_dates=config["date_columns"],
    )


def load_tables(selected_tables):
    # Lê todos os arquivos antes do TRUNCATE. Se algum CSV estiver ausente ou
    # inválido, nenhuma tabela existente será afetada.
    dataframes = {
        config["name"]: read_csv(config)
        for config in selected_tables
    }

    with engine.begin() as connection:
        execute_ddl(connection)
        table_names = ", ".join(
            f"analytics.{config['name']}"
            for config in reversed(selected_tables)
        )
        connection.execute(text(f"TRUNCATE TABLE {table_names}"))

        for config in selected_tables:
            dataframe = dataframes[config["name"]]
            dataframe.to_sql(
                name=config["name"],
                con=connection,
                schema="analytics",
                if_exists="append",
                index=False,
                chunksize=5000,
                method="multi",
            )
            print(
                f"{config['name']}: "
                f"{len(dataframe):,} rows loaded"
            )

    with engine.connect() as connection:
        print("\nPostgreSQL validation:")
        for config in selected_tables:
            count = connection.execute(
                text(
                    f"SELECT COUNT(*) "
                    f"FROM analytics.{config['name']}"
                )
            ).scalar_one()
            print(f"{config['name']}: {count:,} rows")


def main():
    parser = argparse.ArgumentParser(
        description="Load processed CSV datasets into PostgreSQL."
    )
    parser.add_argument(
        "--source",
        choices=["ALL", "IBGE", "BACEN"],
        default="ALL",
        help="Data source to load (default: ALL).",
    )
    args = parser.parse_args()
    selected_tables = [
        config for config in tables
        if args.source == "ALL" or config["source"] == args.source
    ]
    load_tables(selected_tables)


if __name__ == "__main__":
    main()

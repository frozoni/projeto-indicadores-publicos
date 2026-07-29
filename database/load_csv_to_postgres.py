import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text


PROJECT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_DIR / "APIs" / "IBGE" / "data" / "processed"
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
        "file": "dim_uf.csv",
        "date_columns": [],
    },
    {
        "name": "populacao_municipio",
        "file": "populacao_municipio.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "pib_pessoas",
        "file": "PIB_pessoas.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "pib_financeiro",
        "file": "PIB_financeiro.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "pib_percentual",
        "file": "PIB_percentual.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "faixa_etaria_uf",
        "file": "faixa_etaria_uf.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "desemprego_uf_trimestre",
        "file": "desemprego_uf_trimestre.csv",
        "date_columns": ["data_referencia"],
    },
    {
        "name": "ipca_area_mes",
        "file": "ipca_area_mes.csv",
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
    path = PROCESSED_DIR / config["file"]
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(
        path,
        encoding="utf-8-sig",
        parse_dates=config["date_columns"],
    )


with engine.begin() as connection:
    execute_ddl(connection)

    table_names = ", ".join(
        f"analytics.{config['name']}"
        for config in reversed(tables)
    )
    connection.execute(
        text(f"TRUNCATE TABLE {table_names}")
    )

    for config in tables:
        dataframe = read_csv(config)
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
    for config in tables:
        count = connection.execute(
            text(
                f"SELECT COUNT(*) "
                f"FROM analytics.{config['name']}"
            )
        ).scalar_one()
        print(f"{config['name']}: {count:,} rows")


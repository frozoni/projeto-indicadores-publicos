import json
from pathlib import Path


notebook_path = Path("APIs/IBGE/src/ETL_IBGE.ipynb")
notebook = json.loads(notebook_path.read_text(encoding="utf-8"))


def get_source(index):
    return "".join(notebook["cells"][index]["source"])


def set_source(index, text):
    notebook["cells"][index]["source"] = text.splitlines(keepends=True)


imports = get_source(2)
imports = imports.replace(
    "import json\n",
    "import json\nimport os\n",
)
imports = imports.replace(
    "import requests\nfrom pyspark.sql",
    """import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, URL, create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from pyspark.sql""",
)
imports = imports.replace(
    "ATUALIZAR_DADOS = False\n",
    """ATUALIZAR_DADOS = False

# True publishes each final dataset to PostgreSQL using an UPSERT.
PUBLICAR_POSTGRES = False
POSTGRES_SCHEMA = "analytics"
""",
)
set_source(2, imports)

functions = get_source(8)
start = functions.index("def salvar_csv")
functions = functions[:start] + '''_postgres_engine = None
_postgres_preparado = False


def obter_engine_postgres():
    global _postgres_engine

    if _postgres_engine is not None:
        return _postgres_engine

    project_dir = IBGE_DIR.parents[1]
    load_dotenv(project_dir / ".env")

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
    _postgres_engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )
    return _postgres_engine


def preparar_postgres():
    global _postgres_preparado

    if _postgres_preparado:
        return

    project_dir = IBGE_DIR.parents[1]
    ddl_path = (
        project_dir
        / "database"
        / "01_create_analytics_tables.sql"
    )
    ddl = ddl_path.read_text(encoding="utf-8")
    statements = [
        statement.strip()
        for statement in ddl.split(";")
        if statement.strip()
    ]

    engine = obter_engine_postgres()
    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)

    _postgres_preparado = True


def publicar_postgres(pandas_df, tabela, chave, chunk_size=1000):
    if not chave:
        raise ValueError(
            f"{tabela}: an UPSERT requires a primary key"
        )

    preparar_postgres()
    engine = obter_engine_postgres()

    dataframe = (
        pandas_df
        .astype(object)
        .where(pd.notna(pandas_df), None)
    )
    records = dataframe.to_dict(orient="records")

    with engine.begin() as connection:
        metadata = MetaData()
        target = Table(
            tabela,
            metadata,
            schema=POSTGRES_SCHEMA,
            autoload_with=connection,
        )

        table_columns = {column.name for column in target.columns}
        csv_columns = set(dataframe.columns)
        if csv_columns != table_columns:
            raise ValueError(
                f"{tabela}: CSV columns do not match PostgreSQL. "
                f"Missing: {sorted(table_columns - csv_columns)}; "
                f"unexpected: {sorted(csv_columns - table_columns)}"
            )

        for offset in range(0, len(records), chunk_size):
            chunk = records[offset:offset + chunk_size]
            statement = pg_insert(target).values(chunk)
            update_values = {
                column.name: statement.excluded[column.name]
                for column in target.columns
                if column.name not in chave
            }
            statement = statement.on_conflict_do_update(
                index_elements=chave,
                set_=update_values,
            )
            connection.execute(statement)

    print(
        f"{POSTGRES_SCHEMA}.{tabela}: "
        f"{len(dataframe):,} rows inserted or updated"
    )


def publicar_dados(df, nome, chave):
    destino = PROCESSED_DIR / f"{nome}.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)

    pandas_df = df.toPandas()
    duplicadas = int(
        pandas_df.duplicated(subset=chave).sum()
    )
    if duplicadas:
        raise ValueError(
            f"{nome}: {duplicadas} duplicate keys in {chave}"
        )

    pandas_df.to_csv(
        destino,
        index=False,
        encoding="utf-8-sig",
    )
    print(f"{nome}: {len(pandas_df):,} rows -> {destino}")

    if PUBLICAR_POSTGRES:
        publicar_postgres(
            pandas_df=pandas_df,
            tabela=nome,
            chave=chave,
        )

    return destino
'''
set_source(8, functions)

for index in [10, 12, 14, 16, 18, 20]:
    source = get_source(index).replace("salvar_csv(", "publicar_dados(")
    set_source(index, source)

notebook_path.write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8",
)

print("PostgreSQL UPSERT publishing added to the notebook.")

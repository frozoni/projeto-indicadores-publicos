"""ETL de séries temporais do Banco Central (SGS)."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests
from dotenv import load_dotenv
from pyspark.sql import DataFrame, SparkSession, functions as F, types as T
from sqlalchemy import MetaData, Table, URL, create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert


BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
POSTGRES_SCHEMA = "analytics"

# O catálogo é deliberadamente declarativo: novas séries não exigem novas
# funções de extração ou transformação.
SERIES: dict[str, dict[str, Any]] = {
    "selic_meta": {
        "codigo": 432,
        "nome": "Meta Selic",
        "unidade": "% a.a.",
        "periodicidade": "diaria",
    },
    "selic_efetiva": {
        "codigo": 1178,
        "nome": "Taxa Selic efetiva anualizada",
        "unidade": "% a.a.",
        "periodicidade": "diaria",
    },
    "cdi": {
        "codigo": 12,
        "nome": "Taxa de juros CDI",
        "unidade": "% a.d.",
        "periodicidade": "diaria",
    },
    "dolar_venda": {
        "codigo": 1,
        "nome": "Taxa de câmbio - dólar americano (venda)",
        "unidade": "R$/US$",
        "periodicidade": "diaria",
    },
}


def localizar_diretorio_bacen():
    cwd = Path.cwd().resolve()
    candidatos = [cwd, cwd.parent, cwd / "APIs" / "BACEN", cwd.parent / "APIs" / "BACEN"]
    for candidato in candidatos:
        if (candidato / "src").is_dir() and candidato.name.upper() == "BACEN":
            return candidato
    raise FileNotFoundError("Não foi possível localizar APIs/BACEN.")


def janelas_de_datas(inicio: date, fim: date, anos: int = 3) -> Iterable[tuple[date, date]]:
    """Divide consultas para respeitar o limite do SGS para séries diárias."""
    atual = inicio
    while atual <= fim:
        try:
            limite = atual.replace(year=atual.year + anos) - timedelta(days=1)
        except ValueError:  # 29 de fevereiro
            limite = atual.replace(year=atual.year + anos, day=28) - timedelta(days=1)
        termino = min(limite, fim)
        yield atual, termino
        atual = termino + timedelta(days=1)


def consultar_api(
    codigo: int,
    inicio: date,
    fim: date,
    tentativas: int = 4,
    timeout: int = 60,
) -> list[dict[str, str]]:
    url = f"{BASE_URL}.{codigo}/dados"
    params = {
        "formato": "json",
        "dataInicial": inicio.strftime("%d/%m/%Y"),
        "dataFinal": fim.strftime("%d/%m/%Y"),
    }
    headers = {
        "Accept": "application/json",
        "User-Agent": "projeto-indicadores-publicos/1.0",
    }
    ultimo_erro: Exception | None = None
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            resposta.raise_for_status()
            if not resposta.content or not resposta.text.strip():
                raise ValueError("o BACEN retornou uma resposta vazia")
            try:
                dados = resposta.json()
            except requests.exceptions.JSONDecodeError as erro_json:
                tipo = resposta.headers.get("Content-Type", "não informado")
                trecho = resposta.text[:200].replace("\n", " ").strip()
                raise ValueError(
                    "o BACEN não retornou JSON válido "
                    f"(Content-Type: {tipo}; início: {trecho!r})"
                ) from erro_json
            if not isinstance(dados, list):
                raise ValueError(f"Resposta inesperada para a série {codigo}")
            return dados
        except (requests.RequestException, ValueError) as erro:
            ultimo_erro = erro
            if tentativa == tentativas:
                break
            espera = 2 ** (tentativa - 1)
            print(
                f"Série {codigo}, {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}: "
                f"tentativa {tentativa}/{tentativas} falhou ({erro}). "
                f"Nova tentativa em {espera}s."
            )
            time.sleep(espera)
    raise RuntimeError(
        f"Não foi possível consultar a série {codigo} entre "
        f"{inicio:%d/%m/%Y} e {fim:%d/%m/%Y} após {tentativas} tentativas: "
        f"{ultimo_erro}"
    ) from ultimo_erro


def extrair_serie(nome: str, config: dict[str, Any], inicio: date, fim: date, raw_dir: Path,):
    registros: list[dict[str, Any]] = []
    for janela_inicio, janela_fim in janelas_de_datas(inicio, fim):
        dados = consultar_api(config["codigo"], janela_inicio, janela_fim)
        registros.extend(
            {"serie": nome, "codigo": config["codigo"], **item}
            for item in dados
        )
        time.sleep(0.2)

    # Janelas contíguas não deveriam duplicar datas, mas a deduplicação torna a
    # camada raw determinística mesmo se o provedor repetir a borda da janela.
    unicos = {(item["codigo"], item["data"]): item for item in registros}
    ordenados = sorted(unicos.values(), key=lambda item: datetime.strptime(item["data"], "%d/%m/%Y"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = raw_dir / f"bacen_{nome}_{config['codigo']}_{timestamp}.json"
    destino.write_text(json.dumps(ordenados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{nome}: {len(ordenados):,} registros -> {destino}")
    return destino


def json_mais_recente(nome: str, codigo: int, raw_dir: Path):
    arquivos = list(raw_dir.glob(f"bacen_{nome}_{codigo}_*.json"))
    if not arquivos:
        raise FileNotFoundError(
            f"Não existe JSON bruto para {nome}. Execute com atualizar_dados=True."
        )
    return max(arquivos, key=lambda caminho: caminho.stat().st_mtime)


def transformar_series(
    spark: SparkSession,
    arquivos: dict[str, Path],
    series: dict[str, dict[str, Any]],
) -> DataFrame:
    schema = T.ArrayType(T.StructType([
        T.StructField("serie", T.StringType()),
        T.StructField("codigo", T.IntegerType()),
        T.StructField("data", T.StringType()),
        T.StructField("valor", T.StringType()),
    ]))
    frames = []
    for nome, caminho in arquivos.items():
        config = series[nome]
        frame = (
            spark.read.text(str(caminho), wholetext=True)
            .select(F.explode(F.from_json("value", schema)).alias("item"))
            .select("item.*")
            .withColumn("indicador", F.lit(config["nome"]))
            .withColumn("unidade", F.lit(config["unidade"]))
            .withColumn("periodicidade", F.lit(config["periodicidade"]))
        )
        frames.append(frame)

    if not frames:
        raise ValueError("Nenhuma série ativa para transformar.")
    resultado = frames[0]
    for frame in frames[1:]:
        resultado = resultado.unionByName(frame)

    return (
        resultado
        .withColumn("data_referencia", F.to_date("data", "dd/MM/yyyy"))
        .withColumn("ano", F.year("data_referencia").cast("smallint"))
        .withColumn("mes", F.month("data_referencia").cast("smallint"))
        .withColumn("valor", F.regexp_replace("valor", ",", ".").cast(T.DecimalType(20, 8)))
        .select(
            F.col("codigo").alias("serie_id"), "serie", "indicador", "unidade",
            "periodicidade", "data_referencia", "ano", "mes", "valor",
        )
        .filter(F.col("data_referencia").isNotNull() & F.col("valor").isNotNull())
        .dropDuplicates(["serie_id", "data_referencia"])
        .orderBy("serie_id", "data_referencia")
    )


def obter_engine_postgres(project_dir: Path):
    load_dotenv(project_dir / ".env")
    obrigatorias = ["POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    ausentes = [chave for chave in obrigatorias if not os.getenv(chave)]
    if ausentes:
        raise RuntimeError("Configurações PostgreSQL ausentes: " + ", ".join(ausentes))
    url = URL.create(
        "postgresql+psycopg", username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"], host=os.environ["POSTGRES_HOST"],
        port=int(os.getenv("POSTGRES_PORT", "5432")), database=os.environ["POSTGRES_DB"],
    )
    return create_engine(url, pool_pre_ping=True)


def publicar_postgres(pandas_df: pd.DataFrame, project_dir: Path, chunk_size: int = 1000) -> None:
    engine = obter_engine_postgres(project_dir)
    ddl = (project_dir / "database" / "01_create_analytics_tables.sql").read_text(encoding="utf-8")
    dataframe = pandas_df.astype(object).where(pd.notna(pandas_df), None)
    with engine.begin() as connection:
        for statement in (parte.strip() for parte in ddl.split(";") if parte.strip()):
            connection.exec_driver_sql(statement)
        metadata = MetaData()
        target = Table("bacen_serie_historica", metadata, schema=POSTGRES_SCHEMA, autoload_with=connection)
        registros = dataframe.to_dict(orient="records")
        for offset in range(0, len(registros), chunk_size):
            comando = pg_insert(target).values(registros[offset:offset + chunk_size])
            comando = comando.on_conflict_do_update(
                index_elements=["serie_id", "data_referencia"],
                set_={col.name: comando.excluded[col.name] for col in target.columns if col.name not in {"serie_id", "data_referencia"}},
            )
            connection.execute(comando)
    print(f"{POSTGRES_SCHEMA}.bacen_serie_historica: {len(dataframe):,} linhas inseridas ou atualizadas")


def executar_pipeline(
    atualizar_dados: bool = False,
    publicar_no_postgres: bool = False,
    data_inicial: date = date(2016, 1, 1),
    data_final: date | None = None,
    series_ativas: Iterable[str] | None = None,
):
    bacen_dir = localizar_diretorio_bacen()
    project_dir = bacen_dir.parents[1]
    raw_dir = bacen_dir / "data" / "raw"
    processed_dir = project_dir / "dados" / "BACEN"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    selecionadas = list(series_ativas or SERIES)
    desconhecidas = set(selecionadas) - set(SERIES)
    if desconhecidas:
        raise ValueError(f"Séries desconhecidas: {sorted(desconhecidas)}")
    fim = data_final or date.today()
    if data_inicial > fim:
        raise ValueError("data_inicial deve ser anterior ou igual a data_final")

    arquivos: dict[str, Path] = {}
    for nome in selecionadas:
        config = SERIES[nome]
        if atualizar_dados:
            arquivos[nome] = extrair_serie(
                nome, config, data_inicial, fim, raw_dir
            )
            continue

        try:
            arquivos[nome] = json_mais_recente(
                nome, config["codigo"], raw_dir
            )
            print(f"{nome}: reutilizando {arquivos[nome]}")
        except FileNotFoundError:
            print(
                f"{nome}: camada raw ainda não existe; "
                "fazendo a primeira extração automaticamente."
            )
            arquivos[nome] = extrair_serie(
                nome, config, data_inicial, fim, raw_dir
            )
    spark = SparkSession.builder.appName("ETL-BACEN-SGS").master("local[*]").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    try:
        fato = transformar_series(spark, arquivos, SERIES)
        pandas_df = fato.toPandas()
    finally:
        spark.stop()
    if pandas_df.duplicated(["serie_id", "data_referencia"]).any():
        raise ValueError("Foram encontradas chaves duplicadas no resultado.")
    destino = processed_dir / "bacen_serie_historica.csv"
    pandas_df.to_csv(destino, index=False, encoding="utf-8-sig")
    print(f"bacen_serie_historica: {len(pandas_df):,} linhas -> {destino}")
    if publicar_no_postgres:
        publicar_postgres(pandas_df, project_dir)
    return destino


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true", help="Consulta dados novos no SGS")
    parser.add_argument("--publish-postgres", action="store_true", help="Publica por UPSERT")
    parser.add_argument("--start", default="2016-01-01", help="Data inicial (AAAA-MM-DD)")
    parser.add_argument("--end", help="Data final (AAAA-MM-DD); padrão: hoje")
    args = parser.parse_args()
    executar_pipeline(
        atualizar_dados=args.update,
        publicar_no_postgres=args.publish_postgres,
        data_inicial=date.fromisoformat(args.start),
        data_final=date.fromisoformat(args.end) if args.end else None,
    )

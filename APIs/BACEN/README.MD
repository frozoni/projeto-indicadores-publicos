# ETL BACEN — API SGS, PySpark e PostgreSQL

O pipeline segue o mesmo desenho do IBGE:

```text
API SGS → JSON em data/raw → PySpark → CSV em data/processed → PostgreSQL/Power BI
```

As séries iniciais são Meta Selic (432), Selic efetiva (1178), CDI (12) e
dólar de venda (1). O catálogo `SERIES`, em `src/etl_bacen.py`, centraliza código,
nome, unidade e periodicidade, tornando simples adicionar outros indicadores.

## Execução

Na primeira execução, basta iniciar o pipeline. Como a camada raw ainda não
existe, os dados serão consultados automaticamente:

```powershell
python APIs/BACEN/src/etl_bacen.py
```

Nas execuções locais seguintes, o comando reutiliza o JSON mais recente. Use
`--update` quando quiser buscar dados novos. Para atualizar e também fazer
UPSERT no PostgreSQL:

```powershell
python APIs/BACEN/src/etl_bacen.py --update --publish-postgres
```

O período padrão começa em 2016 e termina no dia atual. Ele pode ser alterado:

```powershell
python APIs/BACEN/src/etl_bacen.py --update --start 2020-01-01 --end 2025-12-31
```

Também é possível abrir `src/ETL_BACEN.ipynb`, ajustar os parâmetros e executar
as células. Séries diárias são automaticamente divididas em janelas de três
anos, com retentativas para respostas temporariamente vazias ou inválidas.

## Saída

`data/processed/bacen_serie_historica.csv` possui uma linha por série e data,
com chave `(serie_id, data_referencia)`. A tabela equivalente no banco é
`analytics.bacen_serie_historica`.

O notebook também gera `selic_meta.csv`, `selic_efetiva.csv`, `cdi.csv` e
`dolar_venda.csv`. Para criar e carregar as tabelas consolidada e individuais
no PostgreSQL, execute a partir da raiz do projeto:

```powershell
python database/load_csv_to_postgres.py --source BACEN
```

Fonte oficial: [Portal de Dados Abertos do Banco Central](https://dadosabertos.bcb.gov.br/).

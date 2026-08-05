# PostgreSQL — indicadores públicos

O diretório contém o DDL do schema `analytics` e o carregador dos CSVs
processados pelo IBGE e pelo BACEN.

## Pré-requisitos

Configure no `.env` da raiz:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=db-indicadores
POSTGRES_USER=etl_writer
POSTGRES_PASSWORD=sua_senha
```

Antes da carga do BACEN, execute todas as células do notebook
`APIs/BACEN/src/ETL_BACEN.ipynb`. A pasta `data/processed` deve conter:

- `bacen_serie_historica.csv`
- `selic_meta.csv`
- `selic_efetiva.csv`
- `cdi.csv`
- `dolar_venda.csv`

## Carga somente do BACEN

```powershell
python database/load_csv_to_postgres.py --source BACEN
```

O comando cria as tabelas quando necessário, valida a presença dos CSVs antes
de modificar o banco, trunca somente as tabelas BACEN, carrega os dados em uma
transação e apresenta a contagem final de cada tabela.

## Outras opções

```powershell
python database/load_csv_to_postgres.py --source IBGE
python database/load_csv_to_postgres.py --source ALL
```

Tabelas BACEN criadas no schema `analytics`:

- `bacen_serie_historica` — todas as séries em uma única tabela;
- `bacen_selic_meta`;
- `bacen_selic_efetiva`;
- `bacen_cdi`;
- `bacen_dolar_venda`.

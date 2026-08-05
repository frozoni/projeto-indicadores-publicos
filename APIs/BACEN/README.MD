# ETL BACEN — API SGS, PySpark e PostgreSQL

> [!WARNING]
> **Os dados do BACEN não são enviados normalmente ao GitHub.** Os JSONs de
> `data/raw` e os CSVs/Parquet de `data/processed` são ignorados pelo Git. Ao
> clonar ou baixar o repositório, essas pastas conterão apenas os arquivos
> `.gitkeep`. Execute este ETL antes de atualizar o Power BI ou carregar o
> PostgreSQL.
>
> O PBIX pode abrir exibindo o último snapshot incorporado, mas a atualização do
> modelo ou visuais dependentes dos arquivos locais pode falhar até que os CSVs
> sejam recriados. Se o projeto estiver em outro diretório, revise também os
> caminhos das fontes no Power BI.

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

## Snapshot histórico para distribuição

Para disponibilizar uma base histórica única aos usuários do painel, publique
um ZIP contendo os CSVs processados como arquivo de uma GitHub Release. Informe
no nome ou na descrição a data de extração. O snapshot permanece separado do
histórico normal do Git e deve ser baixado e extraído em `data/processed` antes
de atualizar o Power BI.

# ETL IBGE — API SIDRA, PySpark e Power BI

> [!WARNING]
> **Os dados do IBGE não são enviados normalmente ao GitHub.** Os JSONs de
> `data/raw` e os CSVs/Parquet de `data/processed` são ignorados pelo Git. Ao
> clonar ou baixar o repositório, essas pastas conterão apenas os arquivos
> `.gitkeep`. Execute este ETL antes de atualizar o Power BI.
>
> O PBIX pode abrir exibindo o último snapshot que estava incorporado quando foi
> salvo, mas a atualização do modelo ou visuais dependentes dos arquivos locais
> pode falhar enquanto os datasets não forem recriados. Também pode ser
> necessário ajustar os caminhos das fontes no Power BI para o diretório local.

O projeto possui um único ponto de entrada:

```text
ETL_IBGE.ipynb
```

O notebook controla o pipeline completo:

```text
Descoberta da API
        ↓
Escolha de tabelas, variáveis e classificações
        ↓
Extração com requests
        ↓
JSON bruto em data/raw
        ↓
Tratamento com PySpark
        ↓
CSV tratado em data/processed
        ↓
Power BI
```

## Divisão de responsabilidades

Python é utilizado somente para:

- fazer requisições HTTP;
- aplicar retentativas;
- salvar o retorno original em JSON;
- selecionar o arquivo bruto mais recente;
- entregar o resultado final do Spark em um único CSV.

PySpark é utilizado para:

- interpretar o esquema aninhado do SIDRA;
- explodir variáveis, resultados, séries e períodos;
- interpretar classificações;
- converter tipos;
- tratar símbolos especiais e valores nulos;
- criar dimensões e datas;
- calcular variações e participações;
- pivotar indicadores;
- preparar as tabelas finais do BI.

## Como executar

1. Ative o ambiente virtual.
2. Abra `ETL_IBGE.ipynb`.
3. Revise a célula **Parâmetros do pipeline**.
4. Defina `ATUALIZAR_DADOS = True` quando quiser consultar a API.
5. Execute todas as células.
6. Volte para `ATUALIZAR_DADOS = False` para desenvolver usando os JSONs locais.

Com `ATUALIZAR_DADOS = False`, o notebook reutiliza o JSON mais recente de
cada indicador e não faz novas chamadas à API.

## Escolha dos indicadores

Os indicadores são controlados por:

```python
INDICADORES_ATIVOS = [
    "populacao",
    "pib",
    "faixa_etaria",
    "desemprego",
    "ipca",
]
```

Remova um nome para pular seu processamento. Para adicionar outro indicador,
inclua sua configuração no dicionário `INDICADORES`.

Cada configuração informa:

- código do agregado/tabela;
- períodos;
- variáveis;
- nível territorial;
- classificações e categorias opcionais.

## Descoberta de códigos

Antes de configurar uma tabela desconhecida, use:

```python
metadados = descobrir_agregado("9514")
```

A função apresenta:

- nome da tabela;
- níveis territoriais disponíveis;
- códigos e nomes das variáveis;
- códigos das classificações;
- categorias e respectivos níveis.

Isso permite montar a consulta sem depender de códigos “mágicos” espalhados
pelo tratamento.

## Indicadores atuais

| Indicador | Tabela | Granularidade | Saída |
|---|---:|---|---|
| População estimada | 6579 | Município/ano | `populacao_municipio.csv` |
| PIB e contas nacionais | 6784 | Brasil/ano/variável | `pib_brasil_ano.csv` |
| Faixa etária e sexo | 9514 | UF/Censo 2022 | `faixa_etaria_uf.csv` |
| Desemprego e subutilização | 4099 | UF/trimestre | `desemprego_uf_trimestre.csv` |
| IPCA geral e grupos | 7060 | Área pesquisada/mês | `ipca_area_mes.csv` |
| Unidades da Federação | — | UF | `dim_uf.csv` |

## Observação sobre o IPCA

As áreas pesquisadas pelo IPCA não representam necessariamente todo o estado.
No Power BI, `area_ipca` deve ser uma dimensão territorial própria. Não relacione
automaticamente uma região metropolitana à `DimUF` como se ela representasse a
totalidade da Unidade da Federação.

## Fontes oficiais

- API de Agregados: <https://servicodados.ibge.gov.br/api/docs/agregados>
- SIDRA: <https://sidra.ibge.gov.br/>

## Snapshot histórico para distribuição

Caso seja necessário disponibilizar uma base histórica única junto com o
painel, publique um ZIP dos CSVs processados como arquivo de uma GitHub Release.
O snapshot deve informar a data de extração e não substitui a execução do ETL
para obter dados atualizados.

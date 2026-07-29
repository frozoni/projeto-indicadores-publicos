# Painel de Indicadores Públicos do Brasil

Projeto de engenharia e análise de dados que integra informações públicas
de diferentes APIs em um painel central desenvolvido no Power BI.

## Fontes de dados

- IBGE: indicadores populacionais, econômicos e de emprego.
- BACEN: indicadores financeiros e econômicos.
- Clima: informações meteorológicas e previsões do tempo.

## Arquitetura

1. Extração dos dados por meio das APIs.
2. Tratamento e padronização utilizando Python.
3. Armazenamento dos dados tratados.
4. Consumo dos dados pelo Power BI.
5. Navegação por um menu principal entre as áreas de análise.

## Estrutura

- `APIs/ibge`: integração com os serviços do IBGE.
- `APIs/bacen`: integração com os serviços do Banco Central.
- `APIs/clima-tempo`: integração com os serviços meteorológicos.
- `power-bi`: relatório e modelo semântico do Power BI.
- `documentacao`: arquitetura e dicionário de dados.
- `imagens`: imagens utilizadas no relatório.

## Tecnologias

- Python
- Pandas
- APIs REST
- Power BI
- Git
- GitHub

## Segurança

Chaves, tokens e credenciais não são armazenados no repositório.
As configurações locais devem ser mantidas em um arquivo `.env`.
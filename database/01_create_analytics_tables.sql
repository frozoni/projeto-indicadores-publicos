-- Active: 1785348800873@@127.0.0.1@5432@db-indicadores
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.dim_uf (
    uf_id SMALLINT PRIMARY KEY,
    uf_sigla CHAR(2) NOT NULL UNIQUE,
    uf_nome VARCHAR(30) NOT NULL UNIQUE,
    regiao VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.populacao_municipio (
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    municipio_id INTEGER NOT NULL,
    municipio_nome VARCHAR(150) NOT NULL,
    uf_id SMALLINT NOT NULL,
    populacao BIGINT,
    CONSTRAINT pk_populacao_municipio
        PRIMARY KEY (data_referencia, municipio_id),
    CONSTRAINT fk_populacao_municipio_uf
        FOREIGN KEY (uf_id)
        REFERENCES analytics.dim_uf (uf_id),
    CONSTRAINT ck_populacao_municipio_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia))
);

CREATE TABLE IF NOT EXISTS analytics.pib_pessoas (
    variavel_id INTEGER NOT NULL,
    variavel_nome TEXT NOT NULL,
    unidade VARCHAR(50) NOT NULL,
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    populacao_mil_pessoas BIGINT NOT NULL,
    CONSTRAINT pk_pib_pessoas
        PRIMARY KEY (data_referencia, variavel_id),
    CONSTRAINT ck_pib_pessoas_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia))
);

CREATE TABLE IF NOT EXISTS analytics.pib_financeiro (
    variavel_id INTEGER NOT NULL,
    variavel_nome TEXT NOT NULL,
    unidade VARCHAR(50) NOT NULL,
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    valor_financeiro NUMERIC(20, 2) NOT NULL,
    CONSTRAINT pk_pib_financeiro
        PRIMARY KEY (data_referencia, variavel_id),
    CONSTRAINT ck_pib_financeiro_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia))
);

CREATE TABLE IF NOT EXISTS analytics.pib_percentual (
    variavel_id INTEGER NOT NULL,
    variavel_nome TEXT NOT NULL,
    unidade VARCHAR(50) NOT NULL,
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    valor_percentual NUMERIC(10, 2) NOT NULL,
    CONSTRAINT pk_pib_percentual
        PRIMARY KEY (data_referencia, variavel_id),
    CONSTRAINT ck_pib_percentual_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia))
);

CREATE TABLE IF NOT EXISTS analytics.faixa_etaria_uf (
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    uf_id SMALLINT NOT NULL,
    sexo_id INTEGER NOT NULL,
    sexo VARCHAR(20) NOT NULL,
    faixa_etaria_id INTEGER NOT NULL,
    faixa_etaria VARCHAR(40) NOT NULL,
    faixa_etaria_ordem SMALLINT NOT NULL,
    faixa_macro VARCHAR(30) NOT NULL,
    populacao BIGINT NOT NULL,
    CONSTRAINT pk_faixa_etaria_uf
        PRIMARY KEY (
            data_referencia,
            uf_id,
            sexo_id,
            faixa_etaria_id
        ),
    CONSTRAINT fk_faixa_etaria_uf
        FOREIGN KEY (uf_id)
        REFERENCES analytics.dim_uf (uf_id),
    CONSTRAINT ck_faixa_etaria_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia))
);

CREATE TABLE IF NOT EXISTS analytics.desemprego_uf_trimestre (
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    trimestre_num SMALLINT NOT NULL,
    trimestre VARCHAR(20) NOT NULL,
    uf_id SMALLINT NOT NULL,
    taxa_desocupacao_pct NUMERIC(10, 2),
    taxa_subutilizacao_pct NUMERIC(10, 2),
    CONSTRAINT pk_desemprego_uf_trimestre
        PRIMARY KEY (data_referencia, uf_id),
    CONSTRAINT fk_desemprego_uf
        FOREIGN KEY (uf_id)
        REFERENCES analytics.dim_uf (uf_id),
    CONSTRAINT ck_desemprego_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia)),
    CONSTRAINT ck_desemprego_trimestre
        CHECK (trimestre_num BETWEEN 1 AND 4)
);

CREATE TABLE IF NOT EXISTS analytics.ipca_area_mes (
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    mes SMALLINT NOT NULL,
    area_ipca_id INTEGER NOT NULL,
    area_ipca VARCHAR(100) NOT NULL,
    nivel_id VARCHAR(10) NOT NULL,
    grupo_ipca_id INTEGER NOT NULL,
    grupo_ipca VARCHAR(100) NOT NULL,
    grupo_ipca_ordem SMALLINT NOT NULL,
    variacao_mensal_pct NUMERIC(10, 2),
    acumulado_ano_pct NUMERIC(10, 2),
    acumulado_12_meses_pct NUMERIC(10, 2),
    peso_mensal_pct NUMERIC(10, 2),
    CONSTRAINT pk_ipca_area_mes
        PRIMARY KEY (
            data_referencia,
            area_ipca_id,
            grupo_ipca_id
        ),
    CONSTRAINT ck_ipca_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia)),
    CONSTRAINT ck_ipca_mes
        CHECK (mes BETWEEN 1 AND 12)
);

CREATE TABLE IF NOT EXISTS analytics.bacen_serie_historica (
    serie_id INTEGER NOT NULL,
    serie VARCHAR(50) NOT NULL,
    indicador VARCHAR(150) NOT NULL,
    unidade VARCHAR(30) NOT NULL,
    periodicidade VARCHAR(20) NOT NULL,
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    mes SMALLINT NOT NULL,
    valor NUMERIC(20, 8) NOT NULL,
    CONSTRAINT pk_bacen_serie_historica
        PRIMARY KEY (serie_id, data_referencia),
    CONSTRAINT ck_bacen_serie_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia)),
    CONSTRAINT ck_bacen_serie_mes
        CHECK (mes BETWEEN 1 AND 12)
);

CREATE TABLE IF NOT EXISTS analytics.bacen_selic_meta (
    serie_id INTEGER NOT NULL,
    serie VARCHAR(50) NOT NULL,
    indicador VARCHAR(150) NOT NULL,
    unidade VARCHAR(30) NOT NULL,
    periodicidade VARCHAR(20) NOT NULL,
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    mes SMALLINT NOT NULL,
    valor NUMERIC(20, 8) NOT NULL,
    CONSTRAINT pk_bacen_selic_meta
        PRIMARY KEY (serie_id, data_referencia),
    CONSTRAINT ck_bacen_selic_meta_id CHECK (serie_id = 432),
    CONSTRAINT ck_bacen_selic_meta_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia)),
    CONSTRAINT ck_bacen_selic_meta_mes CHECK (mes BETWEEN 1 AND 12)
);

CREATE TABLE IF NOT EXISTS analytics.bacen_selic_efetiva (
    serie_id INTEGER NOT NULL,
    serie VARCHAR(50) NOT NULL,
    indicador VARCHAR(150) NOT NULL,
    unidade VARCHAR(30) NOT NULL,
    periodicidade VARCHAR(20) NOT NULL,
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    mes SMALLINT NOT NULL,
    valor NUMERIC(20, 8) NOT NULL,
    CONSTRAINT pk_bacen_selic_efetiva
        PRIMARY KEY (serie_id, data_referencia),
    CONSTRAINT ck_bacen_selic_efetiva_id CHECK (serie_id = 1178),
    CONSTRAINT ck_bacen_selic_efetiva_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia)),
    CONSTRAINT ck_bacen_selic_efetiva_mes CHECK (mes BETWEEN 1 AND 12)
);

CREATE TABLE IF NOT EXISTS analytics.bacen_cdi (
    serie_id INTEGER NOT NULL,
    serie VARCHAR(50) NOT NULL,
    indicador VARCHAR(150) NOT NULL,
    unidade VARCHAR(30) NOT NULL,
    periodicidade VARCHAR(20) NOT NULL,
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    mes SMALLINT NOT NULL,
    valor NUMERIC(20, 8) NOT NULL,
    CONSTRAINT pk_bacen_cdi
        PRIMARY KEY (serie_id, data_referencia),
    CONSTRAINT ck_bacen_cdi_id CHECK (serie_id = 12),
    CONSTRAINT ck_bacen_cdi_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia)),
    CONSTRAINT ck_bacen_cdi_mes CHECK (mes BETWEEN 1 AND 12)
);

CREATE TABLE IF NOT EXISTS analytics.bacen_dolar_venda (
    serie_id INTEGER NOT NULL,
    serie VARCHAR(50) NOT NULL,
    indicador VARCHAR(150) NOT NULL,
    unidade VARCHAR(30) NOT NULL,
    periodicidade VARCHAR(20) NOT NULL,
    data_referencia DATE NOT NULL,
    ano SMALLINT NOT NULL,
    mes SMALLINT NOT NULL,
    valor NUMERIC(20, 8) NOT NULL,
    CONSTRAINT pk_bacen_dolar_venda
        PRIMARY KEY (serie_id, data_referencia),
    CONSTRAINT ck_bacen_dolar_venda_id CHECK (serie_id = 1),
    CONSTRAINT ck_bacen_dolar_venda_ano
        CHECK (ano = EXTRACT(YEAR FROM data_referencia)),
    CONSTRAINT ck_bacen_dolar_venda_mes CHECK (mes BETWEEN 1 AND 12)
);

CREATE INDEX IF NOT EXISTS idx_populacao_municipio_uf
    ON analytics.populacao_municipio (uf_id);

CREATE INDEX IF NOT EXISTS idx_faixa_etaria_uf_id
    ON analytics.faixa_etaria_uf (uf_id);

CREATE INDEX IF NOT EXISTS idx_desemprego_uf_id
    ON analytics.desemprego_uf_trimestre (uf_id);

CREATE INDEX IF NOT EXISTS idx_ipca_area_id
    ON analytics.ipca_area_mes (area_ipca_id);

CREATE INDEX IF NOT EXISTS idx_ipca_grupo_id
    ON analytics.ipca_area_mes (grupo_ipca_id);

CREATE INDEX IF NOT EXISTS idx_bacen_serie_data
    ON analytics.bacen_serie_historica (data_referencia);

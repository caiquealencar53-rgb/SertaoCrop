-- -*- coding: utf-8 -*-
-- Schema SQLite do SertãoCrop.
-- Aplicado por database.connection.initialize_database().
-- O arquivo .db fica em data_base/dados/; este script é a única fonte da estrutura.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Cadastro agrícola
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agricultores (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL,
    cpf_cnpj      TEXT,
    telefone      TEXT,
    email         TEXT,
    data_cadastro TEXT DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS propriedades (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    agricultor_id  INTEGER,
    nome           TEXT NOT NULL,
    municipio      TEXT,
    uf             TEXT,
    latitude       REAL,
    longitude      REAL,
    area_total_ha  REAL,
    observacoes    TEXT,
    FOREIGN KEY (agricultor_id) REFERENCES agricultores(id)
);

CREATE TABLE IF NOT EXISTS areas_agricolas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    propriedade_id  INTEGER NOT NULL,
    nome            TEXT NOT NULL,
    solo_id         INTEGER,
    latitude        REAL,
    longitude       REAL,
    area_ha         REAL,
    observacoes     TEXT,
    FOREIGN KEY (propriedade_id) REFERENCES propriedades(id) ON DELETE CASCADE,
    FOREIGN KEY (solo_id) REFERENCES solos(id)
);

-- ---------------------------------------------------------------------------
-- Culturas e parâmetros (rastreabilidade da origem de cada valor)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS culturas (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nome              TEXT NOT NULL UNIQUE,
    nome_cientifico   TEXT,
    codigo_aquacrop   TEXT,
    validada          INTEGER NOT NULL DEFAULT 0,
    ativa             INTEGER NOT NULL DEFAULT 1,
    observacoes       TEXT
);

CREATE TABLE IF NOT EXISTS parametros_cultura (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cultura_id      INTEGER NOT NULL,
    versao          TEXT NOT NULL,
    nome_parametro  TEXT NOT NULL,
    valor           REAL NOT NULL,
    unidade         TEXT,
    fonte           TEXT,
    validado        INTEGER NOT NULL DEFAULT 0,
    data_registro   TEXT DEFAULT CURRENT_DATE,
    FOREIGN KEY (cultura_id) REFERENCES culturas(id) ON DELETE CASCADE,
    UNIQUE (cultura_id, versao, nome_parametro)
);

-- ---------------------------------------------------------------------------
-- Clima
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS estacoes (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nome              TEXT NOT NULL,
    codigo            TEXT NOT NULL UNIQUE,
    municipio         TEXT,
    uf                TEXT,
    latitude          REAL,
    longitude         REAL,
    altitude          REAL,
    fonte             TEXT,
    eh_demonstracao   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dados_climaticos (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    estacao_id         INTEGER NOT NULL,
    data               TEXT NOT NULL,
    temperatura_min    REAL,
    temperatura_max    REAL,
    precipitacao       REAL,
    eto                REAL,
    umidade_relativa   REAL,
    velocidade_vento   REAL,
    radiacao_solar     REAL,
    origem             TEXT NOT NULL DEFAULT 'OBSERVADO',
    validado           INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (estacao_id) REFERENCES estacoes(id) ON DELETE CASCADE,
    UNIQUE (estacao_id, data)
);

-- ---------------------------------------------------------------------------
-- Solo
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS solos (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nome              TEXT NOT NULL UNIQUE,
    tipo              TEXT,
    textura           TEXT,
    codigo_aquacrop   TEXT,
    descricao         TEXT,
    validado          INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS camadas_solo (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    solo_id         INTEGER NOT NULL,
    numero_camada   INTEGER NOT NULL,
    espessura       REAL NOT NULL,
    th_wp           REAL,
    th_fc           REAL,
    th_s            REAL,
    ksat            REAL,
    penetrabilidade REAL,
    FOREIGN KEY (solo_id) REFERENCES solos(id) ON DELETE CASCADE,
    UNIQUE (solo_id, numero_camada)
);

-- ---------------------------------------------------------------------------
-- Manejo de irrigação
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS manejo_irrigacao (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                TEXT NOT NULL UNIQUE,
    metodo_aquacrop     INTEGER NOT NULL,
    limite_umidade      REAL,
    lamina_irrigacao    REAL,
    intervalo           INTEGER,
    descricao           TEXT,
    CHECK (metodo_aquacrop IN (0, 1, 2, 3))
);

CREATE TABLE IF NOT EXISTS agenda_irrigacao (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    manejo_id       INTEGER NOT NULL,
    data            TEXT NOT NULL,
    lamina          REAL NOT NULL,
    FOREIGN KEY (manejo_id) REFERENCES manejo_irrigacao(id) ON DELETE CASCADE,
    UNIQUE (manejo_id, data)
);

-- ---------------------------------------------------------------------------
-- Simulações e resultados
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS simulacoes (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                    TEXT,
    area_id                 INTEGER,
    cultura_id              INTEGER NOT NULL,
    solo_id                 INTEGER NOT NULL,
    estacao_id              INTEGER NOT NULL,
    manejo_id               INTEGER NOT NULL,
    data_plantio            TEXT NOT NULL,
    data_inicio             TEXT NOT NULL,
    data_fim                TEXT NOT NULL,
    umidade_inicial_tipo    TEXT NOT NULL DEFAULT 'FC',
    umidade_inicial_valor   REAL,
    aquacrop_version        TEXT,
    status                  TEXT NOT NULL DEFAULT 'PENDENTE',
    erro                    TEXT,
    data_execucao           TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (area_id) REFERENCES areas_agricolas(id),
    FOREIGN KEY (cultura_id) REFERENCES culturas(id),
    FOREIGN KEY (solo_id) REFERENCES solos(id),
    FOREIGN KEY (estacao_id) REFERENCES estacoes(id),
    FOREIGN KEY (manejo_id) REFERENCES manejo_irrigacao(id),
    CHECK (umidade_inicial_tipo IN ('FC', 'WP', 'SAT', 'Pct')),
    CHECK (status IN ('PENDENTE', 'EXECUTANDO', 'CONCLUIDA', 'ERRO'))
);

CREATE TABLE IF NOT EXISTS resultados (
    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacao_id                 INTEGER NOT NULL UNIQUE,
    produtividade                REAL,
    produtividade_potencial      REAL,
    biomassa_final               REAL,
    indice_colheita              REAL,
    irrigacao_sazonal            REAL,
    precipitacao_total           REAL,
    evapotranspiracao            REAL,
    produtividade_agua           REAL,
    transpiracao_relativa_media  REAL,
    unidade_produtividade        TEXT DEFAULT 'tonne/ha',
    observacoes                  TEXT,
    data_resultado               TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (simulacao_id) REFERENCES simulacoes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS crescimento_diario (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacao_id             INTEGER NOT NULL,
    data                     TEXT NOT NULL,
    dap                      INTEGER NOT NULL,
    cobertura_dossel         REAL,
    biomassa                 REAL,
    indice_colheita          REAL,
    profundidade_raiz        REAL,
    umidade_solo             REAL,
    transpiracao_relativa    REAL,
    FOREIGN KEY (simulacao_id) REFERENCES simulacoes(id) ON DELETE CASCADE,
    UNIQUE (simulacao_id, dap)
);

-- ---------------------------------------------------------------------------
-- Experimentos / calibração (funcionalidade preservada do projeto original)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS experimentos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL,
    descricao     TEXT,
    instituicao   TEXT,
    responsavel   TEXT,
    local         TEXT,
    fonte         TEXT
);

CREATE TABLE IF NOT EXISTS observacoes_experimentais (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    experimento_id       INTEGER NOT NULL,
    cultura_id           INTEGER NOT NULL,
    data_observacao      TEXT NOT NULL,
    produtividade        REAL,
    FOREIGN KEY (experimento_id) REFERENCES experimentos(id) ON DELETE CASCADE,
    FOREIGN KEY (cultura_id) REFERENCES culturas(id)
);

CREATE TABLE IF NOT EXISTS calibracoes (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    experimento_id       INTEGER NOT NULL,
    cultura_id           INTEGER NOT NULL,
    versao_aquacrop      TEXT,
    metodo_otimizacao    TEXT,
    rmse                 REAL,
    status               TEXT,
    data_calibracao      TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (experimento_id) REFERENCES experimentos(id),
    FOREIGN KEY (cultura_id) REFERENCES culturas(id)
);

CREATE TABLE IF NOT EXISTS parametros_calibrados (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    calibracao_id     INTEGER NOT NULL,
    nome_parametro    TEXT NOT NULL,
    valor_calibrado   REAL NOT NULL,
    FOREIGN KEY (calibracao_id) REFERENCES calibracoes(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- Índices
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_clima_data ON dados_climaticos(data);
CREATE INDEX IF NOT EXISTS idx_clima_estacao_data ON dados_climaticos(estacao_id, data);
CREATE INDEX IF NOT EXISTS idx_simulacoes_data ON simulacoes(data_inicio);
CREATE INDEX IF NOT EXISTS idx_crescimento_simulacao ON crescimento_diario(simulacao_id);
CREATE INDEX IF NOT EXISTS idx_resultados_simulacao ON resultados(simulacao_id);

-- ---------------------------------------------------------------------------
-- Dados iniciais (sem parâmetros científicos inventados)
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO culturas
    (nome, nome_cientifico, codigo_aquacrop, validada, observacoes)
VALUES
    ('Sorgo', 'Sorghum bicolor', 'Sorghum', 1,
     'Parâmetros embutidos do AquaCrop 3.1.0 (conjunto padrão FAO). Não calibrados para o Semiárido.'),
    ('Milheto', 'Cenchrus americanus', NULL, 0,
     'Sem parametrização no AquaCrop 3.1.0. Simulação bloqueada até parametrização documentada.');

INSERT OR IGNORE INTO solos
    (nome, tipo, codigo_aquacrop, descricao, validado)
VALUES
    ('SandyLoam', 'Franco-arenoso', 'SandyLoam', 'Perfil embutido no AquaCrop 3.1.0', 0),
    ('Loam', 'Franco', 'Loam', 'Perfil embutido no AquaCrop 3.1.0', 0),
    ('ClayLoam', 'Franco-argiloso', 'ClayLoam', 'Perfil embutido no AquaCrop 3.1.0', 0),
    ('SandyClayLoam', 'Franco-argilo-arenoso', 'SandyClayLoam', 'Perfil embutido no AquaCrop 3.1.0', 0);

INSERT OR IGNORE INTO manejo_irrigacao
    (nome, metodo_aquacrop, limite_umidade, lamina_irrigacao, intervalo, descricao)
VALUES
    ('Sequeiro', 0, NULL, NULL, NULL, 'Sem irrigação'),
    ('Irrigação por umidade', 1, 70, NULL, NULL, 'Limite de depleção de água no solo'),
    ('Irrigação por intervalo', 2, NULL, 20, 3, 'Intervalo fixo entre aplicações'),
    ('Irrigação por calendário', 3, NULL, 20, NULL, 'Datas e lâminas definidas pelo usuário');

'''TESSTE DE ESTAÇÃO'''
INSERT OR IGNORE INTO estacoes (nome,codigo, municipio, uf, latitude, longitude, altitude, fonte, eh_demonstracao
) VALUES 
('Estação Meteorológica de Petrolina','PET-001','Petrolina','PE',9.3894,-40.5006,376.5,'INMET',0);
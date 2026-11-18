
import sqlite3

# ==================================================
# 1. CONEXÃO COM O BANCO DE DADOS
# ==================================================

conexao = sqlite3.connect("sertaocrop.db")
cursor = conexao.cursor()

# Ativar chaves estrangeiras do SQLite
cursor.execute("PRAGMA foreign_keys = ON")


#parametros
cursor.execute("""
CREATE TABLE IF NOT EXISTS parametros_cultura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cultura_id INTEGER NOT NULL UNIQUE,

    CCx REAL,
    CGC REAL,
    CDC REAL,
    WP REAL,
    HI0 REAL,

    Kcb REAL,
    Zmin REAL,
    Zmax REAL,
    PlantPop REAL,

    EmergenceCD REAL,
    MaxRootingCD REAL,
    SenescenceCD REAL,
    MaturityCD REAL,
    HIstartCD REAL,
    YldFormCD REAL,

    FOREIGN KEY (cultura_id)
        REFERENCES culturas(id)
);
""")
# ==================================================
# 2. TABELA: CULTURAS
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS culturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    nome_cientifico TEXT,
    descricao TEXT,
    validada INTEGER DEFAULT 0
)
""")


# ==================================================
# 3. TABELA: ESTAÇÕES METEOROLÓGICAS
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS estacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    codigo TEXT NOT NULL UNIQUE,
    municipio TEXT,
    estado TEXT,
    latitude REAL,
    longitude REAL,
    altitude REAL,
    fonte_dados TEXT
)
""")


# ==================================================
# 4. TABELA: DADOS CLIMÁTICOS
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS dados_climaticos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estacao_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    temperatura_max REAL,
    temperatura_min REAL,
    precipitacao REAL,
    eto REAL,
    umidade_relativa REAL,
    velocidade_vento REAL,
    radiacao_solar REAL,
    origem TEXT DEFAULT 'OBSERVADO',
    validado INTEGER DEFAULT 0,

    FOREIGN KEY (estacao_id)
        REFERENCES estacoes(id),

    UNIQUE (estacao_id, data)
)
""")


# ==================================================
# 5. TABELA: SOLOS
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS solos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    tipo TEXT,
    descricao TEXT,
    codigo_aquacrop TEXT,
    validado INTEGER DEFAULT 0
)
""")


# ==================================================
# 6. TABELA: DADOS DAS CAMADAS DO SOLO
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS dado_solos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solo_id INTEGER NOT NULL,
    numero_camada INTEGER NOT NULL,
    espessura REAL,
    th_wp REAL,
    th_fc REAL,
    th_s REAL,
    ksat REAL,
    penetrabilidade REAL,

    FOREIGN KEY (solo_id)
        REFERENCES solos(id),

    UNIQUE (solo_id, numero_camada)
)
""")


# ==================================================
# 7. TABELA: MANEJO DE IRRIGAÇÃO
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS manejo_irrigacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    metodo INTEGER NOT NULL,
    limite_umidade REAL,
    lamina_irrigacao REAL,
    descricao TEXT
)
""")


# ==================================================
# 8. TABELA: AGENDA DE IRRIGAÇÃO
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS agenda_irrigacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manejo_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    lamina REAL NOT NULL,

    FOREIGN KEY (manejo_id)
        REFERENCES manejo_irrigacao(id)
)
""")


# ==================================================
# 9. TABELA: SIMULAÇÕES
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS simulacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cultura_id INTEGER NOT NULL,
    solo_id INTEGER NOT NULL,
    manejo_id INTEGER NOT NULL,
    estacao_id INTEGER,
    data_plantio TEXT NOT NULL,
    data_inicio TEXT NOT NULL,
    data_fim TEXT NOT NULL,
    umidade_inicial TEXT NOT NULL,
    status TEXT DEFAULT 'PENDENTE',
    data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cultura_id)
        REFERENCES culturas(id),

    FOREIGN KEY (solo_id)
        REFERENCES solos(id),

    FOREIGN KEY (manejo_id)
        REFERENCES manejo_irrigacao(id),

    FOREIGN KEY (estacao_id)
        REFERENCES estacoes(id),

    CHECK (umidade_inicial IN ('FC', 'WP', 'SAT')),

    CHECK (status IN (
        'PENDENTE',
        'EXECUTANDO',
        'CONCLUIDA',
        'ERRO'
    ))
)
""")


# ==================================================
# 10. TABELA: RESULTADOS
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS resultados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacao_id INTEGER NOT NULL UNIQUE,
    produtividade REAL,
    produtividade_potencial REAL,
    irrigacao_sazonal REAL,
    biomassa REAL,
    indice_colheita REAL,

    FOREIGN KEY (simulacao_id)
        REFERENCES simulacoes(id)
)
""")


# ==================================================
# 11. TABELA: CRESCIMENTO DIÁRIO
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS crescimento_diario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacao_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    dap INTEGER,
    cobertura_dossel REAL,
    biomassa REAL,

    FOREIGN KEY (simulacao_id)
        REFERENCES simulacoes(id),

    UNIQUE (simulacao_id, data)
)
""")


# ==================================================
# 12. ÍNDICES PARA MELHORAR AS CONSULTAS
# ==================================================

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_clima_data
ON dados_climaticos(data)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_simulacoes_plantio
ON simulacoes(data_plantio)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_crescimento_simulacao
ON crescimento_diario(simulacao_id)
""")


# ==================================================
# 13. PREENCHIMENTO: CULTURAS
# ==================================================

cursor.execute("""
INSERT OR IGNORE INTO culturas
(nome, nome_cientifico, descricao, validada)
VALUES
(
    'Sorgo',
    'Sorghum bicolor',
    'Cultura prevista para simulações de produtividade',
    0
),
(
    'Milheto',
    'Pennisetum glaucum',
    'Cultura cadastrada, aguardando validação dos parâmetros agronômicos',
    0
)
""")


# ==================================================
# 14. PREENCHIMENTO: ESTAÇÕES METEOROLÓGICAS
# ==================================================

cursor.execute("""
INSERT OR IGNORE INTO estacoes
(nome, codigo, municipio, estado, fonte_dados)
VALUES
(
    'Estação de demonstração',
    'DEMO001',
    'Salgueiro',
    'PE',
    'Cadastro inicial para testes'
)
""")


# ==================================================
# 15. PREENCHIMENTO: SOLOS
# ==================================================

cursor.execute("""
INSERT OR IGNORE INTO solos
(nome, tipo, descricao, codigo_aquacrop, validado)
VALUES
(
    'SandyLoam',
    'Franco-arenoso',
    'Perfil de solo disponibilizado pelo AquaCrop',
    'SandyLoam',
    0
),
(
    'Loam',
    'Franco',
    'Perfil de solo disponibilizado pelo AquaCrop',
    'Loam',
    0
),
(
    'ClayLoam',
    'Franco-argiloso',
    'Perfil de solo disponibilizado pelo AquaCrop',
    'ClayLoam',
    0
),
(
    'SandyClayLoam',
    'Franco-argilo-arenoso',
    'Perfil de solo disponibilizado pelo AquaCrop',
    'SandyClayLoam',
    0
)
""")


# ==================================================
# 16. PREENCHIMENTO: MANEJOS DE IRRIGAÇÃO
# ==================================================

cursor.execute("""
INSERT OR IGNORE INTO manejo_irrigacao
(nome, metodo, limite_umidade, lamina_irrigacao, descricao)
VALUES
(
    'Sequeiro',
    0,
    NULL,
    NULL,
    'Simulação sem irrigação'
),
(
    'Irrigação por limite de umidade',
    1,
    70,
    NULL,
    'Irrigação controlada por limite de umidade do solo'
),
(
    'Irrigação por calendário',
    3,
    NULL,
    20,
    'Irrigação programada em datas específicas'
)
""")


# ==================================================
# 17. CONSULTAS PARA CONFERIR OS CADASTROS
# ==================================================

print("\\n========== CULTURAS ==========")

cursor.execute("""
SELECT id, nome, nome_cientifico, validada
FROM culturas
""")

for registro in cursor.fetchall():
    print(registro)


print("\\n========== SOLOS ==========")

cursor.execute("""
SELECT id, nome, tipo, codigo_aquacrop
FROM solos
""")

for registro in cursor.fetchall():
    print(registro)


print("\\n========== MANEJOS ==========")

cursor.execute("""
SELECT id, nome, metodo, limite_umidade, lamina_irrigacao
FROM manejo_irrigacao
""")

for registro in cursor.fetchall():
    print(registro)


print("\\n========== ESTAÇÕES ==========")

cursor.execute("""
SELECT id, nome, codigo, municipio, estado
FROM estacoes
""")

for registro in cursor.fetchall():
    print(registro)


# ==================================================
# 18. FINALIZAÇÃO
# ==================================================

conexao.commit()
conexao.close()

print("\\nBanco de dados SertãoCrop criado e preenchido!")

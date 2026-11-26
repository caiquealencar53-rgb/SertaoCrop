# -*- coding: utf-8 -*-
"""Repositórios SQLite: única porta de entrada para persistência.

Todas as funções recebem uma conexão aberta por ``database.connect``.
"""

from __future__ import annotations

from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Cadastro agrícola
# ---------------------------------------------------------------------------


def add_agricultor(conn, nome, **campos):
    cur = conn.execute(
        """INSERT INTO agricultores (nome, cpf_cnpj, telefone, email)
           VALUES (:nome, :cpf_cnpj, :telefone, :email)""",
        {
            "nome": nome.strip(),
            "cpf_cnpj": campos.get("cpf_cnpj"),
            "telefone": campos.get("telefone"),
            "email": campos.get("email"),
        },
    )
    return cur.lastrowid


def list_agricultores(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM agricultores ORDER BY nome")]


def add_propriedade(conn, nome, agricultor_id=None, **campos):
    cur = conn.execute(
        """INSERT INTO propriedades
           (agricultor_id, nome, municipio, uf, latitude, longitude, area_total_ha, observacoes)
           VALUES (:agricultor_id, :nome, :municipio, :uf, :latitude, :longitude,
                   :area_total_ha, :observacoes)""",
        {
            "agricultor_id": agricultor_id,
            "nome": nome.strip(),
            "municipio": campos.get("municipio"),
            "uf": campos.get("uf"),
            "latitude": campos.get("latitude"),
            "longitude": campos.get("longitude"),
            "area_total_ha": campos.get("area_total_ha"),
            "observacoes": campos.get("observacoes"),
        },
    )
    return cur.lastrowid


def list_propriedades(conn):
    return [
        dict(r)
        for r in conn.execute(
            """SELECT p.*, a.nome AS agricultor_nome
               FROM propriedades p LEFT JOIN agricultores a ON a.id = p.agricultor_id
               ORDER BY p.nome"""
        )
    ]


def add_area(conn, propriedade_id, nome, **campos):
    cur = conn.execute(
        """INSERT INTO areas_agricolas
           (propriedade_id, nome, solo_id, latitude, longitude, area_ha, observacoes)
           VALUES (:propriedade_id, :nome, :solo_id, :latitude, :longitude,
                   :area_ha, :observacoes)""",
        {
            "propriedade_id": propriedade_id,
            "nome": nome.strip(),
            "solo_id": campos.get("solo_id"),
            "latitude": campos.get("latitude"),
            "longitude": campos.get("longitude"),
            "area_ha": campos.get("area_ha"),
            "observacoes": campos.get("observacoes"),
        },
    )
    return cur.lastrowid


def list_areas(conn):
    return [
        dict(r)
        for r in conn.execute(
            """SELECT ar.*, pr.nome AS propriedade_nome, s.nome AS solo_nome
               FROM areas_agricolas ar
               JOIN propriedades pr ON pr.id = ar.propriedade_id
               LEFT JOIN solos s ON s.id = ar.solo_id
               ORDER BY pr.nome, ar.nome"""
        )
    ]


def delete_agricultor(conn, registro_id):
    conn.execute("DELETE FROM agricultores WHERE id = ?", (registro_id,))


def delete_propriedade(conn, registro_id):
    conn.execute("DELETE FROM propriedades WHERE id = ?", (registro_id,))


def delete_area(conn, registro_id):
    conn.execute("DELETE FROM areas_agricolas WHERE id = ?", (registro_id,))


# ---------------------------------------------------------------------------
# Culturas
# ---------------------------------------------------------------------------


def list_culturas(conn, apenas_ativas=True):
    sql = "SELECT * FROM culturas"
    if apenas_ativas:
        sql += " WHERE ativa = 1"
    sql += " ORDER BY nome"
    return [dict(r) for r in conn.execute(sql)]


def get_cultura(conn, cultura_id):
    r = conn.execute("SELECT * FROM culturas WHERE id = ?", (cultura_id,)).fetchone()
    return dict(r) if r else None


def get_cultura_por_nome(conn, nome):
    r = conn.execute("SELECT * FROM culturas WHERE nome = ?", (nome,)).fetchone()
    return dict(r) if r else None


def upsert_cultura(conn, nome, codigo_aquacrop=None, nome_cientifico=None,
                   validada=0, observacoes=None):
    conn.execute(
        """INSERT INTO culturas
           (nome, nome_cientifico, codigo_aquacrop, validada, observacoes)
           VALUES (:nome, :cientifico, :codigo, :validada, :observacoes)
           ON CONFLICT(nome) DO UPDATE SET
               nome_cientifico=excluded.nome_cientifico,
               codigo_aquacrop=excluded.codigo_aquacrop,
               validada=excluded.validada,
               observacoes=excluded.observacoes""",
        {
            "nome": nome.strip(),
            "cientifico": nome_cientifico,
            "codigo": codigo_aquacrop,
            "validada": int(validada),
            "observacoes": observacoes,
        },
    )
    return get_cultura_por_nome(conn, nome)["id"]


def list_parametros_cultura(conn, cultura_id, versao=None):
    if versao:
        rows = conn.execute(
            """SELECT * FROM parametros_cultura
               WHERE cultura_id = ? AND versao = ? ORDER BY nome_parametro""",
            (cultura_id, versao),
        )
    else:
        rows = conn.execute(
            "SELECT * FROM parametros_cultura WHERE cultura_id = ? ORDER BY versao, nome_parametro",
            (cultura_id,),
        )
    return [dict(r) for r in rows]


def set_parametros_cultura(conn, cultura_id, versao, parametros, fonte=None, validado=0):
    """Registra parâmetros com fonte declarada. Nunca inventa valores."""
    for nome, valor in parametros.items():
        conn.execute(
            """INSERT INTO parametros_cultura
               (cultura_id, versao, nome_parametro, valor, fonte, validado)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(cultura_id, versao, nome_parametro) DO UPDATE SET
                   valor=excluded.valor, fonte=excluded.fonte, validado=excluded.validado""",
            (cultura_id, versao, nome, float(valor), fonte, int(validado)),
        )


# ---------------------------------------------------------------------------
# Clima
# ---------------------------------------------------------------------------


def add_estacao(conn, nome, codigo, **campos):
    cur = conn.execute(
        """INSERT INTO estacoes
           (nome, codigo, municipio, uf, latitude, longitude, altitude, fonte, eh_demonstracao)
           VALUES (:nome, :codigo, :municipio, :uf, :latitude, :longitude, :altitude,
                   :fonte, :eh_demonstracao)""",
        {
            "nome": nome.strip(),
            "codigo": codigo.strip(),
            "municipio": campos.get("municipio"),
            "uf": campos.get("uf"),
            "latitude": campos.get("latitude"),
            "longitude": campos.get("longitude"),
            "altitude": campos.get("altitude"),
            "fonte": campos.get("fonte"),
            "eh_demonstracao": int(campos.get("eh_demonstracao", 0)),
        },
    )
    return cur.lastrowid


def list_estacoes(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM estacoes ORDER BY nome")]


def get_estacao(conn, estacao_id):
    r = conn.execute("SELECT * FROM estacoes WHERE id = ?", (estacao_id,)).fetchone()
    return dict(r) if r else None


def delete_estacao(conn, estacao_id):
    conn.execute("DELETE FROM estacoes WHERE id = ?", (estacao_id,))


def upsert_clima(conn, estacao_id, registros, origem="OBSERVADO", validado=0):
    """Insere ou atualiza dias climáticos. ``registros``: lista de dicts."""
    sql = """
        INSERT INTO dados_climaticos
            (estacao_id, data, temperatura_min, temperatura_max, precipitacao, eto,
             umidade_relativa, velocidade_vento, radiacao_solar, origem, validado)
        VALUES
            (:estacao_id, :data, :temperatura_min, :temperatura_max, :precipitacao, :eto,
             :umidade_relativa, :velocidade_vento, :radiacao_solar, :origem, :validado)
        ON CONFLICT(estacao_id, data) DO UPDATE SET
            temperatura_min=excluded.temperatura_min,
            temperatura_max=excluded.temperatura_max,
            precipitacao=excluded.precipitacao,
            eto=excluded.eto,
            umidade_relativa=excluded.umidade_relativa,
            velocidade_vento=excluded.velocidade_vento,
            radiacao_solar=excluded.radiacao_solar,
            origem=excluded.origem,
            validado=excluded.validado
    """
    for registro in registros:
        conn.execute(
            sql,
            {
                "estacao_id": estacao_id,
                "data": registro["data"].strftime("%Y-%m-%d"),
                "temperatura_min": registro["temperatura_min"],
                "temperatura_max": registro["temperatura_max"],
                "precipitacao": registro["precipitacao"],
                "eto": registro["eto"],
                "umidade_relativa": registro.get("umidade_relativa"),
                "velocidade_vento": registro.get("velocidade_vento"),
                "radiacao_solar": registro.get("radiacao_solar"),
                "origem": origem,
                "validado": int(validado),
            },
        )
    return len(registros)


def get_clima(conn, estacao_id, inicio=None, fim=None):
    sql = "SELECT * FROM dados_climaticos WHERE estacao_id = ?"
    params = [estacao_id]
    if inicio:
        sql += " AND data >= ?"
        params.append(inicio)
    if fim:
        sql += " AND data <= ?"
        params.append(fim)
    sql += " ORDER BY data"
    return [dict(r) for r in conn.execute(sql, params)]


def contar_clima(conn, estacao_id=None):
    if estacao_id is None:
        r = conn.execute("SELECT COUNT(*) AS n FROM dados_climaticos").fetchone()
    else:
        r = conn.execute(
            "SELECT COUNT(*) AS n FROM dados_climaticos WHERE estacao_id = ?", (estacao_id,)
        ).fetchone()
    return r["n"]


# ---------------------------------------------------------------------------
# Solo
# ---------------------------------------------------------------------------


def add_solo(conn, nome, tipo=None, textura=None, codigo_aquacrop=None,
             descricao=None, validado=0):
    cur = conn.execute(
        """INSERT INTO solos (nome, tipo, textura, codigo_aquacrop, descricao, validado)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (nome.strip(), tipo, textura, codigo_aquacrop, descricao, int(validado)),
    )
    return cur.lastrowid


def list_solos(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM solos ORDER BY nome")]


def get_solo(conn, solo_id):
    r = conn.execute("SELECT * FROM solos WHERE id = ?", (solo_id,)).fetchone()
    if not r:
        return None
    solo = dict(r)
    solo["camadas"] = [
        dict(c)
        for c in conn.execute(
            """SELECT * FROM camadas_solo WHERE solo_id = ?
               ORDER BY numero_camada""",
            (solo_id,),
        )
    ]
    return solo


def add_camada_solo(conn, solo_id, numero_camada, espessura, th_wp, th_fc, th_s,
                    ksat, penetrabilidade=100):
    conn.execute(
        """INSERT INTO camadas_solo
           (solo_id, numero_camada, espessura, th_wp, th_fc, th_s, ksat, penetrabilidade)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(solo_id, numero_camada) DO UPDATE SET
               espessura=excluded.espessura, th_wp=excluded.th_wp, th_fc=excluded.th_fc,
               th_s=excluded.th_s, ksat=excluded.ksat,
               penetrabilidade=excluded.penetrabilidade""",
        (solo_id, numero_camada, espessura, th_wp, th_fc, th_s, ksat, penetrabilidade),
    )


def delete_solo(conn, solo_id):
    conn.execute("DELETE FROM solos WHERE id = ?", (solo_id,))


# ---------------------------------------------------------------------------
# Irrigação
# ---------------------------------------------------------------------------


def add_manejo(conn, nome, metodo, limite_umidade=None, lamina_irrigacao=None,
               descricao=None, intervalo=None):
    cur = conn.execute(
        """INSERT INTO manejo_irrigacao
           (nome, metodo_aquacrop, limite_umidade, lamina_irrigacao, intervalo, descricao)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (nome.strip(), metodo, limite_umidade, lamina_irrigacao, intervalo, descricao),
    )
    return cur.lastrowid


def list_manejos(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM manejo_irrigacao ORDER BY nome")]


def get_manejo(conn, manejo_id):
    r = conn.execute(
        "SELECT * FROM manejo_irrigacao WHERE id = ?", (manejo_id,)
    ).fetchone()
    if not r:
        return None
    manejo = dict(r)
    manejo["agenda"] = [
        dict(a)
        for a in conn.execute(
            "SELECT * FROM agenda_irrigacao WHERE manejo_id = ? ORDER BY data", (manejo_id,)
        )
    ]
    return manejo


def set_agenda_irrigacao(conn, manejo_id, eventos):
    conn.execute("DELETE FROM agenda_irrigacao WHERE manejo_id = ?", (manejo_id,))
    for data_irrigacao, lamina in eventos:
        conn.execute(
            """INSERT INTO agenda_irrigacao (manejo_id, data, lamina) VALUES (?, ?, ?)""",
            (manejo_id, str(data_irrigacao), float(lamina)),
        )


# ---------------------------------------------------------------------------
# Simulações
# ---------------------------------------------------------------------------


def create_simulacao(conn, dados):
    cur = conn.execute(
        """INSERT INTO simulacoes
           (nome, area_id, cultura_id, solo_id, estacao_id, manejo_id, data_plantio,
            data_inicio, data_fim, umidade_inicial_tipo, umidade_inicial_valor,
            aquacrop_version, status)
           VALUES (:nome, :area_id, :cultura_id, :solo_id, :estacao_id, :manejo_id,
                   :data_plantio, :data_inicio, :data_fim, :umidade_inicial_tipo,
                   :umidade_inicial_valor, :aquacrop_version, 'PENDENTE')""",
        dados,
    )
    return cur.lastrowid


def set_status(conn, simulacao_id, status, erro=None):
    conn.execute(
        """UPDATE simulacoes
           SET status = ?, erro = ?, data_execucao = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (status, erro, simulacao_id),
    )


def get_simulacao(conn, simulacao_id):
    r = conn.execute(
        """SELECT s.*, c.nome AS cultura_nome, so.nome AS solo_nome,
                  e.nome AS estacao_nome, m.nome AS manejo_nome,
                  ar.nome AS area_nome, pr.nome AS propriedade_nome
           FROM simulacoes s
           JOIN culturas c ON c.id = s.cultura_id
           JOIN solos so ON so.id = s.solo_id
           JOIN estacoes e ON e.id = s.estacao_id
           JOIN manejo_irrigacao m ON m.id = s.manejo_id
           LEFT JOIN areas_agricolas ar ON ar.id = s.area_id
           LEFT JOIN propriedades pr ON pr.id = ar.propriedade_id
           WHERE s.id = ?""",
        (simulacao_id,),
    ).fetchone()
    return dict(r) if r else None


def list_simulacoes(conn, limite=None):
    sql = """
        SELECT s.id, s.nome, s.status, s.data_plantio, s.data_inicio, s.data_fim,
               s.aquacrop_version, s.data_execucao, s.erro,
               c.nome AS cultura_nome, so.nome AS solo_nome, e.nome AS estacao_nome,
               m.nome AS manejo_nome, ar.nome AS area_nome,
               r.produtividade
        FROM simulacoes s
        JOIN culturas c ON c.id = s.cultura_id
        JOIN solos so ON so.id = s.solo_id
        JOIN estacoes e ON e.id = s.estacao_id
        JOIN manejo_irrigacao m ON m.id = s.manejo_id
        LEFT JOIN areas_agricolas ar ON ar.id = s.area_id
        LEFT JOIN resultados r ON r.simulacao_id = s.id
        ORDER BY s.id DESC
    """
    if limite:
        sql += " LIMIT ?"
        return [dict(r) for r in conn.execute(sql, (limite,))]
    return [dict(r) for r in conn.execute(sql)]


def save_resultado(conn, simulacao_id, metricas):
    conn.execute(
        """INSERT INTO resultados
           (simulacao_id, produtividade, produtividade_potencial, biomassa_final,
            indice_colheita, irrigacao_sazonal, precipitacao_total, evapotranspiracao,
            produtividade_agua, transpiracao_relativa_media, observacoes)
           VALUES (:simulacao_id, :produtividade, :produtividade_potencial,
                   :biomassa_final, :indice_colheita, :irrigacao_sazonal,
                   :precipitacao_total, :evapotranspiracao, :produtividade_agua,
                   :transpiracao_relativa_media, :observacoes)
           ON CONFLICT(simulacao_id) DO UPDATE SET
               produtividade=excluded.produtividade,
               produtividade_potencial=excluded.produtividade_potencial,
               biomassa_final=excluded.biomassa_final,
               indice_colheita=excluded.indice_colheita,
               irrigacao_sazonal=excluded.irrigacao_sazonal,
               precipitacao_total=excluded.precipitacao_total,
               evapotranspiracao=excluded.evapotranspiracao,
               produtividade_agua=excluded.produtividade_agua,
               transpiracao_relativa_media=excluded.transpiracao_relativa_media,
               observacoes=excluded.observacoes""",
        {"simulacao_id": simulacao_id, **metricas},
    )


def get_resultado(conn, simulacao_id):
    r = conn.execute(
        "SELECT * FROM resultados WHERE simulacao_id = ?", (simulacao_id,)
    ).fetchone()
    return dict(r) if r else None


def save_crescimento_diario(conn, simulacao_id, registros):
    conn.execute("DELETE FROM crescimento_diario WHERE simulacao_id = ?", (simulacao_id,))
    conn.executemany(
        """INSERT INTO crescimento_diario
           (simulacao_id, data, dap, cobertura_dossel, biomassa, indice_colheita,
            profundidade_raiz, umidade_solo, transpiracao_relativa)
           VALUES (:simulacao_id, :data, :dap, :cobertura_dossel, :biomassa,
                   :indice_colheita, :profundidade_raiz, :umidade_solo,
                   :transpiracao_relativa)""",
        [{"simulacao_id": simulacao_id, **r} for r in registros],
    )


def get_crescimento_diario(conn, simulacao_id):
    return [
        dict(r)
        for r in conn.execute(
            """SELECT * FROM crescimento_diario WHERE simulacao_id = ? ORDER BY dap""",
            (simulacao_id,),
        )
    ]


def datas_simulacao(inicio, plantio, fim):
    """Converte strings YYYY-MM-DD e garante ordem plantio <= fim."""
    ini = date.fromisoformat(inicio)
    plant = date.fromisoformat(plantio)
    fim_dt = date.fromisoformat(fim)
    if not (ini <= plant <= fim_dt):
        raise ValueError("Datas devem satisfazer: início <= plantio <= fim.")
    return ini, plant, fim_dt, [ini + timedelta(days=i) for i in range((fim_dt - ini).days + 1)]


# ---------------------------------------------------------------------------
# Experimentos (calibração preservada)
# ---------------------------------------------------------------------------


def add_experimento(conn, nome, **campos):
    cur = conn.execute(
        """INSERT INTO experimentos (nome, descricao, instituicao, responsavel, local, fonte)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            nome.strip(),
            campos.get("descricao"),
            campos.get("instituicao"),
            campos.get("responsavel"),
            campos.get("local"),
            campos.get("fonte"),
        ),
    )
    return cur.lastrowid


def list_experimentos(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM experimentos ORDER BY nome")]


def add_observacao_experimental(conn, experimento_id, cultura_id, data_observacao,
                                produtividade):
    conn.execute(
        """INSERT INTO observacoes_experimentais
           (experimento_id, cultura_id, data_observacao, produtividade)
           VALUES (?, ?, ?, ?)""",
        (experimento_id, cultura_id, str(data_observacao), float(produtividade)),
    )


def list_observacoes(conn, experimento_id):
    return [
        dict(r)
        for r in conn.execute(
            """SELECT * FROM observacoes_experimentais WHERE experimento_id = ?""",
            (experimento_id,),
        )
    ]

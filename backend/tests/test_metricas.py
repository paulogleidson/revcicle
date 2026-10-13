from datetime import date

from app import models


def _criar_conteudo(client, titulo, materia) -> int:
    r = client.post("/conteudos", json={"titulo": titulo, "materia": materia})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _registrar(client, conteudo_id, percentual, data):
    r = client.post(
        "/sessoes",
        json={"conteudo_id": conteudo_id, "percentual": percentual, "data": data},
    )
    assert r.status_code == 201, r.text


def test_usuario_sem_revisoes_recebe_listas_vazias(client):
    _criar_conteudo(client, "Nunca revisado", "Português")

    r = client.get("/metricas")

    assert r.status_code == 200
    assert r.json() == {"evolucao": [], "por_materia": [], "calendario": []}


def test_evolucao_lista_pontos_em_ordem_cronologica(client):
    cid = _criar_conteudo(client, "Cálculo I", "Matemática")
    _registrar(client, cid, 80, "2026-10-10")
    _registrar(client, cid, 50, "2026-10-01")
    _registrar(client, cid, 100, "2026-10-20")

    evolucao = client.get("/metricas").json()["evolucao"]

    assert len(evolucao) == 1
    assert evolucao[0]["titulo"] == "Cálculo I"
    assert evolucao[0]["materia"] == "Matemática"
    assert evolucao[0]["pontos"] == [
        {"data": "2026-10-01", "percentual": 50.0},
        {"data": "2026-10-10", "percentual": 80.0},
        {"data": "2026-10-20", "percentual": 100.0},
    ]


def test_por_materia_calcula_media_e_ordena_pela_maior(client):
    calc = _criar_conteudo(client, "Cálculo I", "Matemática")
    alg = _criar_conteudo(client, "Álgebra", "Matemática")
    crase = _criar_conteudo(client, "Crase", "Português")
    _registrar(client, calc, 60, "2026-10-01")
    _registrar(client, alg, 75, "2026-10-02")
    _registrar(client, crase, 90, "2026-10-03")

    por_materia = client.get("/metricas").json()["por_materia"]

    assert por_materia == [
        {"materia": "Português", "media_percentual": 90.0, "total_revisoes": 1},
        {"materia": "Matemática", "media_percentual": 67.5, "total_revisoes": 2},
    ]


def test_calendario_marca_realizadas_e_so_a_proxima_revisao_vigente(client):
    cid = _criar_conteudo(client, "Cálculo I", "Matemática")
    # 50% em 01/10 agendaria 02/10, mas a revisão de 05/10 (100%) substitui
    # esse agendamento por 04/11 (+30 dias).
    _registrar(client, cid, 50, "2026-10-01")
    _registrar(client, cid, 100, "2026-10-05")

    calendario = client.get("/metricas").json()["calendario"]

    assert calendario == [
        {
            "data": "2026-10-01",
            "realizadas": [{"conteudo_id": cid, "titulo": "Cálculo I", "percentual": 50.0}],
            "agendadas": [],
        },
        {
            "data": "2026-10-05",
            "realizadas": [{"conteudo_id": cid, "titulo": "Cálculo I", "percentual": 100.0}],
            "agendadas": [],
        },
        {
            "data": "2026-11-04",
            "realizadas": [],
            "agendadas": [{"conteudo_id": cid, "titulo": "Cálculo I", "percentual": None}],
        },
    ]


def test_nao_inclui_dados_de_outro_usuario(client, db_session):
    db_session.add(models.Usuario(id=2, email="outro@local", senha_hash="x"))
    db_session.commit()
    alheio = models.Conteudo(usuario_id=2, titulo="alheio", materia="Secreta")
    db_session.add(alheio)
    db_session.commit()
    db_session.add(
        models.SessaoRevisao(
            conteudo_id=alheio.id,
            data=date(2026, 10, 1),
            percentual=90,
            proxima_revisao=date(2026, 10, 8),
        )
    )
    db_session.commit()

    meu = _criar_conteudo(client, "meu", "Minha")
    _registrar(client, meu, 70, "2026-10-01")

    body = client.get("/metricas").json()

    assert [e["titulo"] for e in body["evolucao"]] == ["meu"]
    assert [m["materia"] for m in body["por_materia"]] == ["Minha"]
    titulos_no_calendario = {
        item["titulo"]
        for dia in body["calendario"]
        for item in dia["realizadas"] + dia["agendadas"]
    }
    assert titulos_no_calendario == {"meu"}

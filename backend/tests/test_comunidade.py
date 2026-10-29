from contextlib import contextmanager

import pytest

from app import models
from app.auth import get_current_user_id
from app.main import app
from app.services.comunidade import disciplinas_em_comum, normalizar_materia

OUTRO_ID = 2


@contextmanager
def como_usuario(usuario_id: int):
    """Troca o usuário logado durante o bloco (o padrão do conftest é o id 1)."""
    anterior = app.dependency_overrides[get_current_user_id]
    app.dependency_overrides[get_current_user_id] = lambda: usuario_id
    try:
        yield
    finally:
        app.dependency_overrides[get_current_user_id] = anterior


@pytest.fixture()
def outro_usuario(db_session):
    db_session.add(models.Usuario(id=OUTRO_ID, email="outro@local", senha_hash=None))
    db_session.commit()
    return OUTRO_ID


def _criar_perfil(client, apelido):
    r = client.put("/comunidade/perfil", json={"apelido": apelido})
    assert r.status_code == 200, r.text
    return r.json()


def _postar(client, texto):
    r = client.post("/comunidade/posts", json={"texto": texto})
    assert r.status_code == 201, r.text
    return r.json()


# --- Regras puras -----------------------------------------------------------


def test_normalizar_materia_ignora_acento_caixa_e_espacos():
    assert normalizar_materia("  Matemática   Básica ") == "matematica basica"
    assert normalizar_materia("MATEMATICA BÁSICA") == "matematica basica"


def test_disciplinas_em_comum_usa_grafia_de_quem_ve_e_ordena():
    minhas = ["Português", "matemática", "História", "Matemática"]
    dele = ["MATEMATICA", "portugues", "Física"]

    assert disciplinas_em_comum(minhas, dele) == ["matemática", "Português"]


def test_disciplinas_em_comum_vazia_quando_nao_ha_intersecao():
    assert disciplinas_em_comum(["Química"], ["Biologia"]) == []
    assert disciplinas_em_comum([], ["Biologia"]) == []


# --- Perfil -----------------------------------------------------------------


def test_perfil_inexistente_devolve_404(client):
    assert client.get("/comunidade/perfil").status_code == 404


def test_cria_e_renomeia_perfil(client):
    criado = _criar_perfil(client, "  paulo.g  ")
    assert criado["apelido"] == "paulo.g"
    assert criado["usuario_id"] == 1

    renomeado = _criar_perfil(client, "Paulo G")
    assert renomeado["apelido"] == "Paulo G"
    assert client.get("/comunidade/perfil").json()["apelido"] == "Paulo G"


@pytest.mark.parametrize("apelido", ["ab", "x" * 31, "tem@arroba", "   "])
def test_apelido_invalido_devolve_422(client, apelido):
    r = client.put("/comunidade/perfil", json={"apelido": apelido})
    assert r.status_code == 422


def test_apelido_repetido_sem_diferenciar_maiusculas_devolve_409(client, outro_usuario):
    with como_usuario(outro_usuario):
        _criar_perfil(client, "Concurseira")

    r = client.put("/comunidade/perfil", json={"apelido": "concurseira"})
    assert r.status_code == 409


def test_perfil_publico_mostra_disciplinas_em_comum_e_total_de_posts(
    client, db_session, outro_usuario
):
    db_session.add_all(
        [
            models.Conteudo(usuario_id=1, titulo="Crase", materia="Português"),
            models.Conteudo(usuario_id=1, titulo="Frações", materia="Matemática"),
            models.Conteudo(usuario_id=OUTRO_ID, titulo="Regência", materia="portugues"),
            models.Conteudo(usuario_id=OUTRO_ID, titulo="Leis", materia="Direito"),
        ]
    )
    db_session.commit()
    _criar_perfil(client, "eu-mesmo")
    with como_usuario(outro_usuario):
        _criar_perfil(client, "Concurseira")
        _postar(client, "primeiro")
        _postar(client, "segundo")

    r = client.get(f"/comunidade/usuarios/{OUTRO_ID}")

    assert r.status_code == 200
    body = r.json()
    assert body["apelido"] == "Concurseira"
    assert body["total_posts"] == 2
    assert body["disciplinas_em_comum"] == ["Português"]
    # Email nunca aparece na comunidade.
    assert "email" not in body


def test_perfil_publico_de_quem_nao_entrou_na_comunidade_devolve_404(client, outro_usuario):
    assert client.get(f"/comunidade/usuarios/{OUTRO_ID}").status_code == 404


# --- Posts ------------------------------------------------------------------


def test_postar_sem_perfil_devolve_403(client):
    r = client.post("/comunidade/posts", json={"texto": "oi"})
    assert r.status_code == 403


def test_post_vazio_ou_longo_demais_devolve_422(client):
    _criar_perfil(client, "eu-mesmo")
    assert client.post("/comunidade/posts", json={"texto": "   "}).status_code == 422
    assert client.post("/comunidade/posts", json={"texto": "x" * 1001}).status_code == 422


def test_feed_lista_posts_de_todos_mais_recentes_primeiro(client, outro_usuario):
    _criar_perfil(client, "eu-mesmo")
    _postar(client, "post meu")
    with como_usuario(outro_usuario):
        _criar_perfil(client, "Concurseira")
        _postar(client, "post dela")

    feed = client.get("/comunidade/posts").json()

    assert [p["texto"] for p in feed] == ["post dela", "post meu"]
    assert [p["autor"]["apelido"] for p in feed] == ["Concurseira", "eu-mesmo"]
    assert [p["meu"] for p in feed] == [False, True]
    assert all(p["total_comentarios"] == 0 for p in feed)


def test_feed_pagina_com_antes_de_e_limite(client):
    _criar_perfil(client, "eu-mesmo")
    ids = [_postar(client, f"post {i}")["id"] for i in range(5)]

    primeira = client.get("/comunidade/posts", params={"limite": 2}).json()
    segunda = client.get(
        "/comunidade/posts", params={"limite": 2, "antes_de": primeira[-1]["id"]}
    ).json()

    assert [p["id"] for p in primeira] == [ids[4], ids[3]]
    assert [p["id"] for p in segunda] == [ids[2], ids[1]]


def test_detalhe_traz_comentarios_em_ordem_e_contagem_no_feed(client, outro_usuario):
    _criar_perfil(client, "eu-mesmo")
    post = _postar(client, "dúvida sobre crase")
    with como_usuario(outro_usuario):
        _criar_perfil(client, "Concurseira")
        r = client.post(f"/comunidade/posts/{post['id']}/comentarios", json={"texto": "antes de 'a'"})
        assert r.status_code == 201, r.text
    client.post(f"/comunidade/posts/{post['id']}/comentarios", json={"texto": "valeu!"})

    detalhe = client.get(f"/comunidade/posts/{post['id']}").json()

    assert detalhe["total_comentarios"] == 2
    assert [(c["autor"]["apelido"], c["texto"], c["meu"]) for c in detalhe["comentarios"]] == [
        ("Concurseira", "antes de 'a'", False),
        ("eu-mesmo", "valeu!", True),
    ]
    assert client.get("/comunidade/posts").json()[0]["total_comentarios"] == 2


def test_detalhe_de_post_inexistente_devolve_404(client):
    assert client.get("/comunidade/posts/999").status_code == 404


def test_apagar_post_proprio_remove_comentarios_junto(client, db_session):
    _criar_perfil(client, "eu-mesmo")
    post = _postar(client, "vou apagar")
    client.post(f"/comunidade/posts/{post['id']}/comentarios", json={"texto": "c1"})

    r = client.delete(f"/comunidade/posts/{post['id']}")

    assert r.status_code == 204
    assert client.get(f"/comunidade/posts/{post['id']}").status_code == 404
    assert db_session.query(models.Comentario).count() == 0


def test_nao_apaga_post_de_outra_pessoa(client, outro_usuario):
    with como_usuario(outro_usuario):
        _criar_perfil(client, "Concurseira")
        post = _postar(client, "meu post")

    assert client.delete(f"/comunidade/posts/{post['id']}").status_code == 403
    assert client.get(f"/comunidade/posts/{post['id']}").status_code == 200


# --- Comentários ------------------------------------------------------------


def test_comentar_sem_perfil_devolve_403(client, outro_usuario):
    with como_usuario(outro_usuario):
        _criar_perfil(client, "Concurseira")
        post = _postar(client, "post")

    r = client.post(f"/comunidade/posts/{post['id']}/comentarios", json={"texto": "oi"})
    assert r.status_code == 403


def test_comentar_em_post_inexistente_devolve_404(client):
    _criar_perfil(client, "eu-mesmo")
    r = client.post("/comunidade/posts/999/comentarios", json={"texto": "oi"})
    assert r.status_code == 404


def test_apagar_comentario_so_pelo_autor(client, outro_usuario):
    _criar_perfil(client, "eu-mesmo")
    post = _postar(client, "post")
    with como_usuario(outro_usuario):
        _criar_perfil(client, "Concurseira")
        dela = client.post(f"/comunidade/posts/{post['id']}/comentarios", json={"texto": "dela"}).json()
    meu = client.post(f"/comunidade/posts/{post['id']}/comentarios", json={"texto": "meu"}).json()

    assert client.delete(f"/comunidade/comentarios/{dela['id']}").status_code == 403
    assert client.delete(f"/comunidade/comentarios/{meu['id']}").status_code == 204
    restantes = client.get(f"/comunidade/posts/{post['id']}").json()["comentarios"]
    assert [c["texto"] for c in restantes] == ["dela"]

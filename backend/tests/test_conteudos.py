from datetime import date

from app import models


def test_get_conteudos_vazio_devolve_lista_vazia(client):
    r = client.get("/conteudos")
    assert r.status_code == 200
    assert r.json() == []


def test_criar_conteudo_devolve_201_com_payload_e_ids(client, mock_user_id):
    r = client.post(
        "/conteudos",
        json={"titulo": "Cálculo I - Limites", "materia": "Matemática"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["titulo"] == "Cálculo I - Limites"
    assert body["materia"] == "Matemática"
    assert body["usuario_id"] == mock_user_id
    assert isinstance(body["id"], int)
    assert "criado_em" in body


def test_conteudo_criado_aparece_na_listagem(client):
    client.post("/conteudos", json={"titulo": "Fotossíntese", "materia": "Biologia"})
    r = client.get("/conteudos")
    assert r.status_code == 200
    dados = r.json()
    assert len(dados) == 1
    assert dados[0]["titulo"] == "Fotossíntese"


def test_listagem_ordena_do_mais_recente_para_o_mais_antigo(client):
    # Ordenação é por criado_em desc, com id desc como desempate
    # (SQLite dá granularidade de segundo em criado_em).
    client.post("/conteudos", json={"titulo": "Primeiro", "materia": "Mat"})
    client.post("/conteudos", json={"titulo": "Segundo", "materia": "Mat"})
    client.post("/conteudos", json={"titulo": "Terceiro", "materia": "Mat"})
    r = client.get("/conteudos")
    titulos = [c["titulo"] for c in r.json()]
    assert titulos == ["Terceiro", "Segundo", "Primeiro"]


def test_payload_sem_materia_devolve_422(client):
    r = client.post("/conteudos", json={"titulo": "Só título"})
    assert r.status_code == 422


def test_payload_sem_titulo_devolve_422(client):
    r = client.post("/conteudos", json={"materia": "Só matéria"})
    assert r.status_code == 422


def test_body_ignora_usuario_id_do_cliente(client, mock_user_id):
    # Segurança: mesmo se o cliente mandar usuario_id, é o autenticado que vale.
    r = client.post(
        "/conteudos",
        json={"titulo": "X", "materia": "Y", "usuario_id": 9999},
    )
    assert r.status_code == 201
    assert r.json()["usuario_id"] == mock_user_id


# ---------------- proxima_revisao na listagem ----------------

class TestProximaRevisaoNaListagem:
    def test_conteudo_sem_sessao_tem_proxima_revisao_null(self, client):
        client.post("/conteudos", json={"titulo": "A", "materia": "M"})
        r = client.get("/conteudos")
        assert r.status_code == 200
        assert r.json()[0]["proxima_revisao"] is None

    def test_conteudo_com_sessao_expoe_proxima_revisao_da_sessao(
        self, client, db_session
    ):
        r = client.post("/conteudos", json={"titulo": "A", "materia": "M"})
        cid = r.json()["id"]
        db_session.add(
            models.SessaoRevisao(
                conteudo_id=cid,
                data=date(2026, 7, 1),
                percentual=100,
                proxima_revisao=date(2026, 7, 31),
            )
        )
        db_session.commit()

        r = client.get("/conteudos")
        assert r.json()[0]["proxima_revisao"] == "2026-07-31"

    def test_considera_apenas_a_ultima_sessao_de_cada_conteudo(
        self, client, db_session
    ):
        r = client.post("/conteudos", json={"titulo": "A", "materia": "M"})
        cid = r.json()["id"]
        # Sessão antiga primeiro…
        db_session.add(
            models.SessaoRevisao(
                conteudo_id=cid,
                data=date(2026, 6, 1),
                percentual=50,
                proxima_revisao=date(2026, 6, 2),
            )
        )
        db_session.commit()
        # …depois uma mais nova (id maior = "última" pela regra do backend).
        db_session.add(
            models.SessaoRevisao(
                conteudo_id=cid,
                data=date(2026, 7, 1),
                percentual=100,
                proxima_revisao=date(2026, 7, 31),
            )
        )
        db_session.commit()

        r = client.get("/conteudos")
        assert r.json()[0]["proxima_revisao"] == "2026-07-31"


# ---------------- DELETE /conteudos/{id} ----------------

class TestDeletarConteudo:
    def test_deletar_conteudo_devolve_204(self, client):
        r = client.post("/conteudos", json={"titulo": "A", "materia": "M"})
        cid = r.json()["id"]

        r = client.delete(f"/conteudos/{cid}")
        assert r.status_code == 204
        # E some da listagem
        assert client.get("/conteudos").json() == []

    def test_deletar_conteudo_inexistente_devolve_404(self, client):
        r = client.delete("/conteudos/9999")
        assert r.status_code == 404

    def test_deletar_conteudo_de_outro_usuario_devolve_404(self, client, db_session):
        outro = models.Usuario(
            id=2, supabase_uid="outro-uid", email="outro@local", senha_hash=None
        )
        db_session.add(outro)
        db_session.commit()
        alheio = models.Conteudo(usuario_id=2, titulo="alheio", materia="X")
        db_session.add(alheio)
        db_session.commit()
        db_session.refresh(alheio)

        r = client.delete(f"/conteudos/{alheio.id}")
        assert r.status_code == 404
        # E o conteudo do outro segue intacto no banco
        assert (
            db_session.query(models.Conteudo).filter_by(id=alheio.id).count() == 1
        )

    def test_deletar_conteudo_apaga_sessoes_vinculadas_em_cascata(
        self, client, db_session
    ):
        r = client.post("/conteudos", json={"titulo": "A", "materia": "M"})
        cid = r.json()["id"]
        db_session.add(
            models.SessaoRevisao(
                conteudo_id=cid,
                data=date(2026, 7, 1),
                percentual=80,
                proxima_revisao=date(2026, 7, 8),
            )
        )
        db_session.commit()
        assert (
            db_session.query(models.SessaoRevisao)
            .filter_by(conteudo_id=cid)
            .count()
            == 1
        )

        r = client.delete(f"/conteudos/{cid}")
        assert r.status_code == 204
        db_session.expire_all()
        assert (
            db_session.query(models.SessaoRevisao)
            .filter_by(conteudo_id=cid)
            .count()
            == 0
        )

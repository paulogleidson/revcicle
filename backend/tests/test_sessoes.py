from datetime import date, timedelta

from app import models


def _criar_conteudo(client, titulo="Cálculo I", materia="Matemática") -> int:
    r = client.post("/conteudos", json={"titulo": titulo, "materia": materia})
    assert r.status_code == 201, r.text
    return r.json()["id"]


class TestRegistrarSessao:
    def test_100_porcento_agenda_proxima_revisao_em_30_dias(self, client):
        conteudo_id = _criar_conteudo(client)
        hoje = date(2026, 7, 23)

        r = client.post(
            "/sessoes",
            json={"conteudo_id": conteudo_id, "percentual": 100, "data": hoje.isoformat()},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["conteudo_id"] == conteudo_id
        assert body["percentual"] == 100
        assert body["data"] == "2026-07-23"
        assert body["proxima_revisao"] == "2026-08-22"

    def test_70_porcento_agenda_proxima_revisao_em_7_dias(self, client):
        conteudo_id = _criar_conteudo(client)
        r = client.post(
            "/sessoes",
            json={"conteudo_id": conteudo_id, "percentual": 70, "data": "2026-07-23"},
        )
        assert r.status_code == 201
        assert r.json()["proxima_revisao"] == "2026-07-30"

    def test_50_porcento_agenda_proxima_revisao_em_1_dia(self, client):
        conteudo_id = _criar_conteudo(client)
        r = client.post(
            "/sessoes",
            json={"conteudo_id": conteudo_id, "percentual": 50, "data": "2026-07-23"},
        )
        assert r.status_code == 201
        assert r.json()["proxima_revisao"] == "2026-07-24"

    def test_conteudo_inexistente_devolve_404(self, client):
        r = client.post(
            "/sessoes",
            json={"conteudo_id": 9999, "percentual": 100, "data": "2026-07-23"},
        )
        assert r.status_code == 404

    def test_conteudo_de_outro_usuario_devolve_404(self, client, db_session):
        # Cria um segundo usuário + um conteudo pra ele, direto no DB
        outro = models.Usuario(id=2, email="outro@local", senha_hash="x")
        db_session.add(outro)
        db_session.commit()
        conteudo_alheio = models.Conteudo(
            usuario_id=2, titulo="secret", materia="secret"
        )
        db_session.add(conteudo_alheio)
        db_session.commit()

        r = client.post(
            "/sessoes",
            json={
                "conteudo_id": conteudo_alheio.id,
                "percentual": 100,
                "data": "2026-07-23",
            },
        )
        assert r.status_code == 404
        # E não gravou nada
        assert db_session.query(models.SessaoRevisao).count() == 0

    def test_percentual_fora_do_intervalo_devolve_422(self, client):
        conteudo_id = _criar_conteudo(client)
        r = client.post(
            "/sessoes",
            json={"conteudo_id": conteudo_id, "percentual": 150, "data": "2026-07-23"},
        )
        assert r.status_code == 422


class TestRevisoesHoje:
    def _semear_sessao(self, db_session, conteudo_id: int, proxima_revisao: date):
        # Grava sessão diretamente, com proxima_revisao arbitrária, sem depender
        # do cálculo — o objetivo aqui é testar o filtro do endpoint.
        db_session.add(
            models.SessaoRevisao(
                conteudo_id=conteudo_id,
                data=date(2026, 7, 1),
                percentual=80,
                proxima_revisao=proxima_revisao,
            )
        )
        db_session.commit()

    def test_lista_vazia_quando_usuario_nao_tem_conteudos(self, client):
        r = client.get("/revisoes/hoje")
        assert r.status_code == 200
        assert r.json() == []

    def test_conteudo_sem_sessao_aparece_como_pendente_com_proxima_revisao_null(
        self, client
    ):
        _criar_conteudo(client, titulo="Nunca revisado", materia="M")
        r = client.get("/revisoes/hoje")
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 1
        assert body[0]["titulo"] == "Nunca revisado"
        assert body[0]["proxima_revisao"] is None

    def test_lista_apenas_vencidos_e_de_hoje(self, client, db_session):
        hoje = date.today()

        atrasado = _criar_conteudo(client, titulo="Atrasado", materia="M")
        vence_hoje = _criar_conteudo(client, titulo="Hoje", materia="M")
        futuro = _criar_conteudo(client, titulo="Futuro", materia="M")

        self._semear_sessao(db_session, atrasado, hoje - timedelta(days=3))
        self._semear_sessao(db_session, vence_hoje, hoje)
        self._semear_sessao(db_session, futuro, hoje + timedelta(days=5))

        r = client.get("/revisoes/hoje")
        assert r.status_code == 200
        body = r.json()
        titulos = [c["titulo"] for c in body]
        # Mais atrasado primeiro (proxima_revisao asc)
        assert titulos == ["Atrasado", "Hoje"]
        # E o campo proxima_revisao vem preenchido pros que têm sessão
        assert body[0]["proxima_revisao"] == (hoje - timedelta(days=3)).isoformat()
        assert body[1]["proxima_revisao"] == hoje.isoformat()

    def test_ordena_atrasados_primeiro_e_novos_por_ultimo(self, client, db_session):
        hoje = date.today()

        atrasado = _criar_conteudo(client, titulo="Atrasado", materia="M")
        _criar_conteudo(client, titulo="Novo A", materia="M")
        vence_hoje = _criar_conteudo(client, titulo="Hoje", materia="M")
        _criar_conteudo(client, titulo="Novo B", materia="M")

        self._semear_sessao(db_session, atrasado, hoje - timedelta(days=2))
        self._semear_sessao(db_session, vence_hoje, hoje)

        r = client.get("/revisoes/hoje")
        titulos = [c["titulo"] for c in r.json()]
        # Atrasado → hoje → novos (nulls last).
        # Ordem entre os "novos" não é garantida; verifico só o particionamento.
        assert titulos[:2] == ["Atrasado", "Hoje"]
        assert set(titulos[2:]) == {"Novo A", "Novo B"}

    def test_considera_apenas_a_ultima_sessao_de_cada_conteudo(self, client, db_session):
        hoje = date.today()
        conteudo_id = _criar_conteudo(client, titulo="A", materia="M")

        # Sessão antiga que agendava pra ontem (vencida)…
        self._semear_sessao(db_session, conteudo_id, hoje - timedelta(days=1))
        # …mas uma sessão nova reagendou pro futuro.
        self._semear_sessao(db_session, conteudo_id, hoje + timedelta(days=10))

        r = client.get("/revisoes/hoje")
        assert r.json() == []

    def test_nao_lista_conteudos_de_outro_usuario(self, client, db_session):
        hoje = date.today()

        outro = models.Usuario(id=2, email="outro@local", senha_hash="x")
        db_session.add(outro)
        db_session.commit()
        conteudo_alheio = models.Conteudo(usuario_id=2, titulo="alheio", materia="M")
        db_session.add(conteudo_alheio)
        db_session.commit()
        self._semear_sessao(db_session, conteudo_alheio.id, hoje - timedelta(days=1))

        # E um do usuário mock, também vencido — pra provar que o filtro
        # de usuario_id não é acidentalmente vazio
        meu = _criar_conteudo(client, titulo="meu", materia="M")
        self._semear_sessao(db_session, meu, hoje - timedelta(days=1))

        r = client.get("/revisoes/hoje")
        titulos = [c["titulo"] for c in r.json()]
        assert titulos == ["meu"]

    def test_registrar_sessao_com_proxima_revisao_futura_some_do_hoje(self, client):
        # Integração end-to-end: registra via POST /sessoes e verifica GET.
        conteudo_id = _criar_conteudo(client, titulo="Integração", materia="M")
        r = client.post(
            "/sessoes",
            json={
                "conteudo_id": conteudo_id,
                "percentual": 100,
                "data": date.today().isoformat(),
            },
        )
        assert r.status_code == 201
        # 100% agenda +30 dias → não aparece hoje
        r = client.get("/revisoes/hoje")
        assert r.json() == []

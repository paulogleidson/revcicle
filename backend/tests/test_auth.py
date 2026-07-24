"""Testes da validação real do JWT do Supabase (ES256 + JWKS).

O `conftest` sobrescreve `get_current_user_id` globalmente pros outros
testes. Aqui a gente REMOVE esse override e ainda monkeypatcha
`app.auth._get_signing_key` pra devolver uma chave pública gerada no
próprio teste — evita HTTP contra o JWKS real.
"""
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app import auth, models
from app.auth import get_current_user_id
from app.main import app

# Par ES256 (P-256) fixo pro módulo — reutilizado por todos os testes.
_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
_PUBLIC_KEY = _PRIVATE_KEY.public_key()
_KID = "test-kid-1"


def _emitir_jwt(
    sub: str,
    email: str | None = None,
    expirado: bool = False,
    audience: str = "authenticated",
    private_key=_PRIVATE_KEY,
    kid: str = _KID,
) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": sub,
        "aud": audience,
        "iat": int(now.timestamp()),
        "exp": int(
            (now - timedelta(minutes=5) if expirado else now + timedelta(hours=1)).timestamp()
        ),
    }
    if email is not None:
        payload["email"] = email
    return pyjwt.encode(payload, private_key, algorithm="ES256", headers={"kid": kid})


@pytest.fixture()
def sem_override(db_session):
    """Remove o dependency_override que o conftest instala — mais nada."""
    app.dependency_overrides.pop(get_current_user_id, None)
    try:
        yield TestClient(app), db_session
    finally:
        from tests.conftest import _override_current_user_id
        app.dependency_overrides[get_current_user_id] = _override_current_user_id


@pytest.fixture()
def real_auth_client(sem_override, monkeypatch):
    """Client exercitando a auth de verdade; JWKS mockado pela chave pública local."""
    monkeypatch.setattr(auth, "_get_signing_key", lambda token: _PUBLIC_KEY)
    yield sem_override


def test_sem_header_authorization_devolve_401(real_auth_client):
    client, _ = real_auth_client
    r = client.get("/conteudos")
    assert r.status_code == 401
    assert "authorization" in r.json()["detail"].lower()


def test_scheme_diferente_de_bearer_devolve_401(real_auth_client):
    client, _ = real_auth_client
    r = client.get("/conteudos", headers={"Authorization": "Basic xyz"})
    assert r.status_code == 401


def test_token_com_assinatura_invalida_devolve_401(real_auth_client):
    client, _ = real_auth_client
    # Assina com OUTRA chave privada — mas a validação usa a nossa pública.
    outra_priv = ec.generate_private_key(ec.SECP256R1())
    token = _emitir_jwt(sub="abc", private_key=outra_priv)
    r = client.get("/conteudos", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_expirado_devolve_401(real_auth_client):
    client, _ = real_auth_client
    token = _emitir_jwt(sub="usuario-x", expirado=True)
    r = client.get("/conteudos", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_com_aud_errada_devolve_401(real_auth_client):
    client, _ = real_auth_client
    token = _emitir_jwt(sub="usuario-x", audience="outra-audience")
    r = client.get("/conteudos", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_jwks_nao_encontra_chave_devolve_401(sem_override, monkeypatch):
    """Simula kid desconhecido / JWKS inalcançável."""
    from jwt import PyJWKClientError

    client, _ = sem_override

    def _raise(_token):
        raise PyJWKClientError("kid não encontrado no JWKS")

    monkeypatch.setattr(auth, "_get_signing_key", _raise)

    token = _emitir_jwt(sub="qualquer")  # bem-formado, mas key resolution vai falhar
    r = client.get("/conteudos", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert "chave" in r.json()["detail"].lower()


def test_token_valido_para_uid_novo_provisiona_usuario(real_auth_client):
    client, db = real_auth_client

    antes = db.query(models.Usuario).count()
    token = _emitir_jwt(sub="uuid-novo-123", email="novo@teste.com")

    r = client.get("/conteudos", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []

    db.expire_all()
    novo = db.query(models.Usuario).filter_by(supabase_uid="uuid-novo-123").one()
    assert novo.email == "novo@teste.com"
    assert novo.senha_hash is None
    assert db.query(models.Usuario).count() == antes + 1


def test_token_valido_reutiliza_usuario_existente(real_auth_client):
    client, db = real_auth_client

    ja_existe = models.Usuario(
        supabase_uid="uuid-existente",
        email="antigo@teste.com",
        senha_hash=None,
    )
    db.add(ja_existe)
    db.commit()
    db.refresh(ja_existe)
    id_esperado = ja_existe.id

    token = _emitir_jwt(sub="uuid-existente", email="antigo@teste.com")

    r = client.post(
        "/conteudos",
        json={"titulo": "T", "materia": "M"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["usuario_id"] == id_esperado

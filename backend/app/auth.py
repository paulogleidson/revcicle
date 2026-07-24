"""Autenticação via Supabase (JWT ES256 + JWKS).

O projeto Supabase migrou pra JWT signing keys assimétricas (ECC P-256).
O frontend loga com Supabase Auth e manda o `access_token` como
`Authorization: Bearer <jwt>`. O backend:

  1. Lê o `kid` do header do JWT.
  2. Baixa a chave pública correspondente do endpoint JWKS do projeto
     (`SUPABASE_JWKS_URL`) — `PyJWKClient` cuida do cache.
  3. Valida assinatura ES256 + `aud=authenticated` + `exp`.
  4. Extrai o `sub` (UUID do usuário no Supabase) e mapeia pra linha
     local em `usuarios` via `supabase_uid` (get-or-create).

O contrato externo é o mesmo do mock anterior: uma dependency
`get_current_user_id` que devolve `int` (o `usuarios.id` local). Os
routers não precisam mudar.
"""
import os
from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError, decode as jwt_decode
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    url = os.getenv("SUPABASE_JWKS_URL")
    if not url:
        # RuntimeError vira 500 no handler abaixo — má config do servidor.
        raise RuntimeError("SUPABASE_JWKS_URL não configurado")
    # cache_jwk_set=True mantém as chaves em memória; lifespan controla TTL.
    return PyJWKClient(url, cache_jwk_set=True, lifespan=3600)


def _get_signing_key(token: str):
    """Resolve a chave pública ES256 desse token via JWKS.

    Isolado numa função pequena pra testes conseguirem monkeypatchar
    sem subir HTTP nem gerar JWKS falsos.
    """
    return _jwks_client().get_signing_key_from_jwt(token).key


def _extrair_bearer(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="header Authorization ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization precisa ser 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token.strip()


def _decodificar_jwt(token: str) -> dict:
    try:
        signing_key = _get_signing_key(token)
    except RuntimeError as e:
        # SUPABASE_JWKS_URL ausente → má config, não é culpa do cliente.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except (PyJWKClientError, InvalidTokenError) as e:
        # Falha ao resolver a chave (kid desconhecido, JWKS inalcançável,
        # header sem kid) — trata como token inválido.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"não foi possível resolver chave do token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return jwt_decode(
            token,
            signing_key,
            algorithms=["ES256"],
            audience="authenticated",  # aud padrão do Supabase Auth
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"token inválido: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _obter_ou_criar_usuario(db: Session, supabase_uid: str, email: str | None) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.supabase_uid == supabase_uid).first()
    if usuario is not None:
        return usuario

    # Primeira request desse usuário — provisiona linha local.
    # Se o JWT não trouxer email (fluxos phone/anon), gera um placeholder
    # pra não violar o NOT NULL / UNIQUE.
    usuario = Usuario(
        supabase_uid=supabase_uid,
        email=email or f"{supabase_uid}@supabase.local",
        senha_hash=None,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def get_current_user_id(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> int:
    token = _extrair_bearer(authorization)
    payload = _decodificar_jwt(token)

    supabase_uid = payload.get("sub")
    if not supabase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token sem claim 'sub'",
        )

    usuario = _obter_ou_criar_usuario(db, supabase_uid, payload.get("email"))
    return usuario.id

"""Fixtures compartilhadas pros testes.

- SQLite in-memory com `StaticPool` (compartilha a mesma conexão entre
  TestClient e sessões de teste).
- Cria/dropa tabelas por teste, semeia o usuário de teste.
- Substitui `get_current_user_id` por um override que devolve o id do
  usuário semeado — dessa forma os testes não precisam emitir JWT
  válido pro Supabase.
"""
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database as db_mod

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)

# Swap antes de importar app.main / routers.
db_mod.engine = _test_engine
db_mod.SessionLocal = _TestSession

from app import models  # noqa: E402
from app.auth import get_current_user_id  # noqa: E402
from app.database import Base  # noqa: E402
from app.main import app  # noqa: E402

TEST_USER_ID = 1


def _override_current_user_id() -> int:
    return TEST_USER_ID


app.dependency_overrides[get_current_user_id] = _override_current_user_id


@pytest.fixture()
def mock_user_id() -> int:
    return TEST_USER_ID


@pytest.fixture()
def db_session():
    """Cria schema, semeia o usuário de teste, devolve a session, dropa tudo no fim."""
    Base.metadata.create_all(_test_engine)
    session = _TestSession()
    session.add(
        models.Usuario(
            id=TEST_USER_ID,
            supabase_uid="test-uid",
            email="dev@local",
            senha_hash=None,
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(_test_engine)


@pytest.fixture()
def client(db_session):
    """TestClient contra a app real; depende de `db_session` pra ter tabelas + seed."""
    return TestClient(app)

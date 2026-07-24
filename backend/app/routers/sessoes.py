from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Conteudo, SessaoRevisao
from app.schemas import ConteudoRevisaoOut, SessaoRevisaoCreate, SessaoRevisaoOut
from app.services.revisao import calcular_proxima_revisao

router = APIRouter(tags=["revisoes"])


@router.post("/sessoes", response_model=SessaoRevisaoOut, status_code=status.HTTP_201_CREATED)
def registrar_sessao(
    payload: SessaoRevisaoCreate,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> SessaoRevisao:
    # Valida que o conteudo pertence ao usuário — 404 (não 403) pra não
    # vazar existência de conteudos alheios.
    conteudo = (
        db.query(Conteudo)
        .filter(Conteudo.id == payload.conteudo_id, Conteudo.usuario_id == usuario_id)
        .first()
    )
    if conteudo is None:
        raise HTTPException(status_code=404, detail="conteudo não encontrado")

    proxima = calcular_proxima_revisao(payload.percentual, payload.data)
    sessao = SessaoRevisao(
        conteudo_id=payload.conteudo_id,
        data=payload.data,
        percentual=payload.percentual,
        proxima_revisao=proxima,
    )
    db.add(sessao)
    db.commit()
    db.refresh(sessao)
    return sessao


@router.get("/revisoes/hoje", response_model=list[ConteudoRevisaoOut])
def listar_revisoes_de_hoje(
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> list[ConteudoRevisaoOut]:
    """Conteúdos que o usuário precisa revisar hoje.

    Entram na lista:
      - conteúdos SEM nenhuma sessão registrada (nunca revisados) —
        `proxima_revisao` volta como `null`;
      - conteúdos cuja ÚLTIMA sessão tem `proxima_revisao <= hoje`
        (atrasados ou vencendo hoje).

    "Última sessão" = maior `id` por `conteudo_id` (id é monotônico).
    Ordenação: atrasados primeiro (`proxima_revisao asc`), nunca-revisados
    por último.
    """
    hoje = date.today()

    ultima_sessao_ids = (
        select(func.max(SessaoRevisao.id))
        .group_by(SessaoRevisao.conteudo_id)
    )

    rows = (
        db.query(Conteudo, SessaoRevisao)
        .outerjoin(
            SessaoRevisao,
            (SessaoRevisao.conteudo_id == Conteudo.id)
            & (SessaoRevisao.id.in_(ultima_sessao_ids)),
        )
        .filter(Conteudo.usuario_id == usuario_id)
        .filter(
            or_(
                SessaoRevisao.id.is_(None),
                SessaoRevisao.proxima_revisao <= hoje,
            )
        )
        # Nulls last é dialect-sensitive; `is_(None)` como chave primária
        # dá ordenação portátil (Falses antes de Trues) em SQLite e Postgres.
        .order_by(
            SessaoRevisao.proxima_revisao.is_(None),
            SessaoRevisao.proxima_revisao.asc(),
        )
        .all()
    )

    return [
        ConteudoRevisaoOut(
            id=c.id,
            usuario_id=c.usuario_id,
            titulo=c.titulo,
            materia=c.materia,
            criado_em=c.criado_em,
            proxima_revisao=(s.proxima_revisao if s is not None else None),
        )
        for c, s in rows
    ]

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Conteudo, SessaoRevisao
from app.schemas import ConteudoCreate, ConteudoOut, ConteudoRevisaoOut

router = APIRouter(prefix="/conteudos", tags=["conteudos"])


@router.post("", response_model=ConteudoOut, status_code=status.HTTP_201_CREATED)
def criar_conteudo(
    payload: ConteudoCreate,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> Conteudo:
    conteudo = Conteudo(
        usuario_id=usuario_id,
        titulo=payload.titulo,
        materia=payload.materia,
    )
    db.add(conteudo)
    db.commit()
    db.refresh(conteudo)
    return conteudo


@router.get("", response_model=list[ConteudoRevisaoOut])
def listar_conteudos(
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> list[ConteudoRevisaoOut]:
    """Lista todos os conteúdos do usuário, com a `proxima_revisao` da
    última sessão (ou `None` se nunca revisado). Mesmo padrão de LEFT
    JOIN usado em `/revisoes/hoje` — só sem o filtro por data.
    """
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
        .order_by(Conteudo.criado_em.desc(), Conteudo.id.desc())
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


@router.delete("/{conteudo_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_conteudo(
    conteudo_id: int,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> Response:
    # 404 tanto pra inexistente quanto pra alheio — não vazar existência.
    conteudo = (
        db.query(Conteudo)
        .filter(Conteudo.id == conteudo_id, Conteudo.usuario_id == usuario_id)
        .first()
    )
    if conteudo is None:
        raise HTTPException(status_code=404, detail="conteudo não encontrado")

    # Cascade via ORM (`cascade="all, delete-orphan"` no relationship de
    # `Conteudo.sessoes`) — as sessoes_revisao vinculadas somem junto.
    db.delete(conteudo)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

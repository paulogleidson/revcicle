from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Conteudo, SessaoRevisao
from app.schemas import MetricasOut
from app.services.metricas import SessaoComConteudo, agregar_metricas

router = APIRouter(tags=["metricas"])


@router.get("/metricas", response_model=MetricasOut)
def obter_metricas(
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> dict:
    rows = (
        db.query(SessaoRevisao, Conteudo)
        .join(Conteudo, SessaoRevisao.conteudo_id == Conteudo.id)
        .filter(Conteudo.usuario_id == usuario_id)
        .all()
    )
    sessoes = [
        SessaoComConteudo(
            sessao_id=s.id,
            conteudo_id=c.id,
            titulo=c.titulo,
            materia=c.materia,
            data=s.data,
            percentual=s.percentual,
            proxima_revisao=s.proxima_revisao,
        )
        for s, c in rows
    ]
    return agregar_metricas(sessoes)

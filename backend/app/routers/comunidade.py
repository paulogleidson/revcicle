from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Comentario, Conteudo, Perfil, Post
from app.schemas import (
    AutorOut,
    ComentarioIn,
    ComentarioOut,
    PerfilIn,
    PerfilOut,
    PerfilPublicoOut,
    PostDetalheOut,
    PostIn,
    PostOut,
)
from app.services.comunidade import disciplinas_em_comum

router = APIRouter(prefix="/comunidade", tags=["comunidade"])


def _exigir_perfil(db: Session, usuario_id: int) -> Perfil:
    perfil = db.get(Perfil, usuario_id)
    if perfil is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="crie seu perfil na comunidade antes de participar",
        )
    return perfil


def _total_comentarios_subq():
    return (
        select(Comentario.post_id, func.count(Comentario.id).label("total"))
        .group_by(Comentario.post_id)
        .subquery()
    )


def _post_out(post: Post, apelido: str, total: int | None, usuario_id: int) -> PostOut:
    return PostOut(
        id=post.id,
        autor=AutorOut(usuario_id=post.usuario_id, apelido=apelido),
        texto=post.texto,
        criado_em=post.criado_em,
        total_comentarios=total or 0,
        meu=post.usuario_id == usuario_id,
    )


def _comentario_out(c: Comentario, apelido: str, usuario_id: int) -> ComentarioOut:
    return ComentarioOut(
        id=c.id,
        post_id=c.post_id,
        autor=AutorOut(usuario_id=c.usuario_id, apelido=apelido),
        texto=c.texto,
        criado_em=c.criado_em,
        meu=c.usuario_id == usuario_id,
    )


# --- Perfil -----------------------------------------------------------------


@router.get("/perfil", response_model=PerfilOut)
def obter_meu_perfil(
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> Perfil:
    perfil = db.get(Perfil, usuario_id)
    if perfil is None:
        raise HTTPException(status_code=404, detail="perfil não criado")
    return perfil


@router.put("/perfil", response_model=PerfilOut)
def salvar_meu_perfil(
    payload: PerfilIn,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> Perfil:
    """Cria ou renomeia o perfil. Apelido é único sem diferenciar maiúsculas."""
    em_uso = (
        db.query(Perfil)
        .filter(func.lower(Perfil.apelido) == payload.apelido.lower(), Perfil.usuario_id != usuario_id)
        .first()
    )
    if em_uso is not None:
        raise HTTPException(status_code=409, detail="apelido já está em uso")

    perfil = db.get(Perfil, usuario_id)
    if perfil is None:
        perfil = Perfil(usuario_id=usuario_id, apelido=payload.apelido)
        db.add(perfil)
    else:
        perfil.apelido = payload.apelido
    try:
        db.commit()
    except IntegrityError:
        # Corrida entre duas requisições com o mesmo apelido.
        db.rollback()
        raise HTTPException(status_code=409, detail="apelido já está em uso")
    db.refresh(perfil)
    return perfil


@router.get("/usuarios/{outro_id}", response_model=PerfilPublicoOut)
def ver_perfil(
    outro_id: int,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> PerfilPublicoOut:
    perfil = db.get(Perfil, outro_id)
    if perfil is None:
        raise HTTPException(status_code=404, detail="perfil não encontrado")

    def materias(uid: int) -> list[str]:
        return list(db.scalars(select(Conteudo.materia).where(Conteudo.usuario_id == uid)))

    total_posts = db.scalar(select(func.count(Post.id)).where(Post.usuario_id == outro_id))
    return PerfilPublicoOut(
        usuario_id=perfil.usuario_id,
        apelido=perfil.apelido,
        membro_desde=perfil.criado_em,
        total_posts=total_posts or 0,
        disciplinas_em_comum=disciplinas_em_comum(materias(usuario_id), materias(outro_id)),
    )


# --- Posts ------------------------------------------------------------------


@router.get("/posts", response_model=list[PostOut])
def listar_posts(
    antes_de: int | None = Query(default=None, description="Paginação: só posts com id menor"),
    limite: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> list[PostOut]:
    """Feed público, mais recentes primeiro."""
    totais = _total_comentarios_subq()
    query = (
        db.query(Post, Perfil.apelido, totais.c.total)
        .join(Perfil, Perfil.usuario_id == Post.usuario_id)
        .outerjoin(totais, totais.c.post_id == Post.id)
    )
    if antes_de is not None:
        query = query.filter(Post.id < antes_de)
    rows = query.order_by(Post.id.desc()).limit(limite).all()
    return [_post_out(p, apelido, total, usuario_id) for p, apelido, total in rows]


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def criar_post(
    payload: PostIn,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> PostOut:
    perfil = _exigir_perfil(db, usuario_id)
    post = Post(usuario_id=usuario_id, texto=payload.texto)
    db.add(post)
    db.commit()
    db.refresh(post)
    return _post_out(post, perfil.apelido, 0, usuario_id)


@router.get("/posts/{post_id}", response_model=PostDetalheOut)
def detalhar_post(
    post_id: int,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> PostDetalheOut:
    row = (
        db.query(Post, Perfil.apelido)
        .join(Perfil, Perfil.usuario_id == Post.usuario_id)
        .filter(Post.id == post_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="post não encontrado")
    post, apelido = row

    comentarios = (
        db.query(Comentario, Perfil.apelido)
        .join(Perfil, Perfil.usuario_id == Comentario.usuario_id)
        .filter(Comentario.post_id == post_id)
        .order_by(Comentario.id)
        .all()
    )
    base = _post_out(post, apelido, len(comentarios), usuario_id)
    return PostDetalheOut(
        **base.model_dump(),
        comentarios=[_comentario_out(c, a, usuario_id) for c, a in comentarios],
    )


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_post(
    post_id: int,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> Response:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post não encontrado")
    # Post é público, então 403 (e não 404) para o de outra pessoa.
    if post.usuario_id != usuario_id:
        raise HTTPException(status_code=403, detail="só o autor pode apagar o post")
    # Comentários vão junto pelo cascade do relationship `Post.comentarios`.
    db.delete(post)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Comentários ------------------------------------------------------------


@router.post(
    "/posts/{post_id}/comentarios",
    response_model=ComentarioOut,
    status_code=status.HTTP_201_CREATED,
)
def comentar(
    post_id: int,
    payload: ComentarioIn,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> ComentarioOut:
    perfil = _exigir_perfil(db, usuario_id)
    if db.get(Post, post_id) is None:
        raise HTTPException(status_code=404, detail="post não encontrado")
    comentario = Comentario(post_id=post_id, usuario_id=usuario_id, texto=payload.texto)
    db.add(comentario)
    db.commit()
    db.refresh(comentario)
    return _comentario_out(comentario, perfil.apelido, usuario_id)


@router.delete("/comentarios/{comentario_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_comentario(
    comentario_id: int,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
) -> Response:
    comentario = db.get(Comentario, comentario_id)
    if comentario is None:
        raise HTTPException(status_code=404, detail="comentário não encontrado")
    if comentario.usuario_id != usuario_id:
        raise HTTPException(status_code=403, detail="só o autor pode apagar o comentário")
    db.delete(comentario)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

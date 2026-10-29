from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


class UsuarioBase(BaseModel):
    email: str


class UsuarioCreate(UsuarioBase):
    senha: str


class UsuarioOut(UsuarioBase):
    id: int
    criado_em: datetime

    class Config:
        from_attributes = True


class ConteudoBase(BaseModel):
    titulo: str
    materia: str


class ConteudoCreate(ConteudoBase):
    pass


class ConteudoOut(ConteudoBase):
    id: int
    usuario_id: int
    criado_em: datetime

    class Config:
        from_attributes = True


class ConteudoRevisaoOut(ConteudoOut):
    """Conteúdo pendente de revisão no Dashboard.

    `proxima_revisao` é `None` quando o conteúdo ainda não teve nenhuma
    sessão registrada (nunca revisado — entra como pendente por padrão).
    """
    proxima_revisao: date | None = None


class SessaoRevisaoBase(BaseModel):
    data: date
    percentual: float = Field(ge=0, le=100)


class SessaoRevisaoCreate(SessaoRevisaoBase):
    conteudo_id: int


class SessaoRevisaoOut(SessaoRevisaoBase):
    id: int
    conteudo_id: int
    proxima_revisao: date

    class Config:
        from_attributes = True


class PontoEvolucaoOut(BaseModel):
    data: date
    percentual: float


class EvolucaoConteudoOut(BaseModel):
    conteudo_id: int
    titulo: str
    materia: str
    pontos: list[PontoEvolucaoOut]


class MateriaMetricaOut(BaseModel):
    materia: str
    media_percentual: float
    total_revisoes: int


class ItemCalendarioOut(BaseModel):
    conteudo_id: int
    titulo: str
    # Preenchido só em revisões realizadas; agendadas ainda não têm resultado.
    percentual: float | None = None


class DiaCalendarioOut(BaseModel):
    data: date
    realizadas: list[ItemCalendarioOut]
    agendadas: list[ItemCalendarioOut]


class MetricasOut(BaseModel):
    evolucao: list[EvolucaoConteudoOut]
    por_materia: list[MateriaMetricaOut]
    calendario: list[DiaCalendarioOut]


# --- Comunidade v1 ---------------------------------------------------------

# Letras (com acento), números, espaço, ponto, hífen e underline.
Apelido = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=30, pattern=r"^[\w .-]+$")
]
TextoPost = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
TextoComentario = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class PerfilIn(BaseModel):
    apelido: Apelido


class PerfilOut(BaseModel):
    usuario_id: int
    apelido: str
    criado_em: datetime

    class Config:
        from_attributes = True


class PerfilPublicoOut(BaseModel):
    usuario_id: int
    apelido: str
    membro_desde: datetime
    total_posts: int
    # Matérias que o usuário logado e este perfil têm em comum nos conteúdos.
    disciplinas_em_comum: list[str]


class AutorOut(BaseModel):
    usuario_id: int
    apelido: str


class PostIn(BaseModel):
    texto: TextoPost


class PostOut(BaseModel):
    id: int
    autor: AutorOut
    texto: str
    criado_em: datetime
    total_comentarios: int
    # True quando o post é do usuário logado (front mostra "apagar").
    meu: bool


class ComentarioIn(BaseModel):
    texto: TextoComentario


class ComentarioOut(BaseModel):
    id: int
    post_id: int
    autor: AutorOut
    texto: str
    criado_em: datetime
    meu: bool


class PostDetalheOut(PostOut):
    comentarios: list[ComentarioOut]

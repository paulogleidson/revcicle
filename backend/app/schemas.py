from datetime import date, datetime

from pydantic import BaseModel, Field


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

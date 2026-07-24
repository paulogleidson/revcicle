from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # UUID que o Supabase Auth emite no claim `sub` do JWT. Serve pra
    # mapear "usuário autenticado no Supabase" → linha local em `usuarios`.
    supabase_uid: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    # Vestigial: com Supabase Auth, senhas são gerenciadas pelo Supabase e a
    # coluna fica NULL. Mantida pra não quebrar seeds/rows antigas.
    senha_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    conteudos: Mapped[list["Conteudo"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


class Conteudo(Base):
    __tablename__ = "conteudos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    materia: Mapped[str] = mapped_column(String, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="conteudos")
    sessoes: Mapped[list["SessaoRevisao"]] = relationship(
        back_populates="conteudo", cascade="all, delete-orphan"
    )


class SessaoRevisao(Base):
    __tablename__ = "sessoes_revisao"
    __table_args__ = (
        CheckConstraint("percentual >= 0 AND percentual <= 100", name="ck_percentual_0_100"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conteudo_id: Mapped[int] = mapped_column(
        ForeignKey("conteudos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    percentual: Mapped[float] = mapped_column(Float, nullable=False)
    proxima_revisao: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    conteudo: Mapped["Conteudo"] = relationship(back_populates="sessoes")

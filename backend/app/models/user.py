"""
Modelos: users, user_role, user_permissions, sessions, password_resets.
Ref: docs/source/02_modelo_de_datos.md secciones 2.2.7-2.2.11
Ref: docs/source/01_glosario_y_enums.md secciones 1.2.4
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    Enum,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utcnow


# --- Enums (doc 01, seccion 1.2.4) ---

class EstadoUser(str, enum.Enum):
    ACTIVO = "ACTIVO"
    SUSPENDIDO = "SUSPENDIDO"


class UserRoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    OPERADOR = "OPERADOR"
    GESTOR = "GESTOR"
    MEDICO = "MEDICO"


# --- Users (doc 02, seccion 2.2.7) ---

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # R2: persona_id UNIQUE
    persona_id: Mapped[int] = mapped_column(
        ForeignKey("personas.persona_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # R3: user_email UNIQUE
    user_email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # R7: estado
    estado: Mapped[str] = mapped_column(
        Enum(EstadoUser, native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoUser.ACTIVO.value,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        default=utcnow, onupdate=utcnow
    )

    # Relaciones
    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", lazy="selectin")
    permissions: Mapped[list["UserPermission"]] = relationship(
        back_populates="user", lazy="selectin"
    )


# --- UserRole (doc 02, seccion 2.2.8) ---

class UserRole(Base):
    __tablename__ = "user_role"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        primary_key=True,
    )
    user_role: Mapped[str] = mapped_column(
        Enum(UserRoleEnum, native_enum=True, values_callable=lambda e: [x.value for x in e]),
        primary_key=True,
    )

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        default=utcnow, onupdate=utcnow
    )

    # Relaciones
    user: Mapped["User"] = relationship(back_populates="roles")

    __table_args__ = (
        UniqueConstraint("user_id", "user_role", name="uq_user_role"),
    )


# --- UserPermission (doc 02, seccion 2.2.9) ---

class UserPermission(Base):
    __tablename__ = "user_permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    permission_code: Mapped[str] = mapped_column(String(100), nullable=False)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        default=utcnow, onupdate=utcnow
    )

    # Relaciones
    user: Mapped["User"] = relationship(back_populates="permissions")

    # R15
    __table_args__ = (
        UniqueConstraint("user_id", "permission_code", name="uq_user_permission"),
    )


# --- Sessions (doc 02, seccion 2.2.10) ---

class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: uuid.uuid4().hex
    )

    # R12
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(nullable=True)


# --- PasswordReset (doc 02, seccion 2.2.11) ---

class PasswordReset(Base):
    __tablename__ = "password_resets"

    reset_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

"""
Modelos: clientes, cliente_apoderado.
Ref: docs/source/02_modelo_de_datos.md secciones 2.2.2-2.2.3
Ref: docs/source/01_glosario_y_enums.md secciones 1.2.2
"""

import enum
from datetime import datetime

from sqlalchemy import String, Text, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utcnow


# --- Enums ---

class EstadoCliente(str, enum.Enum):
    ACTIVO = "ACTIVO"
    SUSPENDIDO = "SUSPENDIDO"


class EstadoApoderado(str, enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


# --- Clientes (doc 02, seccion 2.2.2) ---

class Cliente(Base):
    __tablename__ = "clientes"

    # PK y FK -> personas.persona_id
    persona_id: Mapped[int] = mapped_column(
        ForeignKey("personas.persona_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        primary_key=True,
    )
    estado: Mapped[str] = mapped_column(
        Enum(EstadoCliente, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoCliente.ACTIVO.value,
    )
    promotor_id: Mapped[int | None] = mapped_column(
        ForeignKey("promotores.promotor_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=utcnow, onupdate=utcnow)

    # Relaciones
    persona: Mapped["Persona"] = relationship(lazy="selectin")  # noqa: F821


# --- ClienteApoderado (doc 02, seccion 2.2.3) ---

class ClienteApoderado(Base):
    __tablename__ = "cliente_apoderado"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.persona_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    apoderado_id: Mapped[int] = mapped_column(
        ForeignKey("personas.persona_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        Enum(EstadoApoderado, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoApoderado.ACTIVO.value,
    )

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=utcnow, onupdate=utcnow)

    # R17: UNIQUE(cliente_id, apoderado_id)
    __table_args__ = (
        UniqueConstraint("cliente_id", "apoderado_id", name="uq_cliente_apoderado"),
    )

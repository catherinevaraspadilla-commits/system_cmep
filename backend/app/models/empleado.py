"""
Modelos: empleado, medico_extra.
Ref: docs/source/02_modelo_de_datos.md secciones 2.2.5-2.2.6
Ref: docs/source/01_glosario_y_enums.md seccion 1.2.4
"""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Enum, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utcnow


# --- Enums ---

class RolEmpleado(str, enum.Enum):
    OPERADOR = "OPERADOR"
    GESTOR = "GESTOR"
    MEDICO = "MEDICO"


class EstadoEmpleado(str, enum.Enum):
    ACTIVO = "ACTIVO"
    SUSPENDIDO = "SUSPENDIDO"
    VACACIONES = "VACACIONES"
    PERMISO = "PERMISO"


# --- Empleado (doc 02, seccion 2.2.5) ---

class Empleado(Base):
    __tablename__ = "empleado"

    empleado_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    persona_id: Mapped[int] = mapped_column(
        ForeignKey("personas.persona_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    rol_empleado: Mapped[str] = mapped_column(
        Enum(RolEmpleado, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    estado_empleado: Mapped[str] = mapped_column(
        Enum(EstadoEmpleado, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoEmpleado.ACTIVO.value,
    )
    tipo_empleado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tarifa_empleado: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=utcnow, onupdate=utcnow)

    # Relaciones
    persona: Mapped["Persona"] = relationship(lazy="selectin")  # noqa: F821

    # UNIQUE(persona_id, rol_empleado)
    __table_args__ = (
        UniqueConstraint("persona_id", "rol_empleado", name="uq_empleado_persona_rol"),
    )


# --- MedicoExtra (doc 02, seccion 2.2.6) ---

class MedicoExtra(Base):
    __tablename__ = "medico_extra"

    # PK y FK -> personas.persona_id
    persona_id: Mapped[int] = mapped_column(
        ForeignKey("personas.persona_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        primary_key=True,
    )
    tipo_medico: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cmp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    especialidad: Mapped[str | None] = mapped_column(String(150), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=utcnow, onupdate=utcnow)

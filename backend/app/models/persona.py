"""
Modelo: personas — entidad base de identidad.
Ref: docs/source/02_modelo_de_datos.md seccion 2.2.1
Ref: docs/source/01_glosario_y_enums.md seccion 1.2.1
"""

import enum
from datetime import datetime

from sqlalchemy import String, Date, Text, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utcnow


class TipoDocumento(str, enum.Enum):
    DNI = "DNI"
    CE = "CE"
    PASAPORTE = "PASAPORTE"
    RUC = "RUC"


class Persona(Base):
    __tablename__ = "personas"

    persona_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    tipo_documento: Mapped[str | None] = mapped_column(
        Enum(TipoDocumento, native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )
    numero_documento: Mapped[str | None] = mapped_column(String(30), nullable=True)
    nombres: Mapped[str] = mapped_column(String(150), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(150), nullable=False)
    fecha_nacimiento: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    celular_1: Mapped[str | None] = mapped_column(String(20), nullable=True)
    celular_2: Mapped[str | None] = mapped_column(String(20), nullable=True)
    telefono_fijo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        default=utcnow, onupdate=utcnow
    )

    # R1: UNIQUE(tipo_documento, numero_documento)
    __table_args__ = (
        UniqueConstraint("tipo_documento", "numero_documento", name="uq_persona_documento"),
    )

"""
Modelo: promotores — fuente/origen del cliente.
Ref: docs/source/02_modelo_de_datos.md seccion 2.2.4
Ref: docs/source/01_glosario_y_enums.md seccion 1.2.3
"""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utcnow


class TipoPromotor(str, enum.Enum):
    PERSONA = "PERSONA"
    EMPRESA = "EMPRESA"
    OTROS = "OTROS"


class Promotor(Base):
    __tablename__ = "promotores"

    promotor_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    tipo_promotor: Mapped[str] = mapped_column(
        Enum(TipoPromotor, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    fuente_promotor: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Solo si tipo_promotor = PERSONA (validar en backend)
    persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("personas.persona_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )
    # Solo si tipo_promotor = EMPRESA
    razon_social: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Solo si tipo_promotor = OTROS
    nombre_promotor_otros: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationship to Persona (for PERSONA type)
    persona: Mapped["Persona"] = relationship(  # noqa: F821
        foreign_keys=[persona_id], lazy="selectin"
    )

    ruc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    celular_1: Mapped[str | None] = mapped_column(String(20), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    tarifa: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=utcnow, onupdate=utcnow)

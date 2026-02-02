"""
Modelo: servicios — catalogo de servicios con tarifa.
Ref: docs/source/02_modelo_de_datos.md seccion 2.2.12
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utcnow


class Servicio(Base):
    __tablename__ = "servicios"

    servicio_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    descripcion_servicio: Mapped[str] = mapped_column(String(255), nullable=False)
    caracteristicas_servicio: Mapped[str | None] = mapped_column(Text, nullable=True)
    tarifa_servicio: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    moneda_tarifa: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=utcnow, onupdate=utcnow)

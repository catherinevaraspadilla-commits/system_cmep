"""
Modelos: solicitud_cmep, solicitud_asignacion, solicitud_estado_historial,
         pago_solicitud, archivos, solicitud_archivo.
Ref: docs/source/01_glosario_y_enums.md secciones 1.2.5-1.2.7
Ref: docs/source/02_modelo_de_datos.md (tablas derivadas de secciones 2.2.12+)
Ref: docs/source/04_acciones_y_reglas_negocio.md (auditoria, pagos, asignaciones)
Ref: docs/source/05_api_y_policy.md (estado_operativo derivado, contratos)
"""

import enum
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    String,
    Text,
    Enum,
    ForeignKey,
    UniqueConstraint,
    Boolean,
    Date,
    Numeric,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utcnow


# ── Enums (doc 01, seccion 1.2.5-1.2.7) ──────────────────────────────

class EstadoPago(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    PAGADO = "PAGADO"
    OBSERVADO = "OBSERVADO"


class EstadoAtencion(str, enum.Enum):
    REGISTRADO = "REGISTRADO"
    EN_PROCESO = "EN_PROCESO"
    ATENDIDO = "ATENDIDO"
    OBSERVADO = "OBSERVADO"
    CANCELADO = "CANCELADO"


class EstadoCertificado(str, enum.Enum):
    APROBADO = "APROBADO"
    OBSERVADO = "OBSERVADO"


class TarifaMoneda(str, enum.Enum):
    PEN = "PEN"
    USD = "USD"


class TarifaFuente(str, enum.Enum):
    SERVICIO = "SERVICIO"
    OVERRIDE = "OVERRIDE"


class RolAsignacion(str, enum.Enum):
    OPERADOR = "OPERADOR"
    GESTOR = "GESTOR"
    MEDICO = "MEDICO"


class TipoArchivo(str, enum.Enum):
    EVIDENCIA_PAGO = "EVIDENCIA_PAGO"
    DOCUMENTO = "DOCUMENTO"
    OTROS = "OTROS"


# ── solicitud_cmep ────────────────────────────────────────────────────

class SolicitudCmep(Base):
    __tablename__ = "solicitud_cmep"

    solicitud_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Codigo unico legible: CMEP-YYYY-NNNN
    codigo: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)

    # FK relaciones principales
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.persona_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    apoderado_id: Mapped[int | None] = mapped_column(
        ForeignKey("personas.persona_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )
    servicio_id: Mapped[int | None] = mapped_column(
        ForeignKey("servicios.servicio_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )
    promotor_id: Mapped[int | None] = mapped_column(
        ForeignKey("promotores.promotor_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )

    # Estados (doc 01, seccion 1.2.5)
    estado_atencion: Mapped[str] = mapped_column(
        Enum(EstadoAtencion, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoAtencion.REGISTRADO.value,
    )
    estado_pago: Mapped[str] = mapped_column(
        Enum(EstadoPago, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoPago.PENDIENTE.value,
    )
    estado_certificado: Mapped[str | None] = mapped_column(
        Enum(EstadoCertificado, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )

    # Tarifa snapshot (no retroactiva)
    tarifa_monto: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    tarifa_moneda: Mapped[str | None] = mapped_column(
        Enum(TarifaMoneda, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )
    tarifa_fuente: Mapped[str | None] = mapped_column(
        Enum(TarifaFuente, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )

    # Atencion
    tipo_atencion: Mapped[str | None] = mapped_column(String(20), nullable=True)
    lugar_atencion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Cierre / Cancelacion (M6)
    motivo_cancelacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_cierre: Mapped[datetime | None] = mapped_column(nullable=True)
    cerrado_por: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )
    fecha_cancelacion: Mapped[datetime | None] = mapped_column(nullable=True)
    cancelado_por: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )
    comentario_admin: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=utcnow, onupdate=utcnow)

    # Relaciones
    cliente: Mapped["Cliente"] = relationship(  # noqa: F821
        foreign_keys=[cliente_id], lazy="selectin"
    )
    apoderado: Mapped["Persona"] = relationship(  # noqa: F821
        foreign_keys=[apoderado_id], lazy="selectin"
    )
    servicio: Mapped["Servicio"] = relationship(  # noqa: F821
        foreign_keys=[servicio_id], lazy="selectin"
    )
    promotor: Mapped["Promotor"] = relationship(  # noqa: F821
        foreign_keys=[promotor_id], lazy="selectin"
    )
    asignaciones: Mapped[list["SolicitudAsignacion"]] = relationship(
        back_populates="solicitud", lazy="selectin"
    )
    historial: Mapped[list["SolicitudEstadoHistorial"]] = relationship(
        back_populates="solicitud", lazy="selectin",
        order_by="SolicitudEstadoHistorial.cambiado_en.desc()",
    )
    pagos: Mapped[list["PagoSolicitud"]] = relationship(
        back_populates="solicitud", lazy="selectin"
    )
    archivos_rel: Mapped[list["SolicitudArchivo"]] = relationship(
        back_populates="solicitud", lazy="selectin"
    )
    resultados_medicos: Mapped[list["ResultadoMedico"]] = relationship(
        back_populates="solicitud", lazy="selectin"
    )


# ── solicitud_asignacion ──────────────────────────────────────────────

class SolicitudAsignacion(Base):
    __tablename__ = "solicitud_asignacion"

    asignacion_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitud_cmep.solicitud_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    persona_id: Mapped[int] = mapped_column(
        ForeignKey("personas.persona_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    rol: Mapped[str] = mapped_column(
        Enum(RolAsignacion, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    es_vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    asignado_por: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )
    fecha_asignacion: Mapped[datetime] = mapped_column(default=utcnow)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=utcnow, onupdate=utcnow)

    # Relaciones
    solicitud: Mapped["SolicitudCmep"] = relationship(back_populates="asignaciones")
    persona: Mapped["Persona"] = relationship(lazy="selectin")  # noqa: F821


# ── solicitud_estado_historial ────────────────────────────────────────

class SolicitudEstadoHistorial(Base):
    __tablename__ = "solicitud_estado_historial"

    historial_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitud_cmep.solicitud_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    campo: Mapped[str] = mapped_column(String(100), nullable=False)
    valor_anterior: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_nuevo: Mapped[str | None] = mapped_column(Text, nullable=True)
    cambiado_por: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )
    cambiado_en: Mapped[datetime] = mapped_column(default=utcnow)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    solicitud: Mapped["SolicitudCmep"] = relationship(back_populates="historial")


# ── pago_solicitud ────────────────────────────────────────────────────

class PagoSolicitud(Base):
    __tablename__ = "pago_solicitud"

    pago_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitud_cmep.solicitud_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    canal_pago: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha_pago: Mapped[date | None] = mapped_column(Date, nullable=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    moneda: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    referencia_transaccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Validacion del pago
    validated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )
    validated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=utcnow, onupdate=utcnow)

    # Relaciones
    solicitud: Mapped["SolicitudCmep"] = relationship(back_populates="pagos")


# ── archivos ──────────────────────────────────────────────────────────

class Archivo(Base):
    __tablename__ = "archivos"

    archivo_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    nombre_original: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_storage: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(
        Enum(TipoArchivo, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tamano_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    updated_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=utcnow, onupdate=utcnow)


# ── solicitud_archivo ─────────────────────────────────────────────────

class SolicitudArchivo(Base):
    __tablename__ = "solicitud_archivo"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitud_cmep.solicitud_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    archivo_id: Mapped[int] = mapped_column(
        ForeignKey("archivos.archivo_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    pago_id: Mapped[int | None] = mapped_column(
        ForeignKey("pago_solicitud.pago_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    # Relaciones
    solicitud: Mapped["SolicitudCmep"] = relationship(back_populates="archivos_rel")
    archivo: Mapped["Archivo"] = relationship(lazy="selectin")


# ── resultado_medico (M6) ────────────────────────────────────────────

class ResultadoMedico(Base):
    __tablename__ = "resultado_medico"

    resultado_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitud_cmep.solicitud_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    medico_id: Mapped[int] = mapped_column(
        ForeignKey("personas.persona_id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )

    fecha_evaluacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    diagnostico: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultado: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    recomendaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado_certificado: Mapped[str | None] = mapped_column(
        Enum(EstadoCertificado, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=utcnow, onupdate=utcnow)

    # Relaciones
    solicitud: Mapped["SolicitudCmep"] = relationship(back_populates="resultados_medicos")
    medico: Mapped["Persona"] = relationship(lazy="selectin")  # noqa: F821

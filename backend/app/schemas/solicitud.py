"""
Schemas Pydantic para solicitudes CMEP.
Ref: docs/source/05_api_y_policy.md (contratos API solicitudes)
"""

from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


# ── Request schemas ───────────────────────────────────────────────────

class ClienteInput(BaseModel):
    tipo_documento: str = Field(..., pattern="^(DNI|CE|PASAPORTE|RUC)$")
    numero_documento: str = Field(..., min_length=1, max_length=30)
    nombres: str = Field(..., min_length=1, max_length=150)
    apellidos: str = Field(..., min_length=1, max_length=150)
    celular: str | None = None
    fecha_nacimiento: date | None = None
    email: str | None = None


class ApoderadoInput(BaseModel):
    tipo_documento: str = Field(..., pattern="^(DNI|CE|PASAPORTE|RUC)$")
    numero_documento: str = Field(..., min_length=1, max_length=30)
    nombres: str = Field(..., min_length=1, max_length=150)
    apellidos: str = Field(..., min_length=1, max_length=150)
    celular: str | None = None


class PromotorInput(BaseModel):
    tipo_promotor: str = Field(..., pattern="^(PERSONA|EMPRESA|OTROS)$")
    # PERSONA: persona fields (nombres+apellidos required, doc preferred)
    tipo_documento: str | None = None
    numero_documento: str | None = None
    nombres: str | None = None
    apellidos: str | None = None
    # EMPRESA
    razon_social: str | None = None
    # OTROS
    nombre_promotor_otros: str | None = None
    # Shared optional fields
    ruc: str | None = None
    email: str | None = None
    celular_1: str | None = None
    fuente_promotor: str | None = None
    comentario: str | None = None

    @model_validator(mode="after")
    def validate_by_type(self) -> "PromotorInput":
        if self.tipo_promotor == "PERSONA":
            if not self.nombres or not self.apellidos:
                raise ValueError("PERSONA requiere nombres y apellidos")
        elif self.tipo_promotor == "EMPRESA":
            if not self.razon_social:
                raise ValueError("EMPRESA requiere razon_social")
        elif self.tipo_promotor == "OTROS":
            if not self.nombre_promotor_otros:
                raise ValueError("OTROS requiere nombre_promotor_otros")
        return self


class AtencionInput(BaseModel):
    tipo_atencion: str | None = Field(None, pattern="^(VIRTUAL|PRESENCIAL)$")
    lugar_atencion: str | None = None


class CreateSolicitudRequest(BaseModel):
    cliente: ClienteInput
    apoderado: ApoderadoInput | None = None
    promotor: PromotorInput | None = None
    promotor_id: int | None = None
    atencion: AtencionInput | None = None
    servicio_id: int | None = None
    comentario: str | None = None

    @model_validator(mode="after")
    def check_promotor_exclusivity(self) -> "CreateSolicitudRequest":
        if self.promotor is not None and self.promotor_id is not None:
            raise ValueError("Enviar promotor o promotor_id, no ambos")
        return self


class EditSolicitudRequest(BaseModel):
    """Campos editables de la solicitud (PATCH)."""
    tipo_atencion: str | None = None
    lugar_atencion: str | None = None
    comentario: str | None = None
    servicio_id: int | None = None
    estado_certificado: str | None = None  # APROBADO | OBSERVADO
    # Cliente editable
    cliente_nombres: str | None = None
    cliente_apellidos: str | None = None
    cliente_celular: str | None = None
    cliente_email: str | None = None


# ── M3: Action request schemas ───────────────────────────────────────

class AsignarGestorRequest(BaseModel):
    """Request para ASIGNAR_GESTOR / CAMBIAR_GESTOR."""
    persona_id_gestor: int


class RegistrarPagoRequest(BaseModel):
    """Request para REGISTRAR_PAGO."""
    canal_pago: str = Field(..., min_length=1)
    fecha_pago: date
    monto: Decimal = Field(..., gt=0)
    moneda: str = Field("PEN", pattern="^(PEN|USD)$")
    referencia_transaccion: str | None = None


class AsignarMedicoRequest(BaseModel):
    """Request para ASIGNAR_MEDICO / CAMBIAR_MEDICO."""
    persona_id_medico: int


class CerrarRequest(BaseModel):
    """Request para CERRAR (comentario opcional)."""
    comentario: str | None = None


class CancelarRequest(BaseModel):
    """Request para CANCELAR (comentario opcional)."""
    comentario: str | None = None


class OverrideRequest(BaseModel):
    """Request para OVERRIDE (solo ADMIN en CERRADO/CANCELADO)."""
    motivo: str = Field(..., min_length=1)
    accion: str = Field(..., pattern="^(EDITAR_DATOS|CAMBIAR_GESTOR|CAMBIAR_MEDICO|REGISTRAR_PAGO|CERRAR|CANCELAR)$")
    payload: dict = Field(default_factory=dict)


# ── Response schemas ──────────────────────────────────────────────────

class PersonaDTO(BaseModel):
    persona_id: int
    tipo_documento: str | None = None
    numero_documento: str | None = None
    nombres: str
    apellidos: str
    celular_1: str | None = None
    email: str | None = None

    model_config = {"from_attributes": True}


class ClienteDTO(BaseModel):
    persona_id: int
    doc: str  # "DNI 12345678"
    nombre: str
    celular: str | None = None

    model_config = {"from_attributes": True}


class AsignacionVigenteDTO(BaseModel):
    persona_id: int
    nombre: str
    rol: str

    model_config = {"from_attributes": True}


class PagoDTO(BaseModel):
    pago_id: int
    canal_pago: str | None = None
    fecha_pago: date | None = None
    monto: Decimal
    moneda: str
    referencia_transaccion: str | None = None
    validated_at: datetime | None = None

    model_config = {"from_attributes": True}


class HistorialDTO(BaseModel):
    historial_id: int
    campo: str
    valor_anterior: str | None = None
    valor_nuevo: str | None = None
    cambiado_por: int | None = None
    cambiado_en: datetime
    comentario: str | None = None

    model_config = {"from_attributes": True}


class SolicitudListItemDTO(BaseModel):
    solicitud_id: int
    codigo: str | None = None
    cliente: ClienteDTO
    apoderado: PersonaDTO | None = None
    estado_operativo: str
    operador: str | None = None
    gestor: str | None = None
    medico: str | None = None
    promotor: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResultadoMedicoDTO(BaseModel):
    resultado_id: int
    medico_id: int
    fecha_evaluacion: date | None = None
    diagnostico: str | None = None
    resultado: str | None = None
    observaciones: str | None = None
    recomendaciones: str | None = None
    estado_certificado: str | None = None

    model_config = {"from_attributes": True}


class SolicitudDetailDTO(BaseModel):
    solicitud_id: int
    codigo: str | None = None
    cliente: ClienteDTO
    apoderado: PersonaDTO | None = None
    servicio: dict | None = None
    estado_atencion: str
    estado_pago: str
    estado_certificado: str | None = None
    tarifa_monto: Decimal | None = None
    tarifa_moneda: str | None = None
    tipo_atencion: str | None = None
    lugar_atencion: str | None = None
    comentario: str | None = None
    estado_operativo: str
    acciones_permitidas: list[str]
    asignaciones_vigentes: dict[str, AsignacionVigenteDTO | None]
    promotor: dict | None = None
    pagos: list[PagoDTO]
    archivos: list[dict]
    historial: list[HistorialDTO]
    # M6: campos de cierre/cancelacion
    motivo_cancelacion: str | None = None
    fecha_cierre: datetime | None = None
    cerrado_por: int | None = None
    fecha_cancelacion: datetime | None = None
    cancelado_por: int | None = None
    comentario_admin: str | None = None
    resultados_medicos: list[ResultadoMedicoDTO] = []
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

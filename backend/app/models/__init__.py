"""
Registro central de modelos ORM.
Alembic importa Base.metadata desde aqui via database.py.
"""

from app.models.persona import Persona, TipoDocumento  # noqa: F401
from app.models.user import (  # noqa: F401
    User,
    UserRole,
    UserPermission,
    Session,
    PasswordReset,
    EstadoUser,
    UserRoleEnum,
)
from app.models.cliente import Cliente, ClienteApoderado, EstadoCliente, EstadoApoderado  # noqa: F401
from app.models.promotor import Promotor, TipoPromotor  # noqa: F401
from app.models.empleado import Empleado, MedicoExtra, RolEmpleado, EstadoEmpleado  # noqa: F401
from app.models.servicio import Servicio  # noqa: F401
from app.models.solicitud import (  # noqa: F401
    SolicitudCmep,
    SolicitudAsignacion,
    SolicitudEstadoHistorial,
    PagoSolicitud,
    Archivo,
    SolicitudArchivo,
    ResultadoMedico,
    EstadoPago,
    EstadoAtencion,
    EstadoCertificado,
    TarifaMoneda,
    TarifaFuente,
    RolAsignacion,
    TipoArchivo,
)

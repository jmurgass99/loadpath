"""loadpath — esquemas de datos estructurales unificados.

Single source of truth para la suite Structural JM / Loadpath: objetos Pydantic
v2 estrictos que describen física estructural base, compartidos entre el gateway
(`_platform`), los repos de productos y (vía JSON-schema → TypeScript) el frontend.

Convención de unidades (SI, con sufijo explícito en cada campo):
    fuerzas en kN, momentos en kN·m, longitudes en m, geometría de sección en mm
    (área mm², inercia mm⁴, módulo mm³, alabeo mm⁶), módulos de material en MPa.
"""
from .materials import MaterialType, StructuralMaterial
from .sections import FrameSection
from .forces import InternalForces

__version__ = "0.1.1"
UNIT_SYSTEM = "SI: kN, kN·m, m; sección en mm (mm²/mm⁴/mm³/mm⁶); material en MPa"

__all__ = [
    "MaterialType",
    "StructuralMaterial",
    "FrameSection",
    "InternalForces",
    "UNIT_SYSTEM",
    "__version__",
]

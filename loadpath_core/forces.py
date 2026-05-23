"""Fuerzas internas en barras."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class InternalForces(BaseModel):
    """Fuerzas internas en una estación de una barra (unidades SI).

    Convención de signos: axial `N` positivo en tracción. Fuerzas en kN,
    momentos en kN·m. `station_m` es la distancia a lo largo de la barra desde
    su nudo inicial. Las componentes por defecto son 0.0 para permitir construir
    estados parciales (p.ej. solo flexión).

    Ejes locales: 1 = axial (eje de la barra), 2 = y, 3 = z.
    """
    model_config = ConfigDict(extra="forbid")

    member_id: str
    station_m: float = Field(ge=0, description="Distancia a lo largo de la barra (m).")
    N_kN: float = Field(default=0.0, description="Axial (kN), tracción positiva.")
    Vy_kN: float = Field(default=0.0, description="Cortante eje local y (kN).")
    Vz_kN: float = Field(default=0.0, description="Cortante eje local z (kN).")
    T_kNm: float = Field(default=0.0, description="Torsión (kN·m).")
    My_kNm: float = Field(default=0.0, description="Momento flector eje local y (kN·m).")
    Mz_kNm: float = Field(default=0.0, description="Momento flector eje local z (kN·m).")

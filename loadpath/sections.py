"""Secciones de barra (frame sections)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FrameSection(BaseModel):
    """Propiedades geométricas de una sección de barra (unidades SI, mm).

    Obligatorias las que cualquier análisis elástico necesita (`A`, `Ix`, `Iy`,
    `J`). El alabeo (`Cw`), los módulos plásticos/elásticos, las propiedades
    eficaces de Clase 4 y las dimensiones brutas son opcionales: no todos los
    flujos los requieren.

    Ejes: x = eje fuerte, y = eje débil (convención del ecosistema).
    
    Mapeo con InternalForces (ejes locales):
      - La flexión fuerte (generalmente Mz_kNm, momento sobre el eje local z / 3) 
        se resiste con las propiedades del eje fuerte x (Ix_mm4, Sx_mm3, Zx_mm3).
      - La flexión débil (generalmente My_kNm, momento sobre el eje local y / 2) 
        se resiste con las propiedades del eje débil y (Iy_mm4, Sy_mm3, Zy_mm3).
    """
    model_config = ConfigDict(extra="forbid")

    name: str
    A_mm2: float = Field(gt=0, description="Área de la sección (mm²).")
    Ix_mm4: float = Field(gt=0, description="Inercia respecto al eje fuerte x (mm⁴).")
    Iy_mm4: float = Field(gt=0, description="Inercia respecto al eje débil y (mm⁴).")
    J_mm4: float = Field(gt=0, description="Constante de torsión de St. Venant (mm⁴).")
    Cw_mm6: float | None = Field(default=None, ge=0, description="Constante de alabeo (mm⁶).")
    Zx_mm3: float | None = Field(default=None, gt=0, description="Módulo plástico, eje x (mm³).")
    Zy_mm3: float | None = Field(default=None, gt=0, description="Módulo plástico, eje y (mm³).")
    Sx_mm3: float | None = Field(default=None, gt=0, description="Módulo elástico, eje x (mm³).")
    Sy_mm3: float | None = Field(default=None, gt=0, description="Módulo elástico, eje y (mm³).")
    depth_mm: float | None = Field(default=None, gt=0, description="Canto total (mm).")
    width_mm: float | None = Field(default=None, gt=0, description="Ancho (mm).")
    section_class: int | None = Field(default=None, ge=1, le=4, description="Clase de sección EN 1993-1-1 (1 a 4).")
    A_eff_mm2: float | None = Field(default=None, gt=0, description="Área eficaz para secciones Clase 4 (mm²).")
    Ix_eff_mm4: float | None = Field(default=None, gt=0, description="Inercia eficaz eje fuerte x Clase 4 (mm⁴).")
    Iy_eff_mm4: float | None = Field(default=None, gt=0, description="Inercia eficaz eje débil y Clase 4 (mm⁴).")
    Sx_eff_mm3: float | None = Field(default=None, gt=0, description="Módulo elástico eficaz eje fuerte x Clase 4 (mm³).")
    Sy_eff_mm3: float | None = Field(default=None, gt=0, description="Módulo elástico eficaz eje débil y Clase 4 (mm³).")

    @property
    def I_strong_axis_mm4(self) -> float:
        """Alias para inercia de eje fuerte (Ix_mm4)."""
        return self.Ix_mm4

    @property
    def I_weak_axis_mm4(self) -> float:
        """Alias para inercia de eje débil (Iy_mm4)."""
        return self.Iy_mm4

    @property
    def I_strong_mm4(self) -> float:
        """Alias para inercia de eje fuerte (Ix_mm4)."""
        return self.Ix_mm4

    @property
    def I_weak_mm4(self) -> float:
        """Alias para inercia de eje débil (Iy_mm4)."""
        return self.Iy_mm4

    @property
    def S_strong_axis_mm3(self) -> float | None:
        """Alias para módulo elástico del eje fuerte (Sx_mm3)."""
        return self.Sx_mm3

    @property
    def S_weak_axis_mm3(self) -> float | None:
        """Alias para módulo elástico del eje débil (Sy_mm3)."""
        return self.Sy_mm3

    @property
    def Z_strong_axis_mm3(self) -> float | None:
        """Alias para módulo plástico del eje fuerte (Zx_mm3)."""
        return self.Zx_mm3

    @property
    def Z_weak_axis_mm3(self) -> float | None:
        """Alias para módulo plástico del eje débil (Zy_mm3)."""
        return self.Zy_mm3

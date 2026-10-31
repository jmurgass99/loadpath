"""Materiales estructurales."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MaterialType(str, Enum):
    """Familia de material estructural."""
    STEEL = "steel"
    CONCRETE = "concrete"
    COLD_FORMED_STEEL = "cold_formed_steel"
    ALUMINUM = "aluminum"
    TIMBER = "timber"
    MASONRY = "masonry"


class StructuralMaterial(BaseModel):
    """Propiedades físicas de un material estructural (unidades SI, MPa).

    `Fy_MPa`/`Fu_MPa` aplican a aceros; `fc_MPa` (compresión característica) al
    hormigón. Solo `E_MPa`, `poisson` y `density_kg_m3` son obligatorios, porque
    son los que todo solver necesita; las resistencias son opcionales según el
    material.
    """
    model_config = ConfigDict(extra="forbid")

    name: str
    material_type: MaterialType
    E_MPa: float = Field(gt=0, description="Módulo de elasticidad (MPa).")
    poisson: float = Field(ge=0.0, le=0.5, description="Coeficiente de Poisson.")
    density_kg_m3: float = Field(gt=0, description="Densidad (kg/m³).")
    Fy_MPa: float | None = Field(default=None, gt=0, description="Límite elástico, acero (MPa).")
    Fu_MPa: float | None = Field(default=None, gt=0, description="Resistencia última, acero (MPa).")
    fc_MPa: float | None = Field(default=None, gt=0, description="Resistencia a compresión, hormigón (MPa).")
    damping_ratio: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Razón de amortiguamiento (fracción del crítico)."
    )

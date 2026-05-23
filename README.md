# loadpath-core

**Esquemas de datos estructurales unificados** — *single source of truth* para la
suite Structural JM / Loadpath.

Paquete Pydantic v2 estricto que define la física estructural base compartida
entre el gateway (`_platform`), los repos de productos y —vía JSON-schema →
TypeScript— el frontend. Evita el drift de tipos entre microservicios.

## Modelos v1

| Modelo | Qué describe |
|---|---|
| `StructuralMaterial` | Material: `E_MPa`, `poisson`, `density_kg_m3`, `Fy_MPa`/`Fu_MPa` (acero), `fc_MPa` (hormigón), `damping_ratio` |
| `FrameSection` | Sección de barra: `A_mm2`, `Ix/Iy_mm4`, `J_mm4`, `Cw_mm6`, módulos plásticos/elásticos, dimensiones |
| `InternalForces` | Fuerzas en una estación: `N_kN`, `Vy/Vz_kN`, `T_kNm`, `My/Mz_kNm` |

`MaterialType`: steel, concrete, cold_formed_steel, aluminum, timber, masonry.

## Convención de unidades (SI, sufijo explícito por campo)

Fuerzas en kN, momentos en kN·m, longitudes en m; geometría de sección en mm
(área mm², inercia mm⁴, módulo mm³, alabeo mm⁶); módulos de material en MPa.
Validación estricta: campos obligatorios mínimos y `extra="forbid"`.

## Uso

```python
from loadpath_core import StructuralMaterial, FrameSection, InternalForces

acero = StructuralMaterial(
    name="A992", material_type="steel", E_MPa=200000, poisson=0.3,
    density_kg_m3=7850, Fy_MPa=345, Fu_MPa=450,
)
sec = FrameSection(name="W14X90", A_mm2=17100, Ix_mm4=4.16e8, Iy_mm4=1.51e8, J_mm4=4.16e6)
f = InternalForces(member_id="V101", station_m=3.0, Mz_kNm=120.0)
```

## Instalación / tests

```bash
pip install -e .[test]
python -m pytest -q
```

## Roadmap (fuera de v1)

- `loadpath_core.bim`: esquema BIM/rebar (columnas, vigas, parrillas, ganchos)
  que consume el add-in de Revit. Es la base del workstream de interoperabilidad.
- Generación de tipos TypeScript desde `model_json_schema()` para el frontend.
- Modelo relacional unificado (PostgreSQL) para el *single source of truth* en la nube.

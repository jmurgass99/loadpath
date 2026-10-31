# loadpath

Esquemas de datos estructurales unificados: materiales, secciones de barra y esfuerzos internos como modelos Pydantic v2 estrictos (campos mínimos obligatorios, `extra="forbid"`, unidades SI con sufijo explícito en cada campo). Sirve como contrato de datos entre herramientas de cálculo, exportadores y frontends (vía JSON Schema → TypeScript).

[![CI](https://github.com/jmurgass99/loadpath/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/loadpath/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Paquete independiente. Dependencias: `pydantic` y `numpy`.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/loadpath.git
```

## Modelos

| Modelo | Qué describe |
|---|---|
| `StructuralMaterial` | Material: `E_MPa`, `poisson`, `density_kg_m3`, `Fy_MPa`/`Fu_MPa` (acero), `fc_MPa` (hormigón), `damping_ratio` |
| `FrameSection` | Sección de barra: `A_mm2`, `Ix/Iy_mm4`, `J_mm4`, `Cw_mm6`, módulos plásticos y elásticos, dimensiones |
| `InternalForces` | Esfuerzos en una estación: `N_kN`, `Vy/Vz_kN`, `T_kNm`, `My/Mz_kNm` |

`MaterialType`: steel, concrete, cold_formed_steel, aluminum, timber, masonry.

## Convención de unidades

Fuerzas en kN, momentos en kN·m, longitudes en m; geometría de sección en mm (área mm², inercia mm⁴, módulo mm³, alabeo mm⁶); módulos de material en MPa. La constante `loadpath.UNIT_SYSTEM` lo declara.

## Uso

```python
from loadpath import StructuralMaterial, FrameSection, InternalForces

acero = StructuralMaterial(
    name="A992", material_type="steel", E_MPa=200000, poisson=0.3,
    density_kg_m3=7850, Fy_MPa=345, Fu_MPa=450,
)
sec = FrameSection(name="W14X90", A_mm2=17100, Ix_mm4=4.16e8, Iy_mm4=1.51e8, J_mm4=4.16e6)
f = InternalForces(member_id="V101", station_m=3.0, Mz_kNm=120.0)

print(FrameSection.model_json_schema()["title"])   # esquema JSON para generar tipos en otros lenguajes
```

## Ayudas de elementos finitos (`loadpath.fea`)

- `non_prismatic.beam_stiffness_2d(L, EI, EA, n)`: matriz de rigidez de viga 2D con EI y EA variables a lo largo de la barra (integración de Simpson).
- `semi_rigid.semi_rigid_bending_stiffness(Kb, Ri, Rj)`: corrección de la rigidez a flexión por nudos semirrígidos.

## Tests

```bash
pip install -e ".[test]"
pytest -q
```

## Licencia

MIT. Consulta [LICENSE](LICENSE).

---

Parte del toolkit estructural de código abierto **Loadpath**, de [Jesús Murgas](https://github.com/jmurgass99).

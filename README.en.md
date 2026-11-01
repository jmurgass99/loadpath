# loadpath — structural data contract (materials, sections, internal forces) in Pydantic v2 and frame FEA helpers

[Español](README.md) · **English** · [Português](README.pt.md) · [Italiano](README.it.md)

Three strict models that travel between analysis programs, checkers, exporters and interfaces: `StructuralMaterial`, `FrameSection` and `InternalForces`, with SI units in the name of every field, `extra="forbid"` and a JSON Schema to generate types in other languages. Plus two frame finite element helpers: the 2D stiffness matrix of a non-prismatic beam (EI(x), EA(x) by Simpson) and the condensation of end rotational springs for semi-rigid joints. Dependencies: `pydantic` and `numpy`.

[![CI](https://github.com/jmurgass99/loadpath/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/loadpath/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What problem it solves

Between an analysis program, a section checker and a report, data crosses three boundaries, and at each one units, axes and sign conventions get lost: the strong-axis moment is called M3 in one place and M_y in another, axial force is positive in compression here and in tension there, and an `E = 210` does not say whether it is GPa or MPa. `loadpath` fixes a single format with the unit in the field name, the axes documented in the two models that share them, and validation on input, so that malformed data is rejected with the field path instead of propagating as a number.

**Use it when**

- you define the input or output of a calculation tool (REST API, CLI, file) and want materials, sections and internal forces to have a single validated format;
- you generate TypeScript types or API documentation from the JSON Schema of the models;
- you import results from SAP2000, ETABS or another program and need a place to declare the axis mapping and the sign convention;
- you need the stiffness matrix of a tapered or haunched beam (piecewise EI(x)) or the condensed stiffness of a beam with semi-rigid joints to assemble it into a frame.

**Don't use it for**

- section catalogues (it does not include IPE, HEB or W tables; the examples show how to compute the properties from the dimensions and check them);
- code checks: there are no design resistances, buckling or section classification, only the data contract and the stiffness helpers;
- analysis of complete structures: `fea` gives element matrices, it does not assemble or solve (the portal frame example does it in 40 lines with numpy to show how);
- built-up, asymmetric or warping-restrained sections: `FrameSection` describes properties, not geometry.

## Installation

```bash
pip install git+https://github.com/jmurgass99/loadpath.git
```

For development: `git clone`, `pip install -e ".[test]"`, `pytest -q` (6 test files). On Windows, if the console is not UTF-8, run the examples with `python -X utf8 examples/<name>.py`.

## Capabilities

| Capability | Modules | Code or reference | Use cases |
|---|---|---|---|
| Materials: `StructuralMaterial` with mandatory E, ν, ρ and optional strengths by type (steel, concrete, cold-formed, aluminium, timber, masonry); range validation; JSON Schema | `materials` | EN 1993-1-1 §3.2.6; EN 10025-2 Table 7; EN 1992-1-1 Table 3.1 and §3.1.3; EN 14080; EN 1999-1-1 | [5 cases](#1-materials) |
| Sections: `FrameSection` with mandatory A, I_x, I_y, J and optional C_w, elastic and plastic moduli and dimensions; strong- and weak-axis aliases; axis map with the internal forces | `sections` | EN 10365 / EN 10210 (catalogue check); SAP2000 M3 strong / M2 weak convention | [5 cases](#2-sections) |
| Internal forces and data contract: `InternalForces` per station with tension positive and components zero by default; JSON Lines; composite models with `$defs`; mapping from SAP2000 | `forces`, Pydantic v2 | Local axis convention 1-2-3 | [5 cases](#3-internal-forces-and-data-contract) |
| FEA helpers: 6×6 stiffness of a 2D beam with EI(x) and EA(x) by Simpson (cantilever flexibility), condensed end rotational springs (Monforton and Wu) | `fea.non_prismatic`, `fea.semi_rigid` | Monforton and Wu (1963); EN 1993-1-8 §5.2.2.5 (joint classification); PCA frame constant tables | [5 cases](#4-finite-element-helpers) |

The 20 scripts in `examples/` were run in a clean environment before publishing; their output is in `examples/output/` and is what is reproduced here.

## Use cases

The outputs are reproduced exactly as the scripts print them, in Spanish.

### 1. Materials

#### Project material catalogue with code values: S355, A992, C30/37, GL24h, aluminium 6061-T6 and masonry

<details><summary>Actual output of <code>python examples/material_catalog_steel_concrete_timber_aluminum_from_codes.py</code></summary>

```text
Tipos admitidos: ['steel', 'concrete', 'cold_formed_steel', 'aluminum', 'timber', 'masonry']

  material                           tipo                E [MPa]     ν ρ [kg/m³]    F_y    F_u    f_c     ξ
  S355 (EN 10025-2)                  steel                210000  0.30      7850    355    490      —  0.02
  A992 (ASTM)                        steel                200000  0.30      7850    345    450      —  0.02
  C30/37 (EN 1992-1-1)               concrete              33000  0.20      2500      —      —     30  0.05
  GL24h (EN 14080)                   timber                11500  0.40       420      —      —      —  0.01
  EN AW-6061 T6 (EN 1999-1-1)        aluminum              70000  0.33      2700    240    260      —     —
  Ladrillo macizo M10 (EN 1996-1-1)  masonry                5000  0.20      1800      —      —      5     —

Módulo de cortante del S355: G = E/(2·(1+ν)) = 80769 MPa (EN 1993-1-1: 81 000)
Peso propio del S355: 76.98 kN/m³; del C30/37: 24.52 kN/m³

Un consumidor comprueba con `material_type` qué resistencia leer: Fy/Fu en metales, fc en hormigón y fábrica; None es «no aplica», no «cero».
```

</details>

#### What the schema rejects and why: field without a unit, negative E, ν > 0.5, unknown type, text in a number

<details><summary>Actual output of <code>python examples/material_validation_rejects_missing_units_and_out_of_range.py</code></summary>

```text
Válido: S275 E = 210000 MPa

  caso                         errores  tipo → campo
  E sin unidad (campo `E`)           1  extra_forbidden → E
  E_MPa negativo                     1  greater_than → E_MPa
  ν = 0,7 (> 0,5)                    1  less_than_equal → poisson
  densidad 0                         1  greater_than → density_kg_m3
  tipo `adamantium`                  1  enum → material_type
  F_y como texto                     1  float_parsing → Fy_MPa
  falta E_MPa                        1  missing → E_MPa

`extra='forbid'` convierte un campo sin unidad en un error en vez de en un número que viaja sin que nadie sepa si es MPa o kPa.
```

</details>

#### From the JSON Schema to a TypeScript interface with the ranges and units in the comments

<details><summary>Actual output of <code>python examples/material_json_schema_to_typescript_interface.py</code></summary>

```text
JSON Schema: 9 propiedades, obligatorias ['name', 'material_type', 'E_MPa', 'poisson', 'density_kg_m3'], enum MaterialType con 6 valores

/** Propiedades físicas de un material estructural (unidades SI, MPa). */
export interface StructuralMaterial {
  name: string;
  material_type: "steel" | "concrete" | "cold_formed_steel" | "aluminum" | "timber" | "masonry";
  /** Módulo de elasticidad (MPa). (> 0) */
  E_MPa: number;
  /** Coeficiente de Poisson. (>= 0.0, <= 0.5) */
  poisson: number;
  /** Densidad (kg/m³). (> 0) */
  density_kg_m3: number;
  /** Límite elástico, acero (MPa). (> 0) */
  Fy_MPa?: number | null;
  /** Resistencia última, acero (MPa). (> 0) */
  Fu_MPa?: number | null;
  /** Resistencia a compresión, hormigón (MPa). (> 0) */
  fc_MPa?: number | null;
  /** Razón de amortiguamiento (fracción del crítico). (>= 0.0, <= 1.0) */
  damping_ratio?: number | null;
}

El mismo generador sirve para FrameSection e InternalForces; `?` marca las propiedades opcionales (None en Python).
```

</details>

#### Concretes C20/25 to C50/60 with E_cm = 22·(f_cm/10)^0.3 GPa (EN 1992-1-1 Table 3.1) and the aggregate factor

<details><summary>Actual output of <code>python examples/material_concrete_Ecm_from_fck_EN1992_table_3_1.py</code></summary>

```text
  clase             f_ck  f_cm E_cm calc [GPa] Tabla 3.1  desvío
  C20/25 cuarcita     20    28           29.96        30   -0.1 %
  C25/30 cuarcita     25    33           31.48        31   +1.5 %
  C30/37 cuarcita     30    38           32.84        33   -0.5 %
  C35/45 cuarcita     35    43           34.08        34   +0.2 %
  C40/50 cuarcita     40    48           35.22        35   +0.6 %
  C45/55 cuarcita     45    53           36.28        36   +0.8 %
  C50/60 cuarcita     50    58           37.28        37   +0.8 %

Efecto del árido para C30/37 (§3.1.3(2)):
  cuarcita  E_cm =  32.8 GPa
  caliza    E_cm =  29.6 GPa
  arenisca  E_cm =  23.0 GPa
  basalto   E_cm =  39.4 GPa

La fórmula reproduce la tabla con desvíos < 2 % (la tabla redondea al GPa; C25/30 es el peor caso, 31,5 frente a 31); el módulo que viaja en el esquema es el calculado, no el redondeado.
```

</details>

#### Steels S235 to S460 with the thickness-dependent yield strength (EN 10025-2 Table 7)

<details><summary>Actual output of <code>python examples/material_steel_grades_EN10025_thickness_dependent_fy.py</code></summary>

```text
  grado      t=10     t=20     t=50     t=70   (f_y en MPa, EN 10025-2)
  S235        235      225      215      215
  S275        275      265      255      245
  S355        355      345      335      325
  S460        460      440      430      410

Chapa de 50 mm: EN 10025-2 frente a la simplificación de EN 1993-1-1 Tabla 3.1 (40 < t <= 80):
  S235: 215 MPa frente a 215 MPa; usar el nominal de t <= 16 (235) sobrestimaría un 9 %
  S275: 255 MPa frente a 255 MPa; usar el nominal de t <= 16 (275) sobrestimaría un 8 %
  S355: 335 MPa frente a 335 MPa; usar el nominal de t <= 16 (355) sobrestimaría un 6 %
  S460: 430 MPa frente a 410 MPa; usar el nominal de t <= 16 (460) sobrestimaría un 7 %

Ejemplo serializado: {"name":"S355 t=50 mm","material_type":"steel","E_MPa":210000.0,"poisson":0.3,"density_kg_m3":7850.0,"Fy_MPa":335.0,"Fu_MPa":470.0,"fc_MPa":null,"damping_ratio":null}
```

</details>

### 2. Sections

#### Properties of an I section from its dimensions and check against the catalogue: IPE 300 and HEB 300

The area with the root-fillet correction (4 − π)·r² comes out exact; I_x and W_pl are 4 % below the catalogue and torsion 20–25 %: I_t is taken from the catalogue.

<details><summary>Actual output of <code>python examples/section_properties_from_I_shape_dimensions_IPE300_HEB300_vs_catalog.py</code></summary>

```text
IPE 300: h = 300, b = 150, t_w = 7.1, t_f = 10.7, r = 15 mm
              A [cm²]  I_x [cm⁴]  I_y [cm⁴] W_pl,x [cm³] I_t [cm⁴] I_w [10³ cm⁶]
  calculado      53.8       7999        603          602      15.6           126
  catálogo       53.8       8356        604          628      20.1           126
  desvío       +0.0 %     -4.3 %     -0.2 %       -4.1 %   -22.5 %        +0.1 %

HEB 300: h = 300, b = 300, t_w = 11.0, t_f = 19.0, r = 27 mm
              A [cm²]  I_x [cm⁴]  I_y [cm⁴] W_pl,x [cm³] I_t [cm⁴] I_w [10³ cm⁶]
  calculado     149.1      24187       8553         1790     148.8          1688
  catálogo      149.1      25170       8563         1869     185.0          1688
  desvío       -0.0 %     -3.9 %     -0.1 %       -4.2 %   -19.6 %        +0.0 %

La corrección (4 − π)·r² deja el área exacta; en I_x y W_pl los acuerdos aportan ~4 % y en I_t un 20–25 %: I_y e I_w salen bien, I_t se toma de catálogo.
```

</details>

#### RHS 200×100×8 and CHS 219.1×8 tubes from their dimensions against EN 10210 (Bredt for RHS torsion)

<details><summary>Actual output of <code>python examples/section_hollow_sections_RHS_CHS_from_dimensions_vs_EN10210.py</code></summary>

```text
  perfil                       A [cm²]  I_x [cm⁴]  I_y [cm⁴]  I_t [cm⁴] W_pl,x [cm³]
  RHS 200x100x8    calculado      45.4       2306        758       1758          289
                   EN 10210       44.8       2269        747       1804          283
                   desvío       +1.4 %     +1.6 %     +1.5 %     -2.6 %       +2.1 %
  CHS 219.1x8      calculado      53.1       2960       2960       5919          357
                   EN 10210       53.1       2960       2960       5919          357
                   desvío       -0.1 %     -0.0 %     -0.0 %     +0.0 %       -0.1 %

El RHS sale 1–3 % alto por las esquinas vivas (el catálogo tiene r_o = 1,5·t); Bredt da la torsión a −2,6 %. El CHS es exacto porque la fórmula es la geometría real.
```

</details>

#### Which moment goes with which inertia: M_z (strong) with I_x, M_y (weak) with I_y, and the error of crossing them

<details><summary>Actual output of <code>python examples/section_strong_weak_axis_mapping_to_internal_forces_bending_stress.py</code></summary>

```text
Mapa de ejes:
  flexión fuerte  M_z = 90 kN·m  →  I_x = 8.356e+07 mm⁴, S_x = 557000 mm³
  flexión débil   M_y = 6 kN·m  →  I_y = 6.040e+06 mm⁴, S_y = 80500 mm³
  cortante V_z = 60 kN acompaña a M_z (plano fuerte); V_y acompañaría a M_y

Tensiones elásticas [MPa]: N/A = -22.3, M_z/S_x = ±161.6, M_y/S_y = ±74.5
Esquina más comprimida: σ = -258.4 MPa → utilización elástica 0.73 frente a f_y = 355 MPa

Si se cruzan los ejes (M_z con S_y): σ = 1118 MPa, 6.9 veces la real. El esquema lo evita nombrando los ejes en los dos modelos.
```

</details>

#### Mandatory minimum, optional fields as None and rejections of the section schema

<details><summary>Actual output of <code>python examples/section_validation_optional_fields_and_json_schema_required.py</code></summary>

```text
Sección mínima: {'name': 'barra genérica', 'A_mm2': 5000.0, 'Ix_mm4': 80000000.0, 'Iy_mm4': 6000000.0, 'J_mm4': 200000.0}
  opcionales en None: ['Cw_mm6', 'Zx_mm3', 'Zy_mm3', 'Sx_mm3', 'Sy_mm3', 'depth_mm', 'width_mm']
Sección completa: W14X90, 12 de 12 campos

JSON Schema: obligatorias ['name', 'A_mm2', 'Ix_mm4', 'Iy_mm4', 'J_mm4']; opcionales ['Cw_mm6', 'Zx_mm3', 'Zy_mm3', 'Sx_mm3', 'Sy_mm3', 'depth_mm', 'width_mm']

  sin J          → missing en J_mm4
  área 0         → greater_than en A_mm2
  C_w negativo   → greater_than_equal en Cw_mm6
  campo `peso`   → extra_forbidden en peso
  I_x como texto → float_parsing en Ix_mm4

C_w = 0 sí se admite (tubos cerrados); lo que se rechaza es el valor negativo.
```

</details>

#### Weight per metre, radii of gyration and column slenderness derived from the schema fields

<details><summary>Actual output of <code>python examples/section_weight_radius_of_gyration_and_slenderness_table.py</code></summary>

```text
S355: λ_1 = π·sqrt(E/f_y) = 76.4; pilar L_cr = 4 m

  perfil       peso [kg/m] i_x [mm] i_y [mm]    λ_y   λ̄_y      régimen
  IPE 300             42.2    124.6     33.5  119.4   1.56      esbelto
  HEB 300            117.0    129.9     75.8   52.8   0.69   intermedio
  HEA 200             42.3     82.8     49.8   80.3   1.05   intermedio
  CHS 219.1x8         41.6     74.7     74.7   53.5   0.70   intermedio

Pesos de catálogo: IPE 300 42,2; HEB 300 117; HEA 200 42,3; CHS 219,1×8 41,6 kg/m. El IPE 300 pesa lo mismo que el HEA 200 y es 2,6 veces más esbelto en su eje débil.
```

</details>

### 3. Internal forces and data contract

#### Simply supported beam with a uniform load: 13 stations as a list of `InternalForces` and envelope against q·L/2 and q·L²/8

<details><summary>Actual output of <code>python examples/internal_forces_simply_supported_beam_stations_udl_envelope.py</code></summary>

```text
  x [m]  V_z [kN] M_z [kN·m]
    0.0      72.0        0.0
    0.5      60.0       33.0
    1.0      48.0       60.0
    1.5      36.0       81.0
    2.0      24.0       96.0
    2.5      12.0      105.0
    3.0       0.0      108.0
    3.5     -12.0      105.0
    4.0     -24.0       96.0
    4.5     -36.0       81.0
    5.0     -48.0       60.0
    5.5     -60.0       33.0
    6.0     -72.0        0.0

Envolvente: |V_z| máx = 72.0 kN en x = 0.0 m (q·L/2 = 72.0); M_z máx = 108.0 kN·m en x = 3.0 m (q·L²/8 = 108.0)
Serializado: 13 estaciones, 111 bytes cada una; ejemplo: {"member_id":"V-12","station_m":3.0,"N_kN":0.0,"Vy_kN":0.0,"Vz_kN":0.0,"T_kNm":0.0,"My_kNm":0.0,"Mz_kNm":108.0}
N, V_y, T y M_y quedan en 0,0 por defecto: un estado parcial es válido y explícito.
```

</details>

#### Axial force sign convention (tension positive): column and tie, fibre stresses and what happens if the importer flips it

<details><summary>Actual output of <code>python examples/internal_forces_sign_convention_tension_positive_column_combined_stress.py</code></summary>

```text
  barra                      N [kN] M_z [kN·m] σ fibra 1 [MPa] σ fibra 2 [MPa] σ_c,máx [MPa] |σ_c|/f_y
  pilar P-3 (compresión)       -850        180            50.3          -164.3        -164.3      0.46
  tirante T-1 (tracción)        300         20            32.0             8.2           0.0      0.00

Con el signo del axil invertido al importar (error típico entre programas):
  barra                      N [kN] M_z [kN·m] σ fibra 1 [MPa] σ fibra 2 [MPa] σ_c,máx [MPa] |σ_c|/f_y
  pilar P-3 (compresión)        850        180           164.3           -50.3         -50.3      0.14
  tirante T-1 (tracción)       -300         20            -8.2           -32.0         -32.0      0.09

Con el signo invertido la fibra comprimida del pilar pasa de −164 a −50 MPa (la compresión máxima, que gobierna el pandeo y la clase de la sección, cae a un tercio) y el tirante aparece comprimido; |σ|máx no cambia, así que una comprobación que solo mire el máximo absoluto no lo detecta. El esquema documenta el convenio en el campo y el importador debe declararlo, no adivinarlo.
```

</details>

#### Exporting a frame to JSON Lines, re-importing with line-by-line validation and extracting the envelope per member

<details><summary>Actual output of <code>python examples/internal_forces_jsonl_export_import_and_member_envelopes.py</code></summary>

```text
Exportadas 45 estaciones en 5486 bytes de JSONL (+1 línea corrupta de prueba)

Reimportadas 45 válidas; rechazadas: [(46, ['greater_than_equal'])]

  barra  |N| máx [kN] |V_z| máx [kN] |M_z| máx [kN·m]
  P-1           420.0           25.0             50.0
  D-1            35.0          180.0            240.0
  P-2           420.0           25.0             50.0
```

</details>

#### What `InternalForces` rejects, the valid partial state and a mapping of a SAP2000 row to the schema

<details><summary>Actual output of <code>python examples/internal_forces_validation_station_negative_extra_field_and_defaults.py</code></summary>

```text
Estado parcial válido: {'member_id': 'C-1', 'station_m': 0.0, 'N_kN': 0.0, 'Vy_kN': 0.0, 'Vz_kN': 0.0, 'T_kNm': 0.0, 'My_kNm': 0.0, 'Mz_kNm': 0.0}

  estación −1 m          → 1 error(es): greater_than_equal en station_m
  campo `Fx_kN`          → 1 error(es): extra_forbidden en Fx_kN
  sin member_id          → 1 error(es): missing en member_id
  M_z como texto         → 1 error(es): float_parsing en Mz_kNm
  dos errores a la vez   → 3 error(es): greater_than_equal en station_m; float_parsing en Mz_kNm; extra_forbidden en extra

Fila de SAP2000 mapeada: {'member_id': 'V-12', 'station_m': 3.0, 'N_kN': -12.0, 'Vy_kN': 0.0, 'Vz_kN': 48.0, 'T_kNm': 0.0, 'My_kNm': 0.0, 'Mz_kNm': 72.0}
El mapeo vive en el importador (y debe declarar el convenio de signo de P); el esquema no acepta los nombres del programa de origen.
```

</details>

#### Composite material + section + forces contract: JSON Schema with `$defs`, round trip and nested rejection

<details><summary>Actual output of <code>python examples/data_contract_member_check_bundle_material_section_forces_jsonschema_defs.py</code></summary>

```text
JSON Schema de MemberCheckInput: propiedades ['member_id', 'length_m', 'material', 'section', 'forces']; $defs = ['FrameSection', 'InternalForces', 'MaterialType', 'StructuralMaterial']
Documento serializado: 996 bytes; vuelta validada igual al original: True

  x [m] M_z [kN·m]  σ = N/A + M/S [MPa]  σ/f_y
    0.0        0.0                  2.2   0.01
    1.5       81.0                147.7   0.42
    3.0      108.0                196.1   0.55
    4.5       81.0                147.7   0.42
    6.0        0.0                  2.2   0.01

Rechazo anidado: [('greater_than', 'section.Ix_mm4')]
```

</details>

### 4. Finite element helpers

#### The prismatic beam as a special case: Simpson recovers the classical 6×6 matrix to machine precision

<details><summary>Actual output of <code>python examples/fea_prismatic_beam_stiffness_recovers_closed_form_12EI_L3.py</code></summary>

```text
IPE 300, L = 6 m: EI = 17,548 kN·m², EA = 1,130,010 kN
  12EI/L³ = 974.9 kN/m   6EI/L² = 2,924.6 kN   4EI/L = 11,698.4 kN·m/rad   2EI/L = 5,849.2 kN·m/rad

  n =  2 intervalos de Simpson: error relativo máximo frente a la forma cerrada = 3.9e-17
  n = 20 intervalos de Simpson: error relativo máximo frente a la forma cerrada = 1.5e-16

Matriz 6×6 (GDL [u_i, v_i, θ_i, u_j, v_j, θ_j]):
[[ 188335.        0.        0.  -188335.        0.        0. ]
 [      0.      974.9    2924.6       0.     -974.9    2924.6]
 [      0.     2924.6   11698.4       0.    -2924.6    5849.2]
 [-188335.        0.        0.   188335.        0.        0. ]
 [      0.     -974.9   -2924.6       0.      974.9   -2924.6]
 [      0.     2924.6    5849.2       0.    -2924.6   11698.4]]

El mismo helper con EI(x) callable da la viga de sección variable: el caso prismático es la comprobación de que la integración está bien montada.
```

</details>

#### Tapered beam with linear EI: end flexibility in closed form and fourth-order convergence

<details><summary>Actual output of <code>python examples/fea_tapered_beam_linear_EI_closed_form_and_simpson_convergence.py</code></summary>

```text
Forma cerrada: D₀₀ = 0.003355 m/kN, D₀₁ = 0.000792 rad/kN, D₁₁ = 0.000237 rad/(kN·m)
Cotas prismáticas de D₀₀: EI₀ → 0.004103, 2·EI₀ → 0.002052

    n  D₀₀ Simpson  error rel.  razón
    2     0.003419    1.90e-02 
    4     0.003361    1.57e-03   12.1
    8     0.003356    1.08e-04   14.5
   16     0.003355    6.93e-06   15.6
   32     0.003355    4.36e-07   15.9
   64     0.003355    2.73e-08   16.0

Rigidez rotacional en el extremo i (K[θ_i,θ_i]): acartelada 14,222 frente a prismática EI₀ 11,699 kN·m/rad (1.22×); en j: 20,071 (1.72×): el extremo con más inercia (j) es el más rígido.
Factor de transmisión K[θ_i,θ_j]/K[θ_j,θ_j] = 0.417 (prismática: 0,500).
```

</details>

#### Rafter with end haunches: piecewise EI, rotational stiffness and carry-over factor against the prismatic beam

<details><summary>Actual output of <code>python examples/fea_haunched_rafter_piecewise_EI_stiffness_and_carry_over_factor.py</code></summary>

```text
Dintel L = 12 m, IPE 400: 4EI/L = 16,191 kN·m/rad, 2EI/L = 8,096, 12EI/L³ = 337 kN/m

                 cartela K[θi,θi] [kN·m/rad] / prismática   K[θi,θj] transmisión K[vi,vi] [kN/m] / prismática
    ninguna (prismática)              16,191         1.00      8,096       0.500             337         1.00
         2 m, canto ×2.0              28,195         1.74     17,969       0.637             641         1.90
         3 m, canto ×2.0              37,434         2.31     25,659       0.685             876         2.60
         2 m, canto ×1.5              23,243         1.44     13,739       0.591             514         1.52

La rigidez rotacional del nudo sube un 74 % con cartelas de 2 m que doblan el canto y el factor de transmisión pasa de 0,50 a 0,64: es lo que hace rentable la cartela frente a aumentar el perfil en toda la luz.
n = 240 intervalos para que el quiebro de EI(x) en x = a caiga cerca de un nodo de Simpson; con EI continuo bastan 20.
```

</details>

#### Semi-rigid joints: EN 1993-1-8 classification, Monforton and Wu fixity factor and condensed stiffness

<details><summary>Actual output of <code>python examples/fea_semi_rigid_joint_eurocode_classification_fixity_factor_table.py</code></summary>

```text
IPE 400, L = 8 m: E·I_b/L_b = 6,072 kN·m/rad; umbrales EN 1993-1-8: articulada <= 3,036, rígida >= 48,573 (arriostrado) / 151,791 (no arriostrado)

  S_j/(EI/L) S_j [kN·m/rad]      γ k_θiθi/(4EI/L) Monforton-Wu  arriostrado no arriostr.
        0.25          1,518  0.077          0.058        0.058   articulada   articulada
         0.5          3,036  0.143          0.108        0.108   articulada   articulada
           1          6,072  0.250          0.190        0.190  semirrígida  semirrígida
           2         12,143  0.400          0.312        0.313  semirrígida  semirrígida
           4         24,286  0.571          0.467        0.467  semirrígida  semirrígida
           8         48,573  0.727          0.629        0.629       rígida  semirrígida
          12         72,860  0.800          0.714        0.714       rígida  semirrígida
          25        151,791  0.893          0.836        0.836       rígida       rígida
          50        303,581  0.943          0.910        0.910       rígida       rígida
         100        607,162  0.971          0.953        0.953       rígida       rígida
         inf            inf  1.000          1.000        1.000       rígida       rígida

Una unión en el umbral «rígido» de pórtico arriostrado (S_j = 8·EI/L) conserva el 63 % de la rigidez rotacional 4EI/L de la viga; en el umbral no arriostrado (25·EI/L), el 84 %.
R va en kN·m/rad, las mismas unidades que K_b; pasar una rigidez relativa (k·L/EI) hace que todo salga articulado.
```

</details>

#### Frame assembled with the helpers: sway stiffness with rigid, semi-rigid and pinned joints against 24·EI_c/H³ and 6·EI_c/H³

<details><summary>Actual output of <code>python examples/fea_portal_frame_sway_stiffness_rigid_vs_semi_rigid_joints_assembly.py</code></summary>

```text
EI_c = 52,857 kN·m²; cotas: 24·EI_c/H³ = 10,149 kN/m, 6·EI_c/H³ = 2,537 kN/m

              dintel          S_j k = F/Δ [kN/m] Δ(100 kN) [mm] k / k_rígido
             IPE 400            ∞          5,595           17.9         1.00
             IPE 400  25·EI_b/L_b          5,215           19.2         0.93
             IPE 400   8·EI_b/L_b          4,656           21.5         0.83
             IPE 400   2·EI_b/L_b          3,637           27.5         0.65
             IPE 400 0 (articulado)          2,528           39.6         0.45
       rígido (×10⁶)            ∞          9,987           10.0         1.79

Comprobación: dintel rígido → 9,987 frente a 24·EI_c/H³ = 10,149 (98.41 %); articulado → 2,528 frente a 6·EI_c/H³ = 2,537 (99.64 %)
Una unión en el umbral «rígido» de pórtico arriostrado (8·EI_b/L_b) pierde un 17 % de rigidez al desplome y en el umbral no arriostrado (25·EI_b/L_b) un 7 %: por eso EN 1993-1-8 exige el segundo en pórticos no arriostrados.
```

</details>

## Verification

- Data contract: validation of mandatory fields, ranges (E > 0, 0 ≤ ν ≤ 0.5, station ≥ 0, C_w ≥ 0), `extra="forbid"`, type enum, round trip `model_dump` → `model_validate` and `required` of the JSON Schema for the three models (`tests/test_materials.py`, `test_sections.py`, `test_forces.py`).
- FEA: the prismatic beam is recovered to machine precision; the linear-EI beam reproduces the closed-form flexibility (D₀₀ = (4·ln 2 − 5/2)·L³/EI₀, D₀₁ = (2·ln 2 − 1)·L²/EI₀, D₁₁ = ln 2·L/EI₀) with fourth-order convergence; the end springs reproduce Monforton and Wu (1963) with equal and different springs and the rigid (4EI/L) and pinned (3EI/L) limits (`tests/test_fea_closed_form_golden.py`, `test_fea_non_prismatic.py`, `test_fea_semi_rigid.py`).
- The examples check the properties computed from dimensions against the EN 10365 and EN 10210 catalogues, the E_cm formula against EN 1992-1-1 Table 3.1, and the assembled frame against the 24·EI_c/H³ and 6·EI_c/H³ bounds.

## Limitations

- There is no section or material catalogue: the package validates what it receives, it does not fill it in.
- `FrameSection` does not distinguish class 4 sections and does not store geometry (flanges, webs); effective properties are the producer's responsibility.
- `InternalForces` is one member station; it does not model plate forces, supports or combinations (the combination identifier goes in `member_id` or in the consumer's composite model).
- `beam_stiffness_2d` is plane bending under Euler-Bernoulli assumptions (no shear deformation) with EI(x) given by the user; with piecewise EI, n must be large enough for the break to fall near a Simpson node.
- `semi_rigid_bending_stiffness` takes R in the units of K_b (kN·m/rad if K_b is in kN and m); passing a relative stiffness k·L/EI makes everything come out pinned.
- The axis conventions (x strong, M_z strong) are those of the Loadpath ecosystem and of SAP2000; other programs use others, and the mapping is the importer's job.

## Codes and references

- EN 1993-1-1:2005 §3.2.6 (E, G, ν); EN 10025-2 Table 7 (f_y by thickness); EN 1993-1-8 §5.2.2.5 (joint classification by stiffness).
- EN 1992-1-1:2004 Table 3.1 and §3.1.3 (E_cm and aggregate); EN 1991-1-1 Table A.1 (densities).
- EN 10365 and EN 10210 (section dimensions and properties, used as a check).
- Monforton, G. R. and Wu, T. S. (1963), Matrix analysis of semi-rigidly connected frames, ASCE J. Struct. Div. 89(6).
- PCA, Handbook of Frame Constants (constants for haunched members).
- Pydantic v2 and JSON Schema 2020-12.

## License

MIT. See [LICENSE](LICENSE).

---

Part of **Loadpath**, the collection of open-source structural libraries by [Jesús Murgas](https://github.com/jmurgass99).

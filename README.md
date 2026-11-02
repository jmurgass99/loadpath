# loadpath — contrato de datos estructurales (materiales, secciones, esfuerzos) en Pydantic v2 y ayudas FEA de barra

**Español** · [English](README.en.md) · [Português](README.pt.md) · [Italiano](README.it.md)

Tres modelos estrictos que viajan entre programas de cálculo, comprobadores, exportadores e interfaces: `StructuralMaterial`, `FrameSection` e `InternalForces`, con unidades SI en el nombre de cada campo, `extra="forbid"` y JSON Schema para generar tipos en otros lenguajes. Más dos ayudas de elementos finitos de barra: la matriz de rigidez 2D de una viga de sección variable (EI(x), EA(x) por Simpson) y la condensación de resortes rotacionales de extremo para nudos semirrígidos. Dependencias: `pydantic` y `numpy`.

[![CI](https://github.com/jmurgass99/loadpath/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/loadpath/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Qué problema resuelve

Entre un programa de análisis, un comprobador de secciones y un informe, los datos cruzan tres fronteras y en cada una se pierden unidades, ejes y convenios de signo: el momento fuerte se llama M3 en un sitio y M_y en otro, el axil es positivo en compresión aquí y en tracción allá, y un `E = 210` no dice si son GPa o MPa. `loadpath` fija un único formato con la unidad en el nombre del campo, los ejes documentados en los dos modelos que los comparten y validación en la entrada, de modo que un dato mal formado se rechaza con la ruta del campo en vez de propagarse como un número.

**Úsalo cuando**

- definas la entrada o la salida de una herramienta de cálculo (API REST, CLI, fichero) y quieras que materiales, secciones y esfuerzos tengan un único formato validado;
- generes tipos TypeScript o documentación de API a partir del JSON Schema de los modelos;
- importes resultados de SAP2000, ETABS u otro programa y necesites un sitio donde declarar el mapeo de ejes y el convenio de signo;
- necesites la matriz de rigidez de una viga acartelada o con cartelas (EI(x) a trozos) o la rigidez condensada de una viga con nudos semirrígidos para montarla en un pórtico.

**No lo uses para**

- catálogos de perfiles (no incluye tablas de IPE, HEB o W; los ejemplos muestran cómo calcular las propiedades desde las dimensiones y contrastarlas);
- comprobaciones de norma: no hay resistencias de diseño, pandeo ni clasificación de secciones, solo el contrato de datos y las ayudas de rigidez;
- análisis de estructuras completas: `fea` da matrices de elemento, no ensambla ni resuelve (el ejemplo del pórtico lo hace en 40 líneas con numpy para enseñar cómo);
- secciones compuestas, no simétricas o con alabeo restringido: `FrameSection` describe propiedades, no geometría.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/loadpath.git
```

Para desarrollo: `git clone`, `pip install -e ".[test]"`, `pytest -q` (8 ficheros de tests). En Windows, si la consola no es UTF-8, ejecuta los ejemplos con `python -X utf8 examples/<nombre>.py`.

## Capacidades

| Capacidad | Módulos | Norma o referencia | Casos de uso |
|---|---|---|---|
| Materiales: `StructuralMaterial` con E, ν, ρ obligatorios y resistencias opcionales según el tipo (acero, hormigón, conformado en frío, aluminio, madera, fábrica); validación de rangos; JSON Schema | `materials` | EN 1993-1-1 §3.2.6; EN 10025-2 Tabla 7; EN 1992-1-1 Tabla 3.1 y §3.1.3; EN 14080; EN 1999-1-1 | [5 casos](#1-materiales) |
| Secciones: `FrameSection` con A, I_x, I_y, J obligatorios y C_w, módulos elásticos y plásticos, dimensiones, clase de sección y propiedades eficaces de Clase 4 opcionales; alias de eje fuerte y débil; mapa de ejes con los esfuerzos | `sections` | EN 10365 / EN 10210 (contraste de catálogo); convenio M3 fuerte / M2 débil de SAP2000 | [5 casos](#2-secciones) |
| Esfuerzos y contrato de datos: `InternalForces` por estación con tracción positiva y componentes a cero por defecto; JSON Lines; modelos compuestos con `$defs`; mapeo desde SAP2000 | `forces`, Pydantic v2 | Convenio de ejes locales 1-2-3 | [5 casos](#3-esfuerzos-y-contrato-de-datos) |
| Ayudas FEA: rigidez 6×6 de viga 2D con EI(x) y EA(x) por Simpson (flexibilidad del voladizo), resortes rotacionales de extremo condensados (Monforton y Wu) | `fea.non_prismatic`, `fea.semi_rigid` | Monforton y Wu (1963); EN 1993-1-8 §5.2.2.5 (clasificación de uniones); tablas PCA de constantes de pórticos | [5 casos](#4-ayudas-de-elementos-finitos) |

Los 20 scripts de `examples/` se ejecutaron en un entorno limpio antes de publicarse; su salida está en `examples/output/` y es la que se reproduce aquí.

## Casos de uso

### 1. Materiales

#### Catálogo de materiales del proyecto con valores de norma: S355, A992, C30/37, GL24h, aluminio 6061-T6 y fábrica

<details><summary>Salida real de <code>python examples/material_catalog_steel_concrete_timber_aluminum_from_codes.py</code></summary>

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

#### Qué rechaza el esquema y por qué: campo sin unidad, E negativo, ν > 0,5, tipo desconocido, texto en un número

<details><summary>Salida real de <code>python examples/material_validation_rejects_missing_units_and_out_of_range.py</code></summary>

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

#### Del JSON Schema a una interfaz TypeScript con los rangos y las unidades en los comentarios

<details><summary>Salida real de <code>python examples/material_json_schema_to_typescript_interface.py</code></summary>

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

#### Hormigones C20/25 a C50/60 con E_cm = 22·(f_cm/10)^0,3 GPa (EN 1992-1-1 Tabla 3.1) y el factor del árido

<details><summary>Salida real de <code>python examples/material_concrete_Ecm_from_fck_EN1992_table_3_1.py</code></summary>

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

#### Aceros S235 a S460 con el límite elástico que depende del espesor (EN 10025-2 Tabla 7)

<details><summary>Salida real de <code>python examples/material_steel_grades_EN10025_thickness_dependent_fy.py</code></summary>

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

### 2. Secciones

#### Propiedades de un perfil en I desde sus dimensiones y contraste con el catálogo: IPE 300 y HEB 300

El área con la corrección de acuerdos (4 − π)·r² sale exacta; I_x y W_pl quedan un 4 % por debajo del catálogo y la torsión un 20–25 %: I_t se toma del catálogo.

<details><summary>Salida real de <code>python examples/section_properties_from_I_shape_dimensions_IPE300_HEB300_vs_catalog.py</code></summary>

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

#### Tubos RHS 200×100×8 y CHS 219,1×8 desde sus dimensiones frente a EN 10210 (Bredt para la torsión del RHS)

<details><summary>Salida real de <code>python examples/section_hollow_sections_RHS_CHS_from_dimensions_vs_EN10210.py</code></summary>

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

#### Qué momento va con qué inercia: M_z (fuerte) con I_x, M_y (débil) con I_y, y el error de cruzarlos

<details><summary>Salida real de <code>python examples/section_strong_weak_axis_mapping_to_internal_forces_bending_stress.py</code></summary>

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

#### Mínimo obligatorio, opcionales en None y rechazos del esquema de sección

<details><summary>Salida real de <code>python examples/section_validation_optional_fields_and_json_schema_required.py</code></summary>

```text
Sección mínima: {'name': 'barra genérica', 'A_mm2': 5000.0, 'Ix_mm4': 80000000.0, 'Iy_mm4': 6000000.0, 'J_mm4': 200000.0}
  opcionales en None: ['Cw_mm6', 'Zx_mm3', 'Zy_mm3', 'Sx_mm3', 'Sy_mm3', 'depth_mm', 'width_mm', 'section_class', 'A_eff_mm2', 'Ix_eff_mm4', 'Iy_eff_mm4', 'Sx_eff_mm3', 'Sy_eff_mm3']
Sección laminada con propiedades brutas: W14X90, 12 de 18 campos; sin rellenar: ['section_class', 'A_eff_mm2', 'Ix_eff_mm4', 'Iy_eff_mm4', 'Sx_eff_mm3', 'Sy_eff_mm3']

JSON Schema: obligatorias ['name', 'A_mm2', 'Ix_mm4', 'Iy_mm4', 'J_mm4']; opcionales ['Cw_mm6', 'Zx_mm3', 'Zy_mm3', 'Sx_mm3', 'Sy_mm3', 'depth_mm', 'width_mm', 'section_class', 'A_eff_mm2', 'Ix_eff_mm4', 'Iy_eff_mm4', 'Sx_eff_mm3', 'Sy_eff_mm3']

  sin J          → missing en J_mm4
  área 0         → greater_than en A_mm2
  C_w negativo   → greater_than_equal en Cw_mm6
  campo `peso`   → extra_forbidden en peso
  I_x como texto → float_parsing en Ix_mm4

C_w = 0 sí se admite (tubos cerrados); lo que se rechaza es el valor negativo.
```

</details>

#### Peso por metro, radios de giro y esbeltez de pilar derivados de los campos del esquema

<details><summary>Salida real de <code>python examples/section_weight_radius_of_gyration_and_slenderness_table.py</code></summary>

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

### 3. Esfuerzos y contrato de datos

#### Viga biapoyada con carga uniforme: 13 estaciones como lista de `InternalForces` y envolvente frente a q·L/2 y q·L²/8

<details><summary>Salida real de <code>python examples/internal_forces_simply_supported_beam_stations_udl_envelope.py</code></summary>

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

#### Convenio de signo del axil (tracción positiva): pilar y tirante, tensión en las fibras y qué pasa si el importador lo invierte

<details><summary>Salida real de <code>python examples/internal_forces_sign_convention_tension_positive_column_combined_stress.py</code></summary>

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

#### Exportar un pórtico a JSON Lines, reimportar validando línea a línea y sacar la envolvente por barra

<details><summary>Salida real de <code>python examples/internal_forces_jsonl_export_import_and_member_envelopes.py</code></summary>

```text
Exportadas 45 estaciones en 5486 bytes de JSONL (+1 línea corrupta de prueba)

Reimportadas 45 válidas; rechazadas: [(46, ['greater_than_equal'])]

  barra  |N| máx [kN] |V_z| máx [kN] |M_z| máx [kN·m]
  P-1           420.0           25.0             50.0
  D-1            35.0          180.0            240.0
  P-2           420.0           25.0             50.0
```

</details>

#### Qué rechaza `InternalForces`, el estado parcial válido y un mapeo de fila de SAP2000 al esquema

<details><summary>Salida real de <code>python examples/internal_forces_validation_station_negative_extra_field_and_defaults.py</code></summary>

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

#### Contrato compuesto material + sección + esfuerzos: JSON Schema con `$defs`, ida y vuelta y rechazo anidado

<details><summary>Salida real de <code>python examples/data_contract_member_check_bundle_material_section_forces_jsonschema_defs.py</code></summary>

```text
JSON Schema de MemberCheckInput: propiedades ['member_id', 'length_m', 'material', 'section', 'forces']; $defs = ['FrameSection', 'InternalForces', 'MaterialType', 'StructuralMaterial']
Documento serializado: 1106 bytes; vuelta validada igual al original: True

  x [m] M_z [kN·m]  σ = N/A + M/S [MPa]  σ/f_y
    0.0        0.0                  2.2   0.01
    1.5       81.0                147.7   0.42
    3.0      108.0                196.1   0.55
    4.5       81.0                147.7   0.42
    6.0        0.0                  2.2   0.01

Rechazo anidado: [('greater_than', 'section.Ix_mm4')]
```

</details>

### 4. Ayudas de elementos finitos

#### La viga prismática como caso particular: Simpson recupera la matriz 6×6 clásica a precisión de máquina

<details><summary>Salida real de <code>python examples/fea_prismatic_beam_stiffness_recovers_closed_form_12EI_L3.py</code></summary>

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

#### Viga acartelada con EI lineal: flexibilidad del extremo en forma cerrada y convergencia de orden 4

<details><summary>Salida real de <code>python examples/fea_tapered_beam_linear_EI_closed_form_and_simpson_convergence.py</code></summary>

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

#### Dintel con cartelas en los extremos: EI a trozos, rigidez rotacional y factor de transmisión frente a la viga prismática

<details><summary>Salida real de <code>python examples/fea_haunched_rafter_piecewise_EI_stiffness_and_carry_over_factor.py</code></summary>

```text
Dintel L = 12 m, IPE 400: 4EI/L = 16,191 kN·m/rad, 2EI/L = 8,096, 12EI/L³ = 337 kN/m

                 cartela K[θi,θi] [kN·m/rad] / prismática   K[θi,θj] transmisión K[vi,vi] [kN/m] / prismática
    ninguna (prismática)              16,191         1.00      8,096       0.500             337         1.00
         2 m, canto ×2.0              28,195         1.74     17,969       0.637             641         1.90
         3 m, canto ×2.0              37,434         2.31     25,659       0.685             876         2.60
         2 m, canto ×1.5              23,243         1.44     13,739       0.591             514         1.52

La rigidez rotacional del nudo sube un 74 % con cartelas de 2 m que doblan el canto y el factor de transmisión pasa de 0.50 a 0.64: es lo que hace rentable la cartela frente a aumentar el perfil en toda la luz.
Quiebros de EI(x) en x = 2 y 10 m, error máximo frente a Simpson por tramos con n = 400: n = 20 con breakpoints_x 4.1e-04; n = 240 sin ellos (la tabla) 4.5e-08; n = 20 sin ellos 3.3e-03.
```

</details>

#### Nudos semirrígidos: clasificación EN 1993-1-8, factor de fijación de Monforton y Wu y rigidez condensada

<details><summary>Salida real de <code>python examples/fea_semi_rigid_joint_eurocode_classification_fixity_factor_table.py</code></summary>

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

#### Pórtico ensamblado con los helpers: rigidez al desplome con nudos rígidos, semirrígidos y articulados frente a 24·EI_c/H³ y 6·EI_c/H³

<details><summary>Salida real de <code>python examples/fea_portal_frame_sway_stiffness_rigid_vs_semi_rigid_joints_assembly.py</code></summary>

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

## Verificación

- Contrato de datos: validación de campos obligatorios, rangos (E > 0, 0 ≤ ν ≤ 0,5, estación ≥ 0, C_w ≥ 0), `extra="forbid"`, enum de tipos, ida y vuelta `model_dump` → `model_validate` y `required` del JSON Schema para los tres modelos (`tests/test_materials.py`, `test_sections.py`, `test_forces.py`).
- FEA: la viga prismática se recupera a precisión de máquina; la viga de EI lineal reproduce la flexibilidad en forma cerrada (D₀₀ = (4·ln 2 − 5/2)·L³/EI₀, D₀₁ = (2·ln 2 − 1)·L²/EI₀, D₁₁ = ln 2·L/EI₀) con convergencia de orden 4; los resortes de extremo reproducen Monforton y Wu (1963) con resortes iguales y distintos y los límites rígido (4EI/L) y articulado (3EI/L) (`tests/test_fea_closed_form_golden.py`, `test_fea_non_prismatic.py`, `test_fea_semi_rigid.py`).
- Los ejemplos contrastan las propiedades calculadas desde dimensiones con los catálogos EN 10365 y EN 10210, la fórmula de E_cm con la Tabla 3.1 de EN 1992-1-1 y el pórtico ensamblado con las cotas 24·EI_c/H³ y 6·EI_c/H³.

## Limitaciones

- No hay catálogo de perfiles ni de materiales: el paquete valida lo que recibe, no lo rellena.
- `FrameSection` no distingue secciones de clase 4 ni almacena geometría (alas, almas); las propiedades eficaces son responsabilidad del productor.
- `InternalForces` es una estación de barra; no modela esfuerzos de placa, apoyos ni combinaciones (el identificador de combinación va en `member_id` o en el modelo compuesto del consumidor).
- `beam_stiffness_2d` es flexión plana con hipótesis de Euler-Bernoulli (sin deformación por cortante) y EI(x) dado por el usuario; con EI a trozos, pasa los quiebros en `breakpoints_x` (Simpson por tramos) o usa un n suficiente para que caigan cerca de un nodo de Simpson.
- `semi_rigid_bending_stiffness` recibe R en las unidades de K_b (kN·m/rad si K_b está en kN y m); pasar una rigidez relativa k·L/EI hace que todo salga articulado.
- Los convenios de ejes (x fuerte, M_z fuerte) son los del ecosistema Loadpath y de SAP2000; otros programas usan otros y el mapeo es tarea del importador.

## Normas y referencias

- EN 1993-1-1:2005 §3.2.6 (E, G, ν); EN 10025-2 Tabla 7 (f_y por espesor); EN 1993-1-8 §5.2.2.5 (clasificación de uniones por rigidez).
- EN 1992-1-1:2004 Tabla 3.1 y §3.1.3 (E_cm y árido); EN 1991-1-1 Tabla A.1 (densidades).
- EN 10365 y EN 10210 (dimensiones y propiedades de perfiles, usados como contraste).
- Monforton, G. R. y Wu, T. S. (1963), Matrix analysis of semi-rigidly connected frames, ASCE J. Struct. Div. 89(6).
- PCA, Handbook of Frame Constants (constantes de barras acarteladas).
- Pydantic v2 y JSON Schema 2020-12.

## Licencia

MIT. Consulta [LICENSE](LICENSE).

---

Parte de **Loadpath**, la colección de librerías estructurales de código abierto de [Jesús Murgas](https://github.com/jmurgass99).

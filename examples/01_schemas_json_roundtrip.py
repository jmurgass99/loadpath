"""Esquemas estructurales como contrato de datos: validación estricta y JSON.

Se crean un material, una sección y esfuerzos internos, se serializan a JSON
(lo que viajaría entre un programa de cálculo y un informe o un frontend), se
vuelven a cargar y se muestra cómo el esquema rechaza campos desconocidos y
unidades implícitas.

Ejecutar:  python examples/01_schemas_json_roundtrip.py
"""
import json

from pydantic import ValidationError

from loadpath import UNIT_SYSTEM, FrameSection, InternalForces, StructuralMaterial


def main() -> None:
    print(f"Convención de unidades: {UNIT_SYSTEM}\n")

    steel = StructuralMaterial(name="S355", material_type="steel", E_MPa=210_000, poisson=0.3,
                               density_kg_m3=7850, Fy_MPa=355, Fu_MPa=490)
    ipe = FrameSection(name="IPE 300", A_mm2=5380, Ix_mm4=8.356e7, Iy_mm4=6.04e6, J_mm4=2.01e5)
    forces = [
        InternalForces(member_id="V-12", station_m=0.0, N_kN=-12.0, Vz_kN=48.0, My_kNm=0.0),
        InternalForces(member_id="V-12", station_m=3.0, N_kN=-12.0, Vz_kN=0.0, My_kNm=72.0),
        InternalForces(member_id="V-12", station_m=6.0, N_kN=-12.0, Vz_kN=-48.0, My_kNm=0.0),
    ]

    payload = {"material": steel.model_dump(), "section": ipe.model_dump(),
               "forces": [f.model_dump() for f in forces]}
    text = json.dumps(payload, indent=1)
    print(f"JSON serializado: {len(text)} caracteres. Primeras líneas:")
    print("\n".join(text.splitlines()[:8]), "\n  ...")

    # Vuelta: el mismo JSON reconstruye objetos validados
    back = json.loads(text)
    m2 = StructuralMaterial.model_validate(back["material"])
    s2 = FrameSection.model_validate(back["section"])
    f2 = [InternalForces.model_validate(f) for f in back["forces"]]
    print(f"\nRecargado: {m2.name}, {s2.name}, {len(f2)} estaciones; M_y máximo = "
          f"{max(f.My_kNm for f in f2):.1f} kN·m")

    # Rechazo de campos desconocidos (extra='forbid'): evita unidades implícitas
    try:
        FrameSection(name="X", A_mm2=1000, Ix_mm4=1e6, Iy_mm4=1e6, J_mm4=1e4, area=1000)
    except ValidationError as e:
        print(f"\nCampo 'area' (sin unidad) rechazado: {e.errors()[0]['type']} → {e.errors()[0]['loc']}")

    # Esquema JSON para generar tipos en otros lenguajes
    schema = FrameSection.model_json_schema()
    print(f"\nJSON Schema de FrameSection: {len(schema['properties'])} propiedades, "
          f"obligatorias: {schema.get('required')}")


if __name__ == "__main__":
    main()

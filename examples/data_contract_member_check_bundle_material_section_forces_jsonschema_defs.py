"""Un contrato de datos compuesto: material + sección + esfuerzos en un solo modelo con JSON Schema y $defs.

`MemberCheckInput` agrupa un `StructuralMaterial`, una `FrameSection` y la lista de
`InternalForces` de una barra, con `extra="forbid"` heredado. Es lo que una API de comprobación
recibiría en un POST: Pydantic valida los tres niveles de una vez, el JSON Schema publica los
tres modelos en `$defs` y el consumidor (comprobador, informe, frontend) tiene un único
documento. Para cerrar, una utilización elástica σ/f_y por estación.

Ejecutar:  python examples/data_contract_member_check_bundle_material_section_forces_jsonschema_defs.py
"""
import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from loadpath import FrameSection, InternalForces, StructuralMaterial


class MemberCheckInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    member_id: str
    length_m: float = Field(gt=0)
    material: StructuralMaterial
    section: FrameSection
    forces: list[InternalForces] = Field(min_length=1)


def main() -> None:
    bundle = MemberCheckInput(
        member_id="V-12", length_m=6.0,
        material=StructuralMaterial(name="S355", material_type="steel", E_MPa=210_000, poisson=0.3, density_kg_m3=7850, Fy_MPa=355, Fu_MPa=490),
        section=FrameSection(name="IPE 300", A_mm2=5381, Ix_mm4=8.356e7, Iy_mm4=6.04e6, J_mm4=2.01e5, Sx_mm3=557e3, Zx_mm3=628e3),
        forces=[InternalForces(member_id="V-12", station_m=x, N_kN=-12.0, Vz_kN=24 * (3 - x), Mz_kNm=12 * x * (6 - x)) for x in (0.0, 1.5, 3.0, 4.5, 6.0)],
    )
    schema = MemberCheckInput.model_json_schema()
    print(f"JSON Schema de MemberCheckInput: propiedades {list(schema['properties'])}; $defs = {sorted(schema['$defs'])}")
    texto = bundle.model_dump_json()
    print(f"Documento serializado: {len(texto)} bytes; vuelta validada igual al original: {MemberCheckInput.model_validate_json(texto) == bundle}\n")
    print(f"  {'x [m]':>5} {'M_z [kN·m]':>10} {'σ = N/A + M/S [MPa]':>20} {'σ/f_y':>6}")
    for f in bundle.forces:
        s = abs(f.N_kN) * 1e3 / bundle.section.A_mm2 + abs(f.Mz_kNm) * 1e6 / bundle.section.Sx_mm3
        print(f"  {f.station_m:5.1f} {f.Mz_kNm:10.1f} {s:20.1f} {s / bundle.material.Fy_MPa:6.2f}")
    malo = json.loads(texto)
    malo["forces"][2]["Mz_kNm"] = "108"   # texto numérico: pydantic lo acepta en modo lax
    malo["section"]["Ix_mm4"] = -1        # negativo anidado: se rechaza con la ruta completa
    try:
        MemberCheckInput.model_validate(malo)
    except ValidationError as e:
        print("\nRechazo anidado:", [(x["type"], ".".join(str(p) for p in x["loc"])) for x in e.errors()])


if __name__ == "__main__":
    main()

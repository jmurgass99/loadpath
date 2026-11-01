"""Mínimo obligatorio de una sección, campos opcionales en None y lo que el esquema rechaza.

`FrameSection` exige lo que cualquier análisis elástico de barras necesita (A, I_x, I_y, J) y
deja opcionales alabeo, módulos y dimensiones. Se muestra una sección mínima, una completa, el
`required` del JSON Schema, y cuatro rechazos: sin J, área nula, C_w negativo y un campo `peso`
que no existe (unidades implícitas).

Ejecutar:  python examples/section_validation_optional_fields_and_json_schema_required.py
"""
from pydantic import ValidationError

from loadpath import FrameSection


def main() -> None:
    minima = FrameSection(name="barra genérica", A_mm2=5000, Ix_mm4=8e7, Iy_mm4=6e6, J_mm4=2e5)
    print("Sección mínima:", {k: v for k, v in minima.model_dump().items() if v is not None})
    print("  opcionales en None:", [k for k, v in minima.model_dump().items() if v is None])
    completa = FrameSection(name="W14X90", A_mm2=17100, Ix_mm4=4.16e8, Iy_mm4=1.51e8, J_mm4=4.16e6, Cw_mm6=6.78e12,
                            Zx_mm3=2.59e6, Sx_mm3=2.33e6, Zy_mm3=1.22e6, Sy_mm3=8.19e5, depth_mm=356, width_mm=369)
    print(f"Sección completa: {completa.name}, {sum(v is not None for v in completa.model_dump().values())} de {len(completa.model_dump())} campos")
    schema = FrameSection.model_json_schema()
    print(f"\nJSON Schema: obligatorias {schema['required']}; opcionales {[k for k in schema['properties'] if k not in schema['required']]}")
    casos = [
        ("sin J", dict(name="x", A_mm2=1000, Ix_mm4=1e6, Iy_mm4=1e6)),
        ("área 0", dict(name="x", A_mm2=0, Ix_mm4=1e6, Iy_mm4=1e6, J_mm4=1e4)),
        ("C_w negativo", dict(name="x", A_mm2=1000, Ix_mm4=1e6, Iy_mm4=1e6, J_mm4=1e4, Cw_mm6=-5)),
        ("campo `peso`", dict(name="x", A_mm2=1000, Ix_mm4=1e6, Iy_mm4=1e6, J_mm4=1e4, peso="pesado")),
        ("I_x como texto", dict(name="x", A_mm2=1000, Ix_mm4="grande", Iy_mm4=1e6, J_mm4=1e4)),
    ]
    print()
    for titulo, datos in casos:
        try:
            FrameSection(**datos)
        except ValidationError as e:
            print(f"  {titulo:14} → " + "; ".join(f"{x['type']} en {'.'.join(str(p) for p in x['loc'])}" for x in e.errors()))
    print("\nC_w = 0 sí se admite (tubos cerrados); lo que se rechaza es el valor negativo.")


if __name__ == "__main__":
    main()

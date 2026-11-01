"""Qué rechaza el esquema de material y por qué: campos sin unidad, rangos físicos y tipos desconocidos.

Siete entradas que un programa de cálculo o un formulario podrían producir y que
`StructuralMaterial` rechaza con `ValidationError` antes de que lleguen a un solver:
E sin sufijo de unidad, E negativo, ν > 0,5, densidad cero, tipo de material inventado, F_y
como texto y la ausencia de E. Se imprime el tipo de error y la ruta del campo, que es lo que
un frontend muestra junto al campo.

Ejecutar:  python examples/material_validation_rejects_missing_units_and_out_of_range.py
"""
from pydantic import ValidationError

from loadpath import StructuralMaterial

BASE = dict(name="S275", material_type="steel", E_MPa=210_000, poisson=0.3, density_kg_m3=7850)

CASOS = [
    ("E sin unidad (campo `E`)", {**BASE, "E": 210_000}),
    ("E_MPa negativo", {**BASE, "E_MPa": -210_000}),
    ("ν = 0,7 (> 0,5)", {**BASE, "poisson": 0.7}),
    ("densidad 0", {**BASE, "density_kg_m3": 0}),
    ("tipo `adamantium`", {**BASE, "material_type": "adamantium"}),
    ("F_y como texto", {**BASE, "Fy_MPa": "doscientos"}),
    ("falta E_MPa", {k: v for k, v in BASE.items() if k != "E_MPa"}),
]


def main() -> None:
    ok = StructuralMaterial(**BASE)
    print(f"Válido: {ok.name} E = {ok.E_MPa:.0f} MPa\n")
    print(f"  {'caso':28} {'errores':>7}  tipo → campo")
    for titulo, datos in CASOS:
        try:
            StructuralMaterial(**datos)
            print(f"  {titulo:28} {'0':>7}  ACEPTADO (no debería)")
        except ValidationError as e:
            errs = e.errors()
            resumen = "; ".join(f"{x['type']} → {'.'.join(str(p) for p in x['loc']) or '(raíz)'}" for x in errs)
            print(f"  {titulo:28} {len(errs):7d}  {resumen}")
    print("\n`extra='forbid'` convierte un campo sin unidad en un error en vez de en un número que viaja sin que nadie sepa si es MPa o kPa.")


if __name__ == "__main__":
    main()

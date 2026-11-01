"""Catálogo de materiales del proyecto con valores de norma y el esquema como único formato.

Seis materiales habituales en una estructura mixta, cada uno con su norma de origen:
S355 (EN 10025-2, E = 210 000 MPa según EN 1993-1-1 §3.2.6), A992 (ASTM, E = 200 000 MPa),
C30/37 (EN 1992-1-1 Tabla 3.1: E_cm = 33 GPa, f_ck = 30), GL24h (EN 14080: E_0,mean = 11 500 MPa),
aluminio 6061-T6 (EN 1999-1-1: E = 70 000, f_o = 240) y fábrica de ladrillo. Las resistencias
que no aplican quedan en None, no en cero; el amortiguamiento es opcional.

Ejecutar:  python examples/material_catalog_steel_concrete_timber_aluminum_from_codes.py
"""
from loadpath import MaterialType, StructuralMaterial

CATALOGO = [
    StructuralMaterial(name="S355 (EN 10025-2)", material_type="steel", E_MPa=210_000, poisson=0.30,
                       density_kg_m3=7850, Fy_MPa=355, Fu_MPa=490, damping_ratio=0.02),
    StructuralMaterial(name="A992 (ASTM)", material_type="steel", E_MPa=200_000, poisson=0.30,
                       density_kg_m3=7850, Fy_MPa=345, Fu_MPa=450, damping_ratio=0.02),
    StructuralMaterial(name="C30/37 (EN 1992-1-1)", material_type="concrete", E_MPa=33_000, poisson=0.20,
                       density_kg_m3=2500, fc_MPa=30, damping_ratio=0.05),
    StructuralMaterial(name="GL24h (EN 14080)", material_type="timber", E_MPa=11_500, poisson=0.40,
                       density_kg_m3=420, damping_ratio=0.01),
    StructuralMaterial(name="EN AW-6061 T6 (EN 1999-1-1)", material_type="aluminum", E_MPa=70_000, poisson=0.33,
                       density_kg_m3=2700, Fy_MPa=240, Fu_MPa=260),
    StructuralMaterial(name="Ladrillo macizo M10 (EN 1996-1-1)", material_type="masonry", E_MPa=5_000, poisson=0.20,
                       density_kg_m3=1800, fc_MPa=5.0),
]


def main() -> None:
    print(f"Tipos admitidos: {[t.value for t in MaterialType]}\n")
    print(f"  {'material':34} {'tipo':18} {'E [MPa]':>8} {'ν':>5} {'ρ [kg/m³]':>9} {'F_y':>6} {'F_u':>6} {'f_c':>6} {'ξ':>5}")
    for m in CATALOGO:
        fmt = lambda v: f"{v:6.0f}" if v is not None else f"{'—':>6}"  # noqa: E731
        xi = f"{m.damping_ratio:5.2f}" if m.damping_ratio is not None else f"{'—':>5}"
        print(f"  {m.name:34} {m.material_type.value:18} {m.E_MPa:8.0f} {m.poisson:5.2f} {m.density_kg_m3:9.0f} {fmt(m.Fy_MPa)} {fmt(m.Fu_MPa)} {fmt(m.fc_MPa)} {xi}")
    acero = CATALOGO[0]
    print(f"\nMódulo de cortante del S355: G = E/(2·(1+ν)) = {acero.E_MPa / (2 * (1 + acero.poisson)):.0f} MPa (EN 1993-1-1: 81 000)")
    print(f"Peso propio del S355: {acero.density_kg_m3 * 9.80665 / 1000:.2f} kN/m³; del C30/37: {CATALOGO[2].density_kg_m3 * 9.80665 / 1000:.2f} kN/m³")
    print("\nUn consumidor comprueba con `material_type` qué resistencia leer: Fy/Fu en metales, fc en hormigón y fábrica; None es «no aplica», no «cero».")


if __name__ == "__main__":
    main()

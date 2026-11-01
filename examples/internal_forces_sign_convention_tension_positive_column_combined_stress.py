"""Convenio de signo del axil (tracción positiva) y tensión combinada N/A + M/S en un pilar y en un tirante.

El esquema fija N_kN > 0 = tracción. Un pilar HEB 300 S355 con N = −850 kN (compresión) y
M_z = 180 kN·m, y un tirante con N = +300 kN y M_z = 20 kN·m. Se calculan las tensiones en las
dos fibras extremas y se enseña el error de leer el axil con el signo de la reacción (SAP2000
devuelve P negativo en compresión, pero otros programas al revés): con el signo cambiado, el
pilar «mejora» y el tirante «empeora».

Ejecutar:  python examples/internal_forces_sign_convention_tension_positive_column_combined_stress.py
"""
from loadpath import FrameSection, InternalForces, StructuralMaterial

HEB300 = FrameSection(name="HEB 300", A_mm2=14910, Ix_mm4=2.517e8, Iy_mm4=8.563e7, J_mm4=1.85e6, Sx_mm3=1678e3, Zx_mm3=1869e3)
S355 = StructuralMaterial(name="S355", material_type="steel", E_MPa=210_000, poisson=0.3, density_kg_m3=7850, Fy_MPa=355)


def fibras(f: InternalForces, s: FrameSection) -> tuple[float, float]:
    sN = f.N_kN * 1e3 / s.A_mm2
    sM = f.Mz_kNm * 1e6 / s.Sx_mm3
    return sN + sM, sN - sM


def main() -> None:
    casos = [
        ("pilar P-3 (compresión)", InternalForces(member_id="P-3", station_m=0.0, N_kN=-850.0, Mz_kNm=180.0)),
        ("tirante T-1 (tracción)", InternalForces(member_id="T-1", station_m=2.0, N_kN=300.0, Mz_kNm=20.0)),
    ]
    cab = f"  {'barra':24} {'N [kN]':>8} {'M_z [kN·m]':>10} {'σ fibra 1 [MPa]':>15} {'σ fibra 2 [MPa]':>15} {'σ_c,máx [MPa]':>13} {'|σ_c|/f_y':>9}"
    print(cab)
    for nombre, f in casos:
        s1, s2 = fibras(f, HEB300)
        sc = min(s1, s2, 0.0)
        print(f"  {nombre:24} {f.N_kN:8.0f} {f.Mz_kNm:10.0f} {s1:15.1f} {s2:15.1f} {sc:13.1f} {abs(sc) / S355.Fy_MPa:9.2f}")
    print("\nCon el signo del axil invertido al importar (error típico entre programas):")
    print(cab)
    for nombre, f in casos:
        g = f.model_copy(update={"N_kN": -f.N_kN})
        s1, s2 = fibras(g, HEB300)
        sc = min(s1, s2, 0.0)
        print(f"  {nombre:24} {g.N_kN:8.0f} {g.Mz_kNm:10.0f} {s1:15.1f} {s2:15.1f} {sc:13.1f} {abs(sc) / S355.Fy_MPa:9.2f}")
    print("\nCon el signo invertido la fibra comprimida del pilar pasa de −164 a −50 MPa (la compresión máxima, que gobierna el pandeo y la clase de la sección, "
          "cae a un tercio) y el tirante aparece comprimido; |σ|máx no cambia, así que una comprobación que solo mire el máximo absoluto no lo detecta. "
          "El esquema documenta el convenio en el campo y el importador debe declararlo, no adivinarlo.")


if __name__ == "__main__":
    main()

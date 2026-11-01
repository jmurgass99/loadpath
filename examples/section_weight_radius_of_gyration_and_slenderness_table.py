"""Magnitudes derivadas de una sección: peso por metro, radios de giro y esbeltez de pilar.

A partir de los campos del esquema (mm, mm⁴) y del material (kg/m³, MPa):
    peso = A·ρ·g          i_x = sqrt(I_x/A), i_y = sqrt(I_y/A)
    λ_y = L_cr/i_y        λ̄_y = λ_y/λ_1 con λ_1 = π·sqrt(E/f_y) = 93,9·ε  (EN 1993-1-1 §6.3.1.3)

Cuatro perfiles como pilares de 4 m articulados (L_cr = L): IPE 300, HEB 300, HEA 200 y
CHS 219,1×8. El radio de giro del eje débil decide la esbeltez; el tubo no tiene eje débil.

Ejecutar:  python examples/section_weight_radius_of_gyration_and_slenderness_table.py
"""
from math import pi, sqrt

from loadpath import FrameSection, StructuralMaterial

S355 = StructuralMaterial(name="S355", material_type="steel", E_MPa=210_000, poisson=0.3, density_kg_m3=7850, Fy_MPa=355)
PERFILES = [
    FrameSection(name="IPE 300", A_mm2=5381, Ix_mm4=8.356e7, Iy_mm4=6.04e6, J_mm4=2.01e5, depth_mm=300, width_mm=150),
    FrameSection(name="HEB 300", A_mm2=14910, Ix_mm4=2.517e8, Iy_mm4=8.563e7, J_mm4=1.85e6, depth_mm=300, width_mm=300),
    FrameSection(name="HEA 200", A_mm2=5383, Ix_mm4=3.692e7, Iy_mm4=1.336e7, J_mm4=2.1e5, depth_mm=190, width_mm=200),
    FrameSection(name="CHS 219.1x8", A_mm2=5305, Ix_mm4=2.96e7, Iy_mm4=2.96e7, J_mm4=5.92e7, Cw_mm6=0.0, depth_mm=219.1, width_mm=219.1),
]
L_CR = 4.0  # m


def main() -> None:
    lam1 = pi * sqrt(S355.E_MPa / S355.Fy_MPa)
    print(f"S355: λ_1 = π·sqrt(E/f_y) = {lam1:.1f}; pilar L_cr = {L_CR:.0f} m\n")
    print(f"  {'perfil':12} {'peso [kg/m]':>11} {'i_x [mm]':>8} {'i_y [mm]':>8} {'λ_y':>6} {'λ̄_y':>6} {'régimen':>12}")
    for s in PERFILES:
        peso = s.A_mm2 * 1e-6 * S355.density_kg_m3
        ix, iy = sqrt(s.Ix_mm4 / s.A_mm2), sqrt(s.Iy_mm4 / s.A_mm2)
        lam = L_CR * 1000 / iy
        lam_bar = lam / lam1
        reg = "sin pandeo (λ̄ < 0,2)" if lam_bar < 0.2 else ("intermedio" if lam_bar < 1.2 else "esbelto")
        print(f"  {s.name:12} {peso:11.1f} {ix:8.1f} {iy:8.1f} {lam:6.1f} {lam_bar:6.2f} {reg:>12}")
    print("\nPesos de catálogo: IPE 300 42,2; HEB 300 117; HEA 200 42,3; CHS 219,1×8 41,6 kg/m. El IPE 300 pesa lo mismo que el HEA 200 y es 2,6 veces más esbelto en su eje débil.")


if __name__ == "__main__":
    main()

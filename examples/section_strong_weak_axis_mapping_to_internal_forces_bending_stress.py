"""Qué momento va con qué inercia: ejes de FrameSection frente a los ejes locales de InternalForces.

En el esquema x es el eje fuerte de la sección (I_x, S_x, Z_x) e y el débil. En los esfuerzos
los ejes locales son 1 = axial, 2 = y, 3 = z: la flexión fuerte es M_z (momento alrededor del
eje local z) y se resiste con I_x/S_x; la flexión débil es M_y y va con I_y/S_y. Es el convenio de
SAP2000/ETABS (M3 fuerte, M2 débil) y la fuente clásica de errores al pasar datos entre programas.

IPE 300 S355 con N = −120 kN, M_z = 90 kN·m, M_y = 6 kN·m en centro de vano:
    σ = N/A ± M_z/S_x ± M_y/S_y  (elástica, extremos de las alas)      utilización = σ_max/f_y

Ejecutar:  python examples/section_strong_weak_axis_mapping_to_internal_forces_bending_stress.py
"""
from loadpath import FrameSection, InternalForces, StructuralMaterial

IPE300 = FrameSection(name="IPE 300", A_mm2=5381, Ix_mm4=8.356e7, Iy_mm4=6.04e6, J_mm4=2.01e5, Cw_mm6=1.26e11,
                      Sx_mm3=557e3, Zx_mm3=628e3, Sy_mm3=80.5e3, Zy_mm3=125e3, depth_mm=300, width_mm=150)
S355 = StructuralMaterial(name="S355", material_type="steel", E_MPa=210_000, poisson=0.3, density_kg_m3=7850, Fy_MPa=355, Fu_MPa=490)


def main() -> None:
    f = InternalForces(member_id="V-07", station_m=3.0, N_kN=-120.0, Mz_kNm=90.0, My_kNm=6.0, Vy_kN=0.0, Vz_kN=60.0)
    print("Mapa de ejes:")
    print(f"  flexión fuerte  M_z = {f.Mz_kNm:.0f} kN·m  →  I_x = {IPE300.I_strong_axis_mm4:.3e} mm⁴, S_x = {IPE300.S_strong_axis_mm3:.0f} mm³")
    print(f"  flexión débil   M_y = {f.My_kNm:.0f} kN·m  →  I_y = {IPE300.I_weak_axis_mm4:.3e} mm⁴, S_y = {IPE300.S_weak_axis_mm3:.0f} mm³")
    print(f"  cortante V_z = {f.Vz_kN:.0f} kN acompaña a M_z (plano fuerte); V_y acompañaría a M_y\n")
    s_N = f.N_kN * 1e3 / IPE300.A_mm2
    s_Mz = f.Mz_kNm * 1e6 / IPE300.Sx_mm3
    s_My = f.My_kNm * 1e6 / IPE300.Sy_mm3
    print(f"Tensiones elásticas [MPa]: N/A = {s_N:+.1f}, M_z/S_x = ±{s_Mz:.1f}, M_y/S_y = ±{s_My:.1f}")
    s_max = -abs(s_N) - s_Mz - s_My if f.N_kN < 0 else s_N + s_Mz + s_My
    print(f"Esquina más comprimida: σ = {s_max:.1f} MPa → utilización elástica {abs(s_max) / S355.Fy_MPa:.2f} frente a f_y = {S355.Fy_MPa:.0f} MPa")
    err = f.Mz_kNm * 1e6 / IPE300.Sy_mm3
    print(f"\nSi se cruzan los ejes (M_z con S_y): σ = {err:.0f} MPa, {err / s_Mz:.1f} veces la real. El esquema lo evita nombrando los ejes en los dos modelos.")


if __name__ == "__main__":
    main()

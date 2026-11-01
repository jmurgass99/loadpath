"""Pórtico plano ensamblado con los helpers: rigidez al desplome con nudos rígidos, semirrígidos y articulados, frente a las formas cerradas.

Pórtico de 10 m de luz y 5 m de altura, pilares HEB 300 (I = 2,517·10⁻⁴ m⁴) empotrados en la
base y dintel IPE 400 (I = 2,313·10⁻⁴ m⁴), E = 210 GPa, carga horizontal de 100 kN en la
cabeza del pilar izquierdo. Se ensamblan las tres matrices 6×6 (`beam_stiffness_2d`, con la
transformación de los pilares) y en el dintel se condensan resortes de extremo
(`semi_rigid_bending_stiffness`) con S_j = ∞, 25, 8, 2 veces E·I_b/L_b y 0.

Formas cerradas que acotan el resultado (EI_c = 52 857 kN·m²):
    dintel infinitamente rígido y nudos rígidos:  k = 24·EI_c/H³ = 10 149 kN/m
    nudos articulados (dintel solo ata las cabezas): k = 2·3·EI_c/H³ = 2 537 kN/m

Ejecutar:  python examples/fea_portal_frame_sway_stiffness_rigid_vs_semi_rigid_joints_assembly.py
"""
from math import cos, inf, sin, pi

import numpy as np

from loadpath.fea import beam_stiffness_2d, semi_rigid_bending_stiffness

E = 210e6
I_C, A_C = 2.517e-4, 1.491e-2      # HEB 300
I_B, A_B = 2.313e-4, 8.446e-3      # IPE 400
H, L, F = 5.0, 10.0, 100.0


def transform(K_local: np.ndarray, alpha: float) -> np.ndarray:
    c, s = cos(alpha), sin(alpha)
    R = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])
    T = np.zeros((6, 6))
    T[:3, :3] = R
    T[3:, 3:] = R
    return T.T @ K_local @ T


def beam_with_springs(EI: float, EA: float, Sj: float) -> np.ndarray:
    K = beam_stiffness_2d(L, EI, EA, n=2)
    idx = [1, 2, 4, 5]
    K[np.ix_(idx, idx)] = semi_rigid_bending_stiffness(K[np.ix_(idx, idx)], Sj, Sj)
    return K


def sway_stiffness(EI_b: float, Sj: float) -> float:
    # nudos: 1 (0,0) 2 (0,H) 3 (L,H) 4 (L,0); GDL 3 por nudo; empotrados 1 y 4
    Kg = np.zeros((12, 12))
    col = transform(beam_stiffness_2d(H, E * I_C, E * A_C, n=2), pi / 2)
    for ni, nj in ((0, 1), (3, 2)):
        dof = [3 * ni, 3 * ni + 1, 3 * ni + 2, 3 * nj, 3 * nj + 1, 3 * nj + 2]
        Kg[np.ix_(dof, dof)] += col
    dof = [3, 4, 5, 6, 7, 8]
    Kg[np.ix_(dof, dof)] += beam_with_springs(EI_b, E * A_B, Sj)
    free = [3, 4, 5, 6, 7, 8]
    P = np.zeros(12)
    P[3] = F
    u = np.linalg.solve(Kg[np.ix_(free, free)], P[free])
    return F / u[0]


def main() -> None:
    EI_c, EIL_b = E * I_C, E * I_B / L
    print(f"EI_c = {EI_c:,.0f} kN·m²; cotas: 24·EI_c/H³ = {24 * EI_c / H ** 3:,.0f} kN/m, 6·EI_c/H³ = {6 * EI_c / H ** 3:,.0f} kN/m\n")
    print(f"  {'dintel':>18} {'S_j':>12} {'k = F/Δ [kN/m]':>14} {'Δ(100 kN) [mm]':>14} {'k / k_rígido':>12}")
    k_ref = sway_stiffness(E * I_B, inf)
    casos = [("IPE 400", E * I_B, inf), ("IPE 400", E * I_B, 25 * EIL_b), ("IPE 400", E * I_B, 8 * EIL_b), ("IPE 400", E * I_B, 2 * EIL_b),
             ("IPE 400", E * I_B, 0.0), ("rígido (×10⁶)", E * I_B * 1e6, inf)]
    for nombre, EIb, Sj in casos:
        k = sway_stiffness(EIb, Sj)
        sj = "∞" if Sj == inf else f"{Sj / EIL_b:.0f}·EI_b/L_b" if Sj > 0 else "0 (articulado)"
        print(f"  {nombre:>18} {sj:>12} {k:14,.0f} {F / k * 1000:14.1f} {k / k_ref:12.2f}")
    k_inf, k_pin = sway_stiffness(E * I_B * 1e6, inf), sway_stiffness(E * I_B, 0.0)
    print(f"\nComprobación: dintel rígido → {k_inf:,.0f} frente a 24·EI_c/H³ = {24 * EI_c / H ** 3:,.0f} ({k_inf / (24 * EI_c / H ** 3) * 100:.2f} %); "
          f"articulado → {k_pin:,.0f} frente a 6·EI_c/H³ = {6 * EI_c / H ** 3:,.0f} ({k_pin / (6 * EI_c / H ** 3) * 100:.2f} %)")
    print("Una unión en el umbral «rígido» de pórtico arriostrado (8·EI_b/L_b) pierde un 17 % de rigidez al desplome y en el umbral no arriostrado (25·EI_b/L_b) un 7 %: por eso EN 1993-1-8 exige el segundo en pórticos no arriostrados.")


if __name__ == "__main__":
    main()

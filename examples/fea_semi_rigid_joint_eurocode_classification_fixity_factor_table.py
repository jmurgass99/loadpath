"""Nudos semirrígidos: clasificación de EN 1993-1-8 §5.2.2.5, factor de fijación y rigidez condensada.

Viga IPE 400 S355 de 8 m (EI_b/L_b = 6 071 kN·m/rad). EN 1993-1-8 clasifica la unión por su
rigidez inicial S_j,ini: nominalmente articulada si S_j,ini <= 0,5·E·I_b/L_b, rígida si
S_j,ini >= k_b·E·I_b/L_b con k_b = 8 (pórtico arriostrado) o 25 (no arriostrado), semirrígida
entre ambas. `semi_rigid_bending_stiffness` condensa resortes R_i = R_j = S_j en los extremos;
el resultado coincide con Monforton y Wu (1963): γ = 1/(1 + 3EI/(R·L)),
k_θiθi = (4EI/L)·3γ/(4 − γ²). Se tabulan S_j = 0,25…100 veces EI/L.

Ejecutar:  python examples/fea_semi_rigid_joint_eurocode_classification_fixity_factor_table.py
"""
from math import inf

import numpy as np

from loadpath.fea import beam_stiffness_2d, semi_rigid_bending_stiffness

E, I, A, L = 210e6, 2.313e-4, 8.446e-3, 8.0


def clasificacion(Sj: float, EIL: float, kb: int) -> str:
    if Sj <= 0.5 * EIL:
        return "articulada"
    if Sj >= kb * EIL:
        return "rígida"
    return "semirrígida"


def main() -> None:
    EI = E * I
    EIL = EI / L
    K6 = beam_stiffness_2d(L, EI, E * A, n=2)
    Kb = K6[np.ix_([1, 2, 4, 5], [1, 2, 4, 5])]
    print(f"IPE 400, L = {L:.0f} m: E·I_b/L_b = {EIL:,.0f} kN·m/rad; umbrales EN 1993-1-8: articulada <= {0.5 * EIL:,.0f}, rígida >= {8 * EIL:,.0f} (arriostrado) / {25 * EIL:,.0f} (no arriostrado)\n")
    print(f"  {'S_j/(EI/L)':>10} {'S_j [kN·m/rad]':>14} {'γ':>6} {'k_θiθi/(4EI/L)':>14} {'Monforton-Wu':>12} {'arriostrado':>12} {'no arriostr.':>12}")
    for f in (0.25, 0.5, 1, 2, 4, 8, 12, 25, 50, 100, inf):
        R = f * EIL if f != inf else inf
        Ks = semi_rigid_bending_stiffness(Kb, R, R)
        g = 1.0 if R == inf else 1.0 / (1.0 + 3 * EI / (R * L))
        mw = 3 * g / (4 - g * g)
        print(f"  {f:>10} {R if R != inf else float('inf'):14,.0f} {g:6.3f} {Ks[1, 1] / (4 * EIL):14.3f} {mw:12.3f} {clasificacion(R, EIL, 8):>12} {clasificacion(R, EIL, 25):>12}")
    print("\nUna unión en el umbral «rígido» de pórtico arriostrado (S_j = 8·EI/L) conserva el 63 % de la rigidez rotacional 4EI/L de la viga; en el umbral no arriostrado (25·EI/L), el 84 %.")
    print("R va en kN·m/rad, las mismas unidades que K_b; pasar una rigidez relativa (k·L/EI) hace que todo salga articulado.")


if __name__ == "__main__":
    main()

"""Ayudas de elementos finitos: viga de inercia variable y nudos semirrígidos.

1. Matriz de rigidez 2D de una viga de canto variable (EI varía linealmente a lo
   largo de la barra) frente a la viga prismática equivalente.
2. Corrección de la rigidez a flexión por rigidez rotacional finita en los
   extremos (nudos semirrígidos), desde articulado hasta empotrado.

Ejecutar:  python examples/02_fea_helpers_tapered_and_semirigid.py
"""
import numpy as np

from loadpath.fea.non_prismatic import beam_stiffness_2d
from loadpath.fea.semi_rigid import semi_rigid_bending_stiffness

L = 6.0            # m
E = 210e6          # kPa (210 000 MPa)
I0, I1 = 8.36e-5, 2.5e-5   # m⁴ en los extremos (IPE 300 → menor)
A = 5.38e-3        # m²


def main() -> None:
    EI_taper = lambda x: E * (I0 + (I1 - I0) * x / L)    # noqa: E731
    K_taper = beam_stiffness_2d(L, EI_taper, E * A, n=40)
    K_prism = beam_stiffness_2d(L, E * I0, E * A, n=40)

    np.set_printoptions(precision=3, suppress=True, linewidth=120)
    print("Rigidez a flexión en el extremo i (K[1,1], kN/m):")
    print(f"  prismática I0:            {K_prism[1, 1]:12.1f}")
    print(f"  variable I0 → I1:         {K_taper[1, 1]:12.1f}  ({K_taper[1, 1] / K_prism[1, 1]:.1%} de la prismática)")
    print("\nMatriz 6x6 de la viga de inercia variable:")
    print(K_taper)

    # Nudos semirrígidos: rigidez rotacional relativa R = (k·L)/(EI) típica
    EI = E * I0
    print("\nNudos semirrígidos (mismo valor en ambos extremos):")
    print(f"  {'k_rot [kN·m/rad]':>18} {'K[1,1] / rígida':>16}")
    Kb = beam_stiffness_2d(L, EI, E * A, n=20)
    for k in (0.0, 1e3, 1e4, 1e5, 1e7):
        R = k * L / EI if k > 0 else 0.0
        Ks = semi_rigid_bending_stiffness(Kb, R, R)
        print(f"  {k:18.0f} {Ks[1, 1] / Kb[1, 1]:16.3f}")


if __name__ == "__main__":
    main()

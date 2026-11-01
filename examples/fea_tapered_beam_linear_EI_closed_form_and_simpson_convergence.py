"""Viga acartelada con EI lineal: flexibilidad del extremo en forma cerrada y convergencia de Simpson.

Voladizo de 6 m cuya rigidez crece hacia el extremo libre, EI(x) = EI₀·(1 + x/L) con
EI₀ = 17 548 kN·m² (IPE 300). La flexibilidad del extremo libre D = inv(K[v_j, θ_j]) tiene
integrales elementales (u = 1 + x/L):

    D₀₀ = (L³/EI₀)·(4·ln 2 − 5/2) = 0,272588·L³/EI₀     (prismática EI₀: 1/3; prismática 2·EI₀: 1/6)
    D₀₁ = (L²/EI₀)·(2·ln 2 − 1)   = 0,386294·L²/EI₀
    D₁₁ = (L/EI₀)·ln 2             = 0,693147·L/EI₀

El error de Simpson cae 16 veces al duplicar n (orden 4): con n = 8 ya está en 10⁻⁵.

Ejecutar:  python examples/fea_tapered_beam_linear_EI_closed_form_and_simpson_convergence.py
"""
from math import log

import numpy as np

from loadpath.fea import beam_stiffness_2d

L, EI0, EA = 6.0, 17_548.0, 1.13e6


def main() -> None:
    exact = np.array([[(4 * log(2) - 2.5) * L ** 3 / EI0, (2 * log(2) - 1) * L ** 2 / EI0],
                      [(2 * log(2) - 1) * L ** 2 / EI0, log(2) * L / EI0]])
    print(f"Forma cerrada: D₀₀ = {exact[0, 0]:.6f} m/kN, D₀₁ = {exact[0, 1]:.6f} rad/kN, D₁₁ = {exact[1, 1]:.6f} rad/(kN·m)")
    print(f"Cotas prismáticas de D₀₀: EI₀ → {L ** 3 / (3 * EI0):.6f}, 2·EI₀ → {L ** 3 / (6 * EI0):.6f}\n")
    print(f"  {'n':>3} {'D₀₀ Simpson':>12} {'error rel.':>11} {'razón':>6}")
    prev = None
    for n in (2, 4, 8, 16, 32, 64):
        K = beam_stiffness_2d(L, EI=lambda x: EI0 * (1 + x / L), EA=EA, n=n)
        D = np.linalg.inv(K[np.ix_([4, 5], [4, 5])])
        err = abs(D[0, 0] - exact[0, 0]) / exact[0, 0]
        print(f"  {n:3d} {D[0, 0]:12.6f} {err:11.2e} {'' if prev is None else f'{prev / err:6.1f}'}")
        prev = err
    K = beam_stiffness_2d(L, EI=lambda x: EI0 * (1 + x / L), EA=EA, n=40)
    Kp = beam_stiffness_2d(L, EI0, EA, n=2)
    print(f"\nRigidez rotacional en el extremo i (K[θ_i,θ_i]): acartelada {K[2, 2]:,.0f} frente a prismática EI₀ {Kp[2, 2]:,.0f} kN·m/rad ({K[2, 2] / Kp[2, 2]:.2f}×); "
          f"en j: {K[5, 5]:,.0f} ({K[5, 5] / Kp[5, 5]:.2f}×): el extremo con más inercia (j) es el más rígido.")
    print(f"Factor de transmisión K[θ_i,θ_j]/K[θ_j,θ_j] = {K[2, 5] / K[5, 5]:.3f} (prismática: 0,500).")


if __name__ == "__main__":
    main()

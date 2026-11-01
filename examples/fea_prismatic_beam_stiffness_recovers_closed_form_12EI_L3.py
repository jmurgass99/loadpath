"""La viga prismática como caso particular: la integración de Simpson recupera la matriz 6×6 clásica a precisión de máquina.

Viga IPE 300 S355 de 6 m (EI = 210·10⁶ kPa · 8,356·10⁻⁵ m⁴ = 17 548 kN·m², EA = 1,130·10⁶ kN).
Con EI y EA constantes `beam_stiffness_2d` debe dar exactamente

    [EA/L, 12EI/L³, 6EI/L², 4EI/L, 2EI/L, −6EI/L², ...]   (GDL [u_i, v_i, θ_i, u_j, v_j, θ_j])

Se imprime la matriz en kN y kN·m y el error máximo frente a la forma cerrada para n = 2 y n = 20
intervalos: Simpson integra exactamente polinomios de grado 3 y el integrando (L − x)²/EI es de
grado 2, así que n = 2 ya es exacto.

Ejecutar:  python examples/fea_prismatic_beam_stiffness_recovers_closed_form_12EI_L3.py
"""
import numpy as np

from loadpath.fea import beam_stiffness_2d

E, I, A, L = 210e6, 8.356e-5, 5.381e-3, 6.0   # kPa, m⁴, m², m


def prismatica(EA: float, EI: float, L: float) -> np.ndarray:
    K = np.zeros((6, 6))
    K[0, 0] = K[3, 3] = EA / L
    K[0, 3] = K[3, 0] = -EA / L
    c = EI / L ** 3
    kb = c * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L ** 2, -6 * L, 2 * L ** 2],
                       [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L ** 2, -6 * L, 4 * L ** 2]])
    idx = [1, 2, 4, 5]
    K[np.ix_(idx, idx)] = kb
    return K


def main() -> None:
    EI, EA = E * I, E * A
    ref = prismatica(EA, EI, L)
    np.set_printoptions(precision=1, suppress=True, linewidth=130)
    print(f"IPE 300, L = {L:.0f} m: EI = {EI:,.0f} kN·m², EA = {EA:,.0f} kN")
    print(f"  12EI/L³ = {12 * EI / L ** 3:,.1f} kN/m   6EI/L² = {6 * EI / L ** 2:,.1f} kN   4EI/L = {4 * EI / L:,.1f} kN·m/rad   2EI/L = {2 * EI / L:,.1f} kN·m/rad\n")
    for n in (2, 20):
        K = beam_stiffness_2d(L, EI, EA, n=n)
        err = np.max(np.abs(K - ref)) / np.max(np.abs(ref))
        print(f"  n = {n:2d} intervalos de Simpson: error relativo máximo frente a la forma cerrada = {err:.1e}")
    print("\nMatriz 6×6 (GDL [u_i, v_i, θ_i, u_j, v_j, θ_j]):")
    print(beam_stiffness_2d(L, EI, EA, n=2))
    print("\nEl mismo helper con EI(x) callable da la viga de sección variable: el caso prismático es la comprobación de que la integración está bien montada.")


if __name__ == "__main__":
    main()

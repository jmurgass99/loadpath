"""Dintel con cartelas en los dos extremos: EI a trozos, rigidez rotacional y factor de transmisión frente a la viga prismática.

Dintel de nave de 12 m en IPE 400 (I = 2,313·10⁸ mm⁴, h = 400 mm) con cartelas de 2 m en cada
extremo que doblan el canto en el nudo y decrecen linealmente hasta el perfil. La inercia de la
sección acartelada se aproxima por I(x) = I₀·(h(x)/h₀)³ (la misma relación canto-inercia de un
perfil en I de alas iguales): 8·I₀ en el nudo, I₀ a 2 m. `beam_stiffness_2d` integra EI(x) a
trozos sin más que pasar la función; se compara con la viga prismática y con una cartela doble
de 3 m. La tabla usa n = 240, con el que los quiebros (x = 2 y 10 m) caen en nodos; al final se mide
cuánto error quita pasar los quiebros en `breakpoints_x` (Simpson por tramos) cuando n es pequeño. El factor de transmisión (Cross) de la prismática es 0,5; con cartelas simétricas sube
por encima de 0,5 (tablas PCA de constantes de pórticos: 0,6–0,7), porque el tramo central, más
flexible, deja llegar al extremo opuesto una fracción mayor del momento aplicado.

Ejecutar:  python examples/fea_haunched_rafter_piecewise_EI_stiffness_and_carry_over_factor.py
"""
from loadpath.fea import beam_stiffness_2d

E = 210e6            # kPa
I0 = 2.313e-4        # m⁴ (IPE 400)
A = 8.446e-3         # m²
L = 12.0


def EI_cartelas(a: float, ratio: float):
    def h_rel(x: float) -> float:
        if x < a:
            return ratio - (ratio - 1.0) * x / a
        if x > L - a:
            return ratio - (ratio - 1.0) * (L - x) / a
        return 1.0
    return lambda x: E * I0 * h_rel(x) ** 3


def main() -> None:
    Kp = beam_stiffness_2d(L, E * I0, E * A, n=2)
    print(f"Dintel L = {L:.0f} m, IPE 400: 4EI/L = {Kp[2, 2]:,.0f} kN·m/rad, 2EI/L = {Kp[2, 5]:,.0f}, 12EI/L³ = {Kp[1, 1]:,.0f} kN/m\n")
    print(f"  {'cartela':>22} {'K[θi,θi] [kN·m/rad]':>19} {'/ prismática':>12} {'K[θi,θj]':>10} {'transmisión':>11} {'K[vi,vi] [kN/m]':>15} {'/ prismática':>12}")
    print(f"  {'ninguna (prismática)':>22} {Kp[2, 2]:19,.0f} {1.0:12.2f} {Kp[2, 5]:10,.0f} {Kp[2, 5] / Kp[2, 2]:11.3f} {Kp[1, 1]:15,.0f} {1.0:12.2f}")
    res = {}
    for a, ratio in ((2.0, 2.0), (3.0, 2.0), (2.0, 1.5)):
        K = beam_stiffness_2d(L, EI_cartelas(a, ratio), E * A, n=240)
        res[(a, ratio)] = K
        print(f"  {f'{a:.0f} m, canto ×{ratio:.1f}':>22} {K[2, 2]:19,.0f} {K[2, 2] / Kp[2, 2]:12.2f} {K[2, 5]:10,.0f} {K[2, 5] / K[2, 2]:11.3f} {K[1, 1]:15,.0f} {K[1, 1] / Kp[1, 1]:12.2f}")
    K2 = res[(2.0, 2.0)]
    print(f"\nLa rigidez rotacional del nudo sube un {(K2[2, 2] / Kp[2, 2] - 1) * 100:.0f} % con cartelas de 2 m que doblan el canto y el factor de "
          f"transmisión pasa de {Kp[2, 5] / Kp[2, 2]:.2f} a {K2[2, 5] / K2[2, 2]:.2f}: es lo que hace rentable la cartela frente a aumentar el perfil en toda la luz.")
    bp = [2.0, L - 2.0]
    Kref = beam_stiffness_2d(L, EI_cartelas(2.0, 2.0), E * A, n=400, breakpoints_x=bp)
    rel = lambda X: max(abs(X[i, j] / Kref[i, j] - 1) for i in range(6) for j in range(6) if abs(Kref[i, j]) > 1e-9)
    Kb = beam_stiffness_2d(L, EI_cartelas(2.0, 2.0), E * A, n=20, breakpoints_x=bp)
    Kn = beam_stiffness_2d(L, EI_cartelas(2.0, 2.0), E * A, n=20)
    print(f"Quiebros de EI(x) en x = 2 y 10 m, error máximo frente a Simpson por tramos con n = 400: "
          f"n = 20 con breakpoints_x {rel(Kb):.1e}; n = 240 sin ellos (la tabla) {rel(K2):.1e}; n = 20 sin ellos {rel(Kn):.1e}.")


if __name__ == "__main__":
    main()

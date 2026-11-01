"""Suite 5.1 — Rigidez de viga de sección no prismática (pórtico plano 2D).

Se obtiene por el método de la flexibilidad sobre el voladizo equivalente
(nudo i empotrado, nudo j libre), integrando numéricamente con la regla de
Simpson la flexibilidad de una sección de inercia variable EI(x):

    D = ∫₀ᴸ m(x)·m(x)ᵀ / EI(x) dx ,   m(x) = [ (L−x) , 1 ]ᵀ

donde la primera componente es el diagrama de momento por una carga
transversal unidad en la punta y la segunda por un momento unidad en la
punta. La rigidez del extremo libre es Kjj = D⁻¹, y la matriz completa
4×4 de flexión se obtiene por equilibrio (cuerpo rígido del voladizo):

    K₄ = Tcᵀ · Kjj · Tc ,
    Tc = [[−1, −L, 1, 0], [0, −1, 0, 1]]   (GDL [vi, θi, vj, θj])

Con EI constante se recupera exactamente la matriz prismática estándar.
El axial se integra análogamente: ka = 1 / ∫₀ᴸ dx/EA(x).

Cuando existen saltos bruscos de sección (cartelas escalonadas, platabandas),
`breakpoints_x` permite subdividir [0, L] en subintervalos suaves e integrar
Simpson por tramos sin error de Gibbs en las discontinuidades.

Orden global de GDL: [ui, vi, θi, uj, vj, θj].
"""
from __future__ import annotations

from typing import Callable, Sequence

import numpy as np


def _as_callable(v) -> Callable[[float], float]:
    if callable(v):
        return v
    return lambda x, _v=float(v): _v


def _simpson_nodes_interval(a: float, b: float, n: int, eps_end: float = 0.0):
    if n < 2:
        n = 2
    if n % 2 != 0:
        n += 1  # Simpson requiere número par de intervalos
    h = (b - a) / n
    x = np.linspace(a, b, n + 1)
    if eps_end > 0.0 and len(x) >= 2:
        x[0] = a + eps_end * (b - a)
        x[-1] = b - eps_end * (b - a)
    w = np.ones(n + 1)
    w[1:-1:2] = 4.0
    w[2:-1:2] = 2.0
    w *= h / 3.0
    return x, w


def _simpson_nodes(L: float, n: int):
    return _simpson_nodes_interval(0.0, L, n, eps_end=0.0)


def beam_stiffness_2d(
    L: float,
    EI,
    EA,
    n: int = 20,
    breakpoints_x: Sequence[float] | None = None,
) -> np.ndarray:
    """Matriz de rigidez 6×6 de una viga 2D de sección variable.

    Parameters
    ----------
    L : longitud del elemento.
    EI, EA : rigidez a flexión / axial. Cada una puede ser un escalar
        (sección prismática) o una función EI(x), EA(x) con 0 ≤ x ≤ L.
    n : número de intervalos de Simpson (se redondea a par).
    breakpoints_x : abscisas interiores opcionales (0 < x_k < L) donde EI(x)
        o EA(x) presentan discontinuidades o cambios bruscos de pendiente.
        Si se indican, la cuadratura de Simpson se aplica tramo a tramo.
    """
    EI_f = _as_callable(EI)
    EA_f = _as_callable(EA)

    if breakpoints_x:
        interior = sorted({float(xb) for xb in breakpoints_x if 0.0 < float(xb) < L})
    else:
        interior = []

    if not interior:
        segments = [(0.0, L, n, 0.0)]
    else:
        knots = [0.0] + interior + [L]
        segments = []
        for a, b in zip(knots[:-1], knots[1:]):
            n_sub = max(4, int(round(n * (b - a) / L)))
            if n_sub % 2 != 0:
                n_sub += 1
            segments.append((a, b, n_sub, 1e-12))

    D = np.zeros((2, 2))
    fa = 0.0
    for a, b, n_sub, eps_end in segments:
        x, w = _simpson_nodes_interval(a, b, n_sub, eps_end=eps_end)
        for xi, wi in zip(x, w):
            m = np.array([L - xi, 1.0])
            D += wi * np.outer(m, m) / EI_f(xi)
        fa += float(np.sum(w / np.array([EA_f(xi) for xi in x])))

    Kjj = np.linalg.inv(D)
    Tc = np.array([[-1.0, -L, 1.0, 0.0],
                   [0.0, -1.0, 0.0, 1.0]])
    K4 = Tc.T @ Kjj @ Tc  # GDL [vi, θi, vj, θj]

    ka = 1.0 / fa

    # --- Ensamblaje 6×6 [ui, vi, θi, uj, vj, θj] ---
    K = np.zeros((6, 6))
    K[0, 0] = K[3, 3] = ka
    K[0, 3] = K[3, 0] = -ka
    idx = [1, 2, 4, 5]
    K[np.ix_(idx, idx)] = K4
    # Simetriza para limpiar ruido numérico de la inversión
    return 0.5 * (K + K.T)

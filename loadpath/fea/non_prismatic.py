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

Orden global de GDL: [ui, vi, θi, uj, vj, θj].
"""
from __future__ import annotations

from typing import Callable

import numpy as np


def _as_callable(v) -> Callable[[float], float]:
    if callable(v):
        return v
    return lambda x, _v=float(v): _v


def _simpson_nodes(L: float, n: int):
    if n % 2 != 0:
        n += 1  # Simpson requiere número par de intervalos
    h = L / n
    x = np.linspace(0.0, L, n + 1)
    w = np.ones(n + 1)
    w[1:-1:2] = 4.0
    w[2:-1:2] = 2.0
    w *= h / 3.0
    return x, w


def beam_stiffness_2d(L: float, EI, EA, n: int = 20) -> np.ndarray:
    """Matriz de rigidez 6×6 de una viga 2D de sección variable.

    Parameters
    ----------
    L : longitud del elemento.
    EI, EA : rigidez a flexión / axial. Cada una puede ser un escalar
        (sección prismática) o una función EI(x), EA(x) con 0 ≤ x ≤ L.
    n : número de intervalos de Simpson (se redondea a par).
    """
    EI_f = _as_callable(EI)
    EA_f = _as_callable(EA)
    x, w = _simpson_nodes(L, n)

    # --- Flexión: flexibilidad del voladizo ---
    D = np.zeros((2, 2))
    for xi, wi in zip(x, w):
        m = np.array([L - xi, 1.0])
        D += wi * np.outer(m, m) / EI_f(xi)
    Kjj = np.linalg.inv(D)
    Tc = np.array([[-1.0, -L, 1.0, 0.0],
                   [0.0, -1.0, 0.0, 1.0]])
    K4 = Tc.T @ Kjj @ Tc  # GDL [vi, θi, vj, θj]

    # --- Axial: flexibilidad en serie ---
    fa = float(np.sum(w / np.array([EA_f(xi) for xi in x])))
    ka = 1.0 / fa

    # --- Ensamblaje 6×6 [ui, vi, θi, uj, vj, θj] ---
    K = np.zeros((6, 6))
    K[0, 0] = K[3, 3] = ka
    K[0, 3] = K[3, 0] = -ka
    idx = [1, 2, 4, 5]
    K[np.ix_(idx, idx)] = K4
    # Simetriza para limpiar ruido numérico de la inversión
    return 0.5 * (K + K.T)

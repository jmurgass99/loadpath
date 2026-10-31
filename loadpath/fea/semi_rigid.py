"""Suite 5.2 — Conexiones semirrígidas (resortes rotacionales de extremo).

Cada extremo de la viga lleva un resorte rotacional (rigidez R_i, R_j) entre
el giro del nudo (externo) y el giro real del extremo de la barra (interno):

        M = R · (θ_nudo − θ_barra)

Se ensambla el sistema viga + resortes con los giros internos como GDL
adicionales y se condensan estáticamente. El método es general: vale para
cualquier matriz de flexión base `Kb` (prismática o no prismática de la
Suite 5.1).

Límites verificables:
  * R → ∞  : extremo rígido (recupera `Kb`).
  * R → 0  : rótula (momento de extremo nulo; rigidez en el otro extremo
             cae de 4EI/L a 3EI/L para viga prismática).
"""
from __future__ import annotations

import math

import numpy as np


def semi_rigid_bending_stiffness(Kb, Ri: float, Rj: float) -> np.ndarray:
    """Matriz de flexión 4×4 con resortes de extremo. GDL [vi, θi, vj, θj]."""
    Kb = np.asarray(Kb, dtype=float)
    # GDL externos
    DOF_VI, DOF_THI, DOF_VJ, DOF_THJ = 0, 1, 2, 3
    next_dof = 4
    internal: list[int] = []
    springs: list[tuple[int, int, float]] = []

    # Extremo i
    if math.isinf(Ri):
        beam_thi = DOF_THI
    else:
        beam_thi = next_dof
        internal.append(next_dof)
        springs.append((DOF_THI, next_dof, Ri))
        next_dof += 1
    # Extremo j
    if math.isinf(Rj):
        beam_thj = DOF_THJ
    else:
        beam_thj = next_dof
        internal.append(next_dof)
        springs.append((DOF_THJ, next_dof, Rj))
        next_dof += 1

    N = next_dof
    K = np.zeros((N, N))
    beam_map = [DOF_VI, beam_thi, DOF_VJ, beam_thj]
    for a in range(4):
        for b in range(4):
            K[beam_map[a], beam_map[b]] += Kb[a, b]
    for e, i, R in springs:
        K[e, e] += R
        K[i, i] += R
        K[e, i] -= R
        K[i, e] -= R

    ext = [DOF_VI, DOF_THI, DOF_VJ, DOF_THJ]
    if internal:
        Kee = K[np.ix_(ext, ext)]
        Kei = K[np.ix_(ext, internal)]
        Kii = K[np.ix_(internal, internal)]
        Kred = Kee - Kei @ np.linalg.inv(Kii) @ Kei.T
    else:
        Kred = K[np.ix_(ext, ext)]
    return 0.5 * (Kred + Kred.T)

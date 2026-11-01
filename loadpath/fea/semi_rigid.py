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


def fixity_factor_monforton_wu(R: float, EI: float, L: float) -> float:
    """Factor de fijación de Monforton-Wu γ = 1 / (1 + 3·EI / (L·R)).

    Para R = 0 devuelve 0.0 (rótula); para R = ∞ devuelve 1.0 (empotramiento).
    """
    if R < 0.0:
        raise ValueError("R debe ser >= 0")
    if EI <= 0.0 or L <= 0.0:
        raise ValueError("EI y L deben ser > 0")
    if R == 0.0:
        return 0.0
    if math.isinf(R):
        return 1.0
    return 1.0 / (1.0 + 3.0 * EI / (L * R))


def classify_connection_ec3(
    Sj_ini: float,
    EI: float,
    L: float,
    *,
    braced: bool = True,
) -> dict:
    """Clasificación por rigidez rotacional según EN 1993-1-8 §5.2.2.5.

    Parámetro adimensional k_b = S_{j,ini} · L / (E · I_b):
      - Nominalmente articulada (pinned): k_b <= 0.5
      - Rígida (rigid): k_b >= 8.0 (pórtico arriostrado) o k_b >= 25.0 (no arriostrado)
      - Semirrígida (semi-rigid): entre ambos límites.
    """
    if Sj_ini < 0.0:
        raise ValueError("Sj_ini debe ser >= 0")
    if EI <= 0.0 or L <= 0.0:
        raise ValueError("EI y L deben ser > 0")
    upper_bound = 8.0 if braced else 25.0
    lower_bound = 0.5
    if math.isinf(Sj_ini):
        kb = math.inf
        classification = "rigid"
    else:
        kb = (Sj_ini * L) / EI
        if kb <= lower_bound:
            classification = "pinned"
        elif kb >= upper_bound:
            classification = "rigid"
        else:
            classification = "semi-rigid"
    return {
        "classification": classification,
        "kb_dimensionless": kb,
        "pinned_upper_bound": lower_bound,
        "rigid_lower_bound": upper_bound,
        "braced": braced,
        "fixity_factor_gamma": fixity_factor_monforton_wu(Sj_ini, EI, L),
    }


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

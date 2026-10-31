"""Suite 5.1 — Matriz de rigidez de viga de sección no prismática.

Comprobación cerrada decisiva: con EI y EA CONSTANTES la integración de
Simpson debe recuperar la matriz prismática de pórtico plano (6 GDL) a
precisión de máquina. Orden de GDL: [ui, vi, θi, uj, vj, θj].
"""
import numpy as np
import pytest

from loadpath.fea.non_prismatic import beam_stiffness_2d


def _prismatic_reference(EA, EI, L):
    """Matriz prismática estándar de pórtico plano 6×6."""
    K = np.zeros((6, 6))
    # Axial (GDL 0,3)
    k = EA / L
    K[0, 0] = K[3, 3] = k
    K[0, 3] = K[3, 0] = -k
    # Flexión (GDL 1=vi,2=θi,4=vj,5=θj)
    c = EI / L ** 3
    kb = c * np.array([
        [12,    6 * L,  -12,    6 * L],
        [6 * L, 4 * L ** 2, -6 * L, 2 * L ** 2],
        [-12,  -6 * L,   12,   -6 * L],
        [6 * L, 2 * L ** 2, -6 * L, 4 * L ** 2],
    ])
    idx = [1, 2, 4, 5]
    for a, ia in enumerate(idx):
        for b, ib in enumerate(idx):
            K[ia, ib] = kb[a, b]
    return K


def test_constant_EI_EA_recovers_prismatic():
    EA, EI, L = 2.1e5 * 8000.0, 2.1e5 * 6.7e7, 4000.0
    K = beam_stiffness_2d(L, EI=EI, EA=EA, n=20)
    ref = _prismatic_reference(EA, EI, L)
    assert np.allclose(K, ref, rtol=1e-9, atol=1e-3)


def test_constant_via_callable_matches_float():
    EA, EI, L = 1.0e9, 2.0e12, 3000.0
    Kf = beam_stiffness_2d(L, EI=EI, EA=EA, n=10)
    Kc = beam_stiffness_2d(L, EI=lambda x: EI, EA=lambda x: EA, n=10)
    assert np.allclose(Kf, Kc, rtol=1e-10)


def test_matrix_symmetric():
    K = beam_stiffness_2d(3000.0, EI=lambda x: 1e12 * (1 + x / 3000.0), EA=1e9, n=40)
    assert np.allclose(K, K.T, atol=1e-3)


def test_tapered_between_bounds():
    # Viga acartelada: EI varía linealmente de EI0 a 2·EI0.
    # Su rigidez rotacional debe quedar entre la de EI0 y la de 2·EI0.
    L = 4000.0
    EI0 = 1.0e12
    EA = 1.0e9
    K_low = beam_stiffness_2d(L, EI=EI0, EA=EA, n=2)
    K_high = beam_stiffness_2d(L, EI=2 * EI0, EA=EA, n=2)
    K_taper = beam_stiffness_2d(L, EI=lambda x: EI0 * (1 + x / L), EA=EA, n=40)
    # Coeficiente de rigidez rotacional en el extremo i (GDL 2,2)
    assert K_low[2, 2] < K_taper[2, 2] < K_high[2, 2]


def test_positive_definite_free_dofs():
    # Empotrando el nudo i (GDL 0,1,2), la submatriz libre del nudo j
    # debe ser definida positiva (estabilidad elástica).
    K = beam_stiffness_2d(3500.0, EI=lambda x: 1e12 * (1 + 0.5 * x / 3500.0), EA=1e9, n=30)
    Kjj = K[3:, 3:]
    eig = np.linalg.eigvalsh(Kjj)
    assert np.all(eig > 0)

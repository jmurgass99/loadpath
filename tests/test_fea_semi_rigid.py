"""Suite 5.2 — Conexiones semirrígidas (resortes rotacionales de extremo).

Comprobaciones cerradas:
  * Ri = Rj = ∞ (rígido) → recupera la matriz de viga empotrada-empotrada.
  * Rj = 0 (rótula en j) → momento en j nulo para cualquier giro; la rigidez
    rotacional en i cae de 4EI/L a 3EI/L (viga apoyada-empotrada).
  * Rigidez intermedia entre ambos límites.
"""
import math

import numpy as np
import pytest

from loadpath_core.fea.non_prismatic import beam_stiffness_2d
from loadpath_core.fea.semi_rigid import semi_rigid_bending_stiffness


EI, L = 2.0e12, 4000.0


def _bending_block(K6):
    """Extrae el bloque de flexión 4×4 [vi, θi, vj, θj] del 6×6."""
    idx = [1, 2, 4, 5]
    return K6[np.ix_(idx, idx)]


def _Kb():
    return _bending_block(beam_stiffness_2d(L, EI=EI, EA=1.0e9, n=2))


def test_rigid_springs_recover_base():
    Kb = _Kb()
    Ksr = semi_rigid_bending_stiffness(Kb, math.inf, math.inf)
    assert np.allclose(Ksr, Kb, rtol=1e-9)


def test_pin_at_j_zero_moment():
    Kb = _Kb()
    Ksr = semi_rigid_bending_stiffness(Kb, math.inf, 0.0)
    # GDL θj es el índice 3 del bloque 4×4 → toda su fila/columna ~0 (M_j=0)
    assert np.allclose(Ksr[3, :], 0.0, atol=1e-3)
    assert np.allclose(Ksr[:, 3], 0.0, atol=1e-3)


def test_pin_at_j_reduces_i_stiffness_to_3EIL():
    Kb = _Kb()
    Ksr = semi_rigid_bending_stiffness(Kb, math.inf, 0.0)
    # Rigidez rotacional en i con rótula en j = 3EI/L (viga propped)
    assert Ksr[1, 1] == pytest.approx(3 * EI / L, rel=1e-6)


def test_base_i_stiffness_is_4EIL():
    Kb = _Kb()
    # Doble empotramiento: 4EI/L
    assert Kb[1, 1] == pytest.approx(4 * EI / L, rel=1e-9)


def test_intermediate_between_bounds():
    Kb = _Kb()
    rigid = semi_rigid_bending_stiffness(Kb, math.inf, math.inf)
    pinned = semi_rigid_bending_stiffness(Kb, math.inf, 0.0)
    mid = semi_rigid_bending_stiffness(Kb, math.inf, 3 * EI / L)
    # La rigidez rotacional en i debe quedar entre el caso rótula y el rígido
    assert pinned[1, 1] < mid[1, 1] < rigid[1, 1]


def test_symmetric_springs_keep_symmetry():
    Kb = _Kb()
    Ksr = semi_rigid_bending_stiffness(Kb, 5 * EI / L, 5 * EI / L)
    assert np.allclose(Ksr, Ksr.T, atol=1e-6)


def test_monforton_wu_fixity_factor():
    # Para viga prismática con resortes iguales R, el factor de fijación
    # γ = 1/(1 + 3EI/(L·R)); con R = 3EI/L → γ = 0.5.
    Kb = _Kb()
    R = 3 * EI / L
    Ksr = semi_rigid_bending_stiffness(Kb, R, R)
    # La rigidez rotacional reducida en i debe ser menor que 4EI/L
    assert Ksr[1, 1] < 4 * EI / L
    assert Ksr[1, 1] > 0

# -*- coding: utf-8 -*-
"""Formas cerradas para las ayudas FEA: viga de EI lineal y resortes de Monforton y Wu.

1. Voladizo con EI(x) = EI₀·(1 + x/L) (crece hacia el extremo libre). Con u = 1 + x/L
   la flexibilidad del extremo libre D = ∫ m·mᵀ/EI dx tiene integrales elementales:

       D₀₀ = ∫(L−x)²/EI = (L³/EI₀)·(4·ln 2 − 5/2) = 0,272588·L³/EI₀
       D₀₁ = ∫(L−x)/EI   = (L²/EI₀)·(2·ln 2 − 1)   = 0,386294·L²/EI₀
       D₁₁ = ∫ 1/EI      = (L/EI₀)·ln 2             = 0,693147·L/EI₀

   y D = inv(K₄[vj,θj]) porque las columnas de T_c para el nudo j son la identidad.
   (Prismática EI₀: D₀₀ = L³/3EI₀ = 0,3333; prismática 2·EI₀: 0,1667; la acartelada
   queda entre ambas.)

2. Viga prismática con resortes iguales R en los dos extremos (Monforton y Wu, 1963):
   γ = 1/(1 + 3·EI/(R·L)); k_θiθi = (4EI/L)·3γ/(4 − γ²) y k_θiθj = (2EI/L)·3γ²/(4 − γ²).
   Con R = 3EI/L, γ = 0,5: k_θiθi = 1,6·EI/L y k_θiθj = 0,4·EI/L.
"""
from __future__ import annotations

from math import log

import numpy as np
import pytest

from loadpath.fea import beam_stiffness_2d, semi_rigid_bending_stiffness


def test_linear_EI_cantilever_flexibility_closed_form():
    L, EI0 = 6.0, 1.0e5
    K = beam_stiffness_2d(L, EI=lambda x: EI0 * (1.0 + x / L), EA=1.0e9, n=200)
    Kjj = K[np.ix_([4, 5], [4, 5])]
    D = np.linalg.inv(Kjj)
    assert D[0, 0] == pytest.approx((4 * log(2) - 2.5) * L ** 3 / EI0, rel=1e-6)
    assert D[0, 1] == pytest.approx((2 * log(2) - 1.0) * L ** 2 / EI0, rel=1e-6)
    assert D[1, 1] == pytest.approx(log(2) * L / EI0, rel=1e-6)
    # cota: entre la prismática de EI0 y la de 2·EI0
    assert L ** 3 / (3 * 2 * EI0) < D[0, 0] < L ** 3 / (3 * EI0)


def test_simpson_convergence_is_fourth_order():
    L, EI0 = 6.0, 1.0e5
    exact = (4 * log(2) - 2.5) * L ** 3 / EI0
    errs = []
    for n in (4, 8, 16):
        K = beam_stiffness_2d(L, EI=lambda x: EI0 * (1.0 + x / L), EA=1.0e9, n=n)
        errs.append(abs(np.linalg.inv(K[np.ix_([4, 5], [4, 5])])[0, 0] - exact))
    assert errs[0] / errs[1] > 12 and errs[1] / errs[2] > 12    # ~16 por cada duplicación


def test_monforton_wu_equal_springs_closed_form():
    EI, L = 2.0e12, 4000.0
    K6 = beam_stiffness_2d(L, EI=EI, EA=1.0e9, n=2)
    Kb = K6[np.ix_([1, 2, 4, 5], [1, 2, 4, 5])]
    for R in (3 * EI / L, 10 * EI / L, 0.5 * EI / L):
        g = 1.0 / (1.0 + 3 * EI / (R * L))
        Ks = semi_rigid_bending_stiffness(Kb, R, R)
        assert Ks[1, 1] == pytest.approx(4 * EI / L * 3 * g / (4 - g * g), rel=1e-9)
        assert Ks[1, 3] == pytest.approx(2 * EI / L * 3 * g * g / (4 - g * g), rel=1e-9)
    Ks = semi_rigid_bending_stiffness(Kb, 3 * EI / L, 3 * EI / L)
    assert Ks[1, 1] == pytest.approx(1.6 * EI / L) and Ks[1, 3] == pytest.approx(0.4 * EI / L)


def test_monforton_wu_unequal_springs_closed_form():
    EI, L = 2.0e12, 4000.0
    K6 = beam_stiffness_2d(L, EI=EI, EA=1.0e9, n=2)
    Kb = K6[np.ix_([1, 2, 4, 5], [1, 2, 4, 5])]
    Ri, Rj = 3 * EI / L, 12 * EI / L
    gi, gj = 1 / (1 + 3 * EI / (Ri * L)), 1 / (1 + 3 * EI / (Rj * L))
    Ks = semi_rigid_bending_stiffness(Kb, Ri, Rj)
    assert Ks[1, 1] == pytest.approx(4 * EI / L * 3 * gi / (4 - gi * gj), rel=1e-9)
    assert Ks[3, 3] == pytest.approx(4 * EI / L * 3 * gj / (4 - gi * gj), rel=1e-9)
    assert Ks[1, 3] == pytest.approx(2 * EI / L * 3 * gi * gj / (4 - gi * gj), rel=1e-9)

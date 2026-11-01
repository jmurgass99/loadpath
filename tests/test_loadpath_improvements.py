"""Tests para mejoras de loadpath: Simpson por tramos, propiedades Clase 4 y clasificación EC3."""
from __future__ import annotations

import math
import numpy as np
import pytest

from loadpath import FrameSection
from loadpath.fea import (
    beam_stiffness_2d,
    classify_connection_ec3,
    fixity_factor_monforton_wu,
)


def test_piecewise_simpson_stepped_beam_exact():
    """Viga escalonada en x = L/2: la cuadratura por tramos coincide con la analítica exacta."""
    L = 4000.0
    EI1 = 2.0e12
    EI2 = 1.0e12
    EA1 = 2.0e9
    EA2 = 1.0e9

    def EI_step(x: float) -> float:
        return EI1 if x < L / 2.0 else EI2

    def EA_step(x: float) -> float:
        return EA1 if x < L / 2.0 else EA2

    K_pw = beam_stiffness_2d(L, EI=EI_step, EA=EA_step, n=8, breakpoints_x=[L / 2.0])

    # Solución analítica exacta de la flexibilidad D = int_0^L [L-x, 1]^T [L-x, 1] / EI(x) dx
    # Tramo 1: [0, L/2] -> u = L-x va de L a L/2
    # Tramo 2: [L/2, L] -> u = L-x va de L/2 a 0
    d11 = ((L**3 - (L / 2.0)**3) / 3.0) / EI1 + (((L / 2.0)**3) / 3.0) / EI2
    d12 = ((L**2 - (L / 2.0)**2) / 2.0) / EI1 + (((L / 2.0)**2) / 2.0) / EI2
    d22 = (L / 2.0) / EI1 + (L / 2.0) / EI2
    D_exact = np.array([[d11, d12], [d12, d22]])
    Kjj_exact = np.linalg.inv(D_exact)
    ka_exact = 1.0 / ((L / 2.0) / EA1 + (L / 2.0) / EA2)

    assert K_pw[0, 0] == pytest.approx(ka_exact, rel=1e-11)
    assert np.allclose(K_pw[np.ix_([4, 5], [4, 5])], Kjj_exact, rtol=1e-11)


def test_frame_section_class4_effective_properties():
    sec = FrameSection(
        name="C200x2.0",
        A_mm2=1200.0,
        Ix_mm4=6.5e6,
        Iy_mm4=1.1e6,
        J_mm4=1600.0,
        section_class=4,
        A_eff_mm2=920.0,
        Ix_eff_mm4=5.4e6,
        Iy_eff_mm4=0.95e6,
        Sx_eff_mm3=54000.0,
        Sy_eff_mm3=19000.0,
    )
    assert sec.section_class == 4
    assert sec.A_eff_mm2 == pytest.approx(920.0)
    assert sec.Ix_eff_mm4 == pytest.approx(5.4e6)


def test_classify_connection_ec3_and_fixity_factor():
    EI = 2.0e12
    L = 4000.0
    # R = 3 EI / L -> kb = 3.0 (semirrígida), gamma = 0.5
    R_semi = 3.0 * EI / L
    res_semi = classify_connection_ec3(R_semi, EI, L, braced=True)
    assert res_semi["classification"] == "semi-rigid"
    assert res_semi["kb_dimensionless"] == pytest.approx(3.0)
    assert res_semi["fixity_factor_gamma"] == pytest.approx(0.5)

    # kb = 0.2 -> articulada
    res_pin = classify_connection_ec3(0.2 * EI / L, EI, L, braced=True)
    assert res_pin["classification"] == "pinned"

    # kb = 10 -> rígida en arriostrado, semirrígida en no arriostrado (umbral 25)
    res_braced = classify_connection_ec3(10.0 * EI / L, EI, L, braced=True)
    res_unbraced = classify_connection_ec3(10.0 * EI / L, EI, L, braced=False)
    assert res_braced["classification"] == "rigid"
    assert res_unbraced["classification"] == "semi-rigid"
    assert fixity_factor_monforton_wu(math.inf, EI, L) == 1.0
    assert fixity_factor_monforton_wu(0.0, EI, L) == 0.0

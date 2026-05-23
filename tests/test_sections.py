"""Tests de FrameSection."""
import pytest
from pydantic import ValidationError

from loadpath_core import FrameSection


def _w():
    # W14x90 aproximado (mm)
    return FrameSection(
        name="W14X90", A_mm2=17100.0, Ix_mm4=4.16e8, Iy_mm4=1.51e8,
        J_mm4=4.16e6, Zx_mm3=2.59e6, depth_mm=356.0, width_mm=369.0,
    )


class TestConstruction:
    def test_seccion_valida(self):
        s = _w()
        assert s.A_mm2 == 17100.0
        assert s.Cw_mm6 is None      # opcional
        assert s.Sx_mm3 is None      # opcional

    def test_minimo_obligatorio(self):
        s = FrameSection(name="dummy", A_mm2=1000.0, Ix_mm4=1e6, Iy_mm4=1e6, J_mm4=1e4)
        assert s.depth_mm is None

    def test_ejes_armonizados(self):
        s = _w()
        assert s.I_strong_axis_mm4 == s.Ix_mm4
        assert s.I_weak_axis_mm4 == s.Iy_mm4
        assert s.I_strong_mm4 == s.Ix_mm4
        assert s.I_weak_mm4 == s.Iy_mm4
        assert s.Z_strong_axis_mm3 == s.Zx_mm3
        assert s.Z_weak_axis_mm3 is None


class TestValidacion:
    def test_falta_J(self):
        with pytest.raises(ValidationError):
            FrameSection(name="x", A_mm2=1000.0, Ix_mm4=1e6, Iy_mm4=1e6)

    def test_area_no_positiva(self):
        with pytest.raises(ValidationError):
            FrameSection(name="x", A_mm2=0, Ix_mm4=1e6, Iy_mm4=1e6, J_mm4=1e4)

    def test_extra_prohibido(self):
        with pytest.raises(ValidationError):
            FrameSection(name="x", A_mm2=1, Ix_mm4=1, Iy_mm4=1, J_mm4=1, peso="pesado")

    def test_cw_negativo(self):
        with pytest.raises(ValidationError):
            FrameSection(name="x", A_mm2=1, Ix_mm4=1, Iy_mm4=1, J_mm4=1, Cw_mm6=-5)


class TestSerializacion:
    def test_round_trip(self):
        s = _w()
        assert FrameSection.model_validate(s.model_dump()) == s

    def test_json_schema_required(self):
        req = set(FrameSection.model_json_schema()["required"])
        assert req == {"name", "A_mm2", "Ix_mm4", "Iy_mm4", "J_mm4"}

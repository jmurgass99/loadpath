"""Tests de InternalForces."""
import pytest
from pydantic import ValidationError

from loadpath import InternalForces


class TestConstruction:
    def test_completo(self):
        f = InternalForces(
            member_id="V101", station_m=3.0, N_kN=-50.0,
            Vy_kN=20.0, Vz_kN=0.0, T_kNm=1.5, My_kNm=0.0, Mz_kNm=120.0,
        )
        assert f.member_id == "V101"
        assert f.Mz_kNm == 120.0

    def test_componentes_default_cero(self):
        # Solo lo obligatorio: el resto de fuerzas son 0.0.
        f = InternalForces(member_id="C1", station_m=0.0)
        assert (f.N_kN, f.Vy_kN, f.Vz_kN, f.T_kNm, f.My_kNm, f.Mz_kNm) == (0.0,) * 6

    def test_axial_traccion_positiva(self):
        assert InternalForces(member_id="m", station_m=0, N_kN=100.0).N_kN > 0


class TestValidacion:
    def test_falta_member_id(self):
        with pytest.raises(ValidationError):
            InternalForces(station_m=1.0)

    def test_station_negativa(self):
        with pytest.raises(ValidationError):
            InternalForces(member_id="m", station_m=-1.0)

    def test_extra_prohibido(self):
        with pytest.raises(ValidationError):
            InternalForces(member_id="m", station_m=0.0, Fx_kN=10.0)


class TestSerializacion:
    def test_round_trip(self):
        f = InternalForces(member_id="V1", station_m=2.5, Mz_kNm=80.0)
        assert InternalForces.model_validate(f.model_dump()) == f

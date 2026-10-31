"""Tests de StructuralMaterial."""
import pytest
from pydantic import ValidationError

from loadpath import MaterialType, StructuralMaterial


def _steel():
    return StructuralMaterial(
        name="A992", material_type="steel", E_MPa=200000.0,
        poisson=0.3, density_kg_m3=7850.0, Fy_MPa=345.0, Fu_MPa=450.0,
    )


class TestConstruction:
    def test_acero_valido(self):
        m = _steel()
        assert m.material_type is MaterialType.STEEL
        assert m.E_MPa == 200000.0
        assert m.Fy_MPa == 345.0
        assert m.fc_MPa is None  # opcional, no aplica a acero

    def test_hormigon_sin_fy(self):
        m = StructuralMaterial(
            name="C30", material_type="concrete", E_MPa=33000.0,
            poisson=0.2, density_kg_m3=2500.0, fc_MPa=30.0,
        )
        assert m.fc_MPa == 30.0
        assert m.Fy_MPa is None

    def test_material_type_desde_string(self):
        assert StructuralMaterial(
            name="x", material_type="cold_formed_steel", E_MPa=1, poisson=0.3, density_kg_m3=1,
        ).material_type is MaterialType.COLD_FORMED_STEEL


class TestValidacion:
    def test_falta_obligatorio(self):
        with pytest.raises(ValidationError):
            StructuralMaterial(name="x", material_type="steel", poisson=0.3, density_kg_m3=1)

    def test_extra_prohibido(self):
        with pytest.raises(ValidationError):
            StructuralMaterial(
                name="x", material_type="steel", E_MPa=1, poisson=0.3,
                density_kg_m3=1, foo="bar",
            )

    def test_E_no_positivo(self):
        with pytest.raises(ValidationError):
            StructuralMaterial(name="x", material_type="steel", E_MPa=0, poisson=0.3, density_kg_m3=1)

    def test_poisson_fuera_de_rango(self):
        with pytest.raises(ValidationError):
            StructuralMaterial(name="x", material_type="steel", E_MPa=1, poisson=0.7, density_kg_m3=1)

    def test_material_type_invalido(self):
        with pytest.raises(ValidationError):
            StructuralMaterial(name="x", material_type="adamantium", E_MPa=1, poisson=0.3, density_kg_m3=1)


class TestSerializacion:
    def test_round_trip(self):
        m = _steel()
        assert StructuralMaterial.model_validate(m.model_dump()) == m

    def test_json_schema_ok(self):
        schema = StructuralMaterial.model_json_schema()
        assert "E_MPa" in schema["properties"]
        assert set(schema["required"]) == {"name", "material_type", "E_MPa", "poisson", "density_kg_m3"}

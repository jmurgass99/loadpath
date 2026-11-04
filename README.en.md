# loadpath

[Español](README.md) · **English**

Structural data models (material, section, internal forces) in Pydantic v2, plus two member stiffness helpers.

[![CI](https://github.com/jmurgass99/loadpath/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/loadpath/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What it does

- `StructuralMaterial`, `FrameSection` and `InternalForces`: three validated models, with SI units in each field name and no unknown fields allowed.
- JSON Schema of the models, to generate types in other languages (one example converts it to TypeScript).
- Stiffness matrix of a tapered or haunched beam (piecewise EI(x)) and condensed stiffness of a beam with semi-rigid joints.

## Install

```bash
pip install git+https://github.com/jmurgass99/loadpath.git
```

## Example

```python
from loadpath import StructuralMaterial

steel = StructuralMaterial(
    name="S355", material_type="steel",
    E_MPa=210_000, poisson=0.3, density_kg_m3=7850, Fy_MPa=355, Fu_MPa=490,
)
print(steel.model_json_schema()["properties"].keys())

StructuralMaterial(name="X", material_type="steel", E_MPa=-1, poisson=0.3, density_kg_m3=7850)
# pydantic.ValidationError (E_MPa must be positive)
```

More cases in [`examples/`](examples).

## What it does not do

- No section or material catalog: it validates what it receives, it does not fill it in.
- No code checks (design resistances, buckling, section classification).
- It does not assemble or solve structures: `fea` gives element matrices.
- `FrameSection` stores properties, not geometry, and does not distinguish class 4 sections.

Details are in [docs/LIMITACIONES.md](docs/LIMITACIONES.md) (in Spanish).

## Tests

```bash
pip install -e ".[test]"
pytest -q
```

## License

MIT. See [LICENSE](LICENSE). Author: [Jesús Murgas](https://github.com/jmurgass99).

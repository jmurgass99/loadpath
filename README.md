# loadpath

**Español** · [English](README.en.md)

Modelos de datos estructurales (material, sección, esfuerzos) en Pydantic v2, y dos ayudas de rigidez de barra.

[![CI](https://github.com/jmurgass99/loadpath/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/loadpath/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

## Qué hace

- `StructuralMaterial`, `FrameSection` e `InternalForces`: tres modelos validados, con unidades SI en el nombre de cada campo y sin campos desconocidos.
- JSON Schema de los modelos, para generar tipos en otros lenguajes (hay un ejemplo que lo convierte a TypeScript).
- Matriz de rigidez de una viga acartelada o con cartelas (EI(x) a trozos) y rigidez condensada de una viga con nudos semirrígidos.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/loadpath.git
```

## Ejemplo

```python
from loadpath import StructuralMaterial

acero = StructuralMaterial(
    name="S355", material_type="steel",
    E_MPa=210_000, poisson=0.3, density_kg_m3=7850, Fy_MPa=355, Fu_MPa=490,
)
print(acero.model_json_schema()["properties"].keys())

StructuralMaterial(name="X", material_type="steel", E_MPa=-1, poisson=0.3, density_kg_m3=7850)
# pydantic.ValidationError (E_MPa debe ser positivo)
```

Más casos en [`examples/`](examples).

## Qué no hace

- No incluye catálogo de perfiles ni de materiales: valida lo que recibe, no lo rellena.
- No hace comprobaciones de norma (resistencias, pandeo, clasificación de secciones).
- No ensambla ni resuelve estructuras: `fea` da matrices de elemento.
- `FrameSection` guarda propiedades, no geometría, y no distingue secciones de clase 4.

El detalle está en [docs/LIMITACIONES.md](docs/LIMITACIONES.md).

## Pruebas

```bash
pip install -e ".[test]"
pytest -q
```

## Licencia

MIT. Ver [LICENSE](LICENSE). Autor: [Jesús Murgas](https://github.com/jmurgass99).

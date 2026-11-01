"""Del esquema JSON de Pydantic a una interfaz TypeScript para el frontend, sin dependencias.

`StructuralMaterial.model_json_schema()` devuelve JSON Schema 2020-12 con tipos, rangos
(`exclusiveMinimum`, `maximum`), descripciones y el enum de `material_type`. Un generador de
20 líneas lo convierte en una interfaz TypeScript con comentarios de unidad: es el camino por
el que la convención de unidades llega al navegador sin reescribirla.

Ejecutar:  python examples/material_json_schema_to_typescript_interface.py
"""
import json

from loadpath import StructuralMaterial

TS_TYPES = {"number": "number", "integer": "number", "string": "string", "boolean": "boolean"}


def ts_type(prop: dict, defs: dict) -> str:
    if "$ref" in prop:
        d = defs[prop["$ref"].rsplit("/", 1)[-1]]
        return " | ".join(json.dumps(v) for v in d["enum"]) if "enum" in d else d.get("title", "unknown")
    if "anyOf" in prop:
        return " | ".join(ts_type(p, defs) for p in prop["anyOf"])
    if prop.get("type") == "null":
        return "null"
    return TS_TYPES.get(prop.get("type"), "unknown")


def to_interface(model) -> str:
    s = model.model_json_schema()
    defs = s.get("$defs", {})
    req = set(s.get("required", []))
    lines = [f"/** {s.get('description', '').splitlines()[0]} */", f"export interface {s['title']} {{"]
    for name, prop in s["properties"].items():
        rng = []
        for k, sym in (("exclusiveMinimum", ">"), ("minimum", ">="), ("exclusiveMaximum", "<"), ("maximum", "<=")):
            if k in prop:
                rng.append(f"{sym} {prop[k]}")
        for p in prop.get("anyOf", []):
            for k, sym in (("exclusiveMinimum", ">"), ("minimum", ">="), ("maximum", "<=")):
                if k in p:
                    rng.append(f"{sym} {p[k]}")
        desc = prop.get("description", "")
        comment = " ".join(x for x in (desc, f"({', '.join(rng)})" if rng else "") if x)
        lines.append(f"  /** {comment} */" if comment else "")
        lines.append(f"  {name}{'' if name in req else '?'}: {ts_type(prop, defs)};")
    lines.append("}")
    return "\n".join(l for l in lines if l != "")


def main() -> None:
    schema = StructuralMaterial.model_json_schema()
    print(f"JSON Schema: {len(schema['properties'])} propiedades, obligatorias {schema['required']}, enum MaterialType con {len(schema['$defs']['MaterialType']['enum'])} valores\n")
    print(to_interface(StructuralMaterial))
    print("\nEl mismo generador sirve para FrameSection e InternalForces; `?` marca las propiedades opcionales (None en Python).")


if __name__ == "__main__":
    main()

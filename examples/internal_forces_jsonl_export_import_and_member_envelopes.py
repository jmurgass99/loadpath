"""Exportar los esfuerzos de un pórtico a JSON Lines, reimportarlos validados y sacar la envolvente por barra.

Un pórtico de tres barras (dos pilares y un dintel) con tres combinaciones; cada estación es
una línea JSON (formato que soportan `jq`, pandas y cualquier stream). Al leer, cada línea pasa
por `InternalForces.model_validate_json`, que rechaza una línea corrupta con el número de línea
en vez de propagar un NaN. Después se agrupa por barra y se imprime |N|, |V_z| y |M_z| máximos.

Ejecutar:  python examples/internal_forces_jsonl_export_import_and_member_envelopes.py
"""
import io
import random

from pydantic import ValidationError

from loadpath import InternalForces

random.seed(7)
BARRAS = {"P-1": 4.0, "D-1": 8.0, "P-2": 4.0}
COMBOS = ("ELU-1", "ELU-2", "ELS")


def generar() -> list[InternalForces]:
    out = []
    for barra, L in BARRAS.items():
        for combo in COMBOS:
            esc = {"ELU-1": 1.0, "ELU-2": 0.85, "ELS": 0.7}[combo]
            for i in range(5):
                x = L * i / 4
                n = -420.0 * esc if barra.startswith("P") else -35.0 * esc
                v = (60.0 - 30.0 * x) * esc if barra == "D-1" else 25.0 * esc
                m = (120.0 * x - 15.0 * x ** 2) * esc if barra == "D-1" else (-50.0 + 25.0 * x) * esc
                out.append(InternalForces(member_id=f"{barra}@{combo}", station_m=x, N_kN=n, Vz_kN=v, Mz_kNm=m))
    return out


def main() -> None:
    fs = generar()
    buf = io.StringIO()
    for f in fs:
        buf.write(f.model_dump_json() + "\n")
    buf.write('{"member_id": "X", "station_m": -1, "Mz_kNm": "nan"}\n')   # línea corrupta a propósito
    texto = buf.getvalue()
    print(f"Exportadas {len(fs)} estaciones en {len(texto)} bytes de JSONL (+1 línea corrupta de prueba)\n")

    leidas, errores = [], []
    for n, linea in enumerate(texto.splitlines(), 1):
        try:
            leidas.append(InternalForces.model_validate_json(linea))
        except ValidationError as e:
            errores.append((n, [x["type"] for x in e.errors()]))
    print(f"Reimportadas {len(leidas)} válidas; rechazadas: {errores}\n")

    env: dict[str, dict[str, float]] = {}
    for f in leidas:
        barra = f.member_id.split("@")[0]
        e = env.setdefault(barra, {"N": 0.0, "Vz": 0.0, "Mz": 0.0})
        e["N"], e["Vz"], e["Mz"] = max(e["N"], abs(f.N_kN)), max(e["Vz"], abs(f.Vz_kN)), max(e["Mz"], abs(f.Mz_kNm))
    print(f"  {'barra':6} {'|N| máx [kN]':>12} {'|V_z| máx [kN]':>14} {'|M_z| máx [kN·m]':>16}")
    for barra, e in env.items():
        print(f"  {barra:6} {e['N']:12.1f} {e['Vz']:14.1f} {e['Mz']:16.1f}")


if __name__ == "__main__":
    main()

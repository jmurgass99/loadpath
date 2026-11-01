"""Qué rechaza InternalForces y qué rellena por defecto: estación negativa, campos ajenos, tipos y estados parciales.

Casos: estación −1 m, un campo `Fx_kN` que no existe en el esquema (SAP2000 llama P, V2, V3,
T, M2, M3 a lo mismo: hay que mapear, no añadir), `member_id` ausente, momento como texto, y
el estado parcial válido con solo `member_id` y `station_m` (todo lo demás 0,0). Se imprime
también un mapeo SAP2000 → esquema como el que usaría un importador.

Ejecutar:  python examples/internal_forces_validation_station_negative_extra_field_and_defaults.py
"""
from pydantic import ValidationError

from loadpath import InternalForces

SAP_A_ESQUEMA = {"P": "N_kN", "V2": "Vy_kN", "V3": "Vz_kN", "T": "T_kNm", "M2": "My_kNm", "M3": "Mz_kNm"}


def main() -> None:
    parcial = InternalForces(member_id="C-1", station_m=0.0)
    print("Estado parcial válido:", parcial.model_dump())
    casos = [
        ("estación −1 m", dict(member_id="m", station_m=-1.0)),
        ("campo `Fx_kN`", dict(member_id="m", station_m=0.0, Fx_kN=10.0)),
        ("sin member_id", dict(station_m=1.0, Mz_kNm=10.0)),
        ("M_z como texto", dict(member_id="m", station_m=1.0, Mz_kNm="diez")),
        ("dos errores a la vez", dict(member_id="m", station_m=-2.0, Mz_kNm="x", extra=1)),
    ]
    print()
    for titulo, datos in casos:
        try:
            InternalForces(**datos)
        except ValidationError as e:
            print(f"  {titulo:22} → {e.error_count()} error(es): " + "; ".join(f"{x['type']} en {'.'.join(str(p) for p in x['loc'])}" for x in e.errors()))
    fila_sap = {"Frame": "V-12", "Station": 3.0, "P": -12.0, "V2": 0.0, "V3": 48.0, "T": 0.0, "M2": 0.0, "M3": 72.0}
    f = InternalForces(member_id=fila_sap["Frame"], station_m=fila_sap["Station"], **{SAP_A_ESQUEMA[k]: v for k, v in fila_sap.items() if k in SAP_A_ESQUEMA})
    print(f"\nFila de SAP2000 mapeada: {f.model_dump()}")
    print("El mapeo vive en el importador (y debe declarar el convenio de signo de P); el esquema no acepta los nombres del programa de origen.")


if __name__ == "__main__":
    main()

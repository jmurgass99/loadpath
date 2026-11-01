"""Esfuerzos por estaciones de una viga biapoyada con carga uniforme, como lista de InternalForces.

Viga V-12 de 6 m con q = 24 kN/m (1,35·12 + 1,5·5,2): V(x) = q·(L/2 − x), M(x) = q·x·(L − x)/2.
Se generan 13 estaciones (cada 0,5 m) con el convenio del esquema (M_z = flexión fuerte,
V_z el cortante que la acompaña), se busca la envolvente y se comprueba contra las formas
cerradas q·L/2 = 72 kN y q·L²/8 = 108 kN·m. Es el formato con el que un solver entrega
resultados a un comprobador de secciones o a un informe.

Ejecutar:  python examples/internal_forces_simply_supported_beam_stations_udl_envelope.py
"""
from loadpath import InternalForces

L, Q = 6.0, 24.0


def estaciones(member: str, n: int = 12) -> list[InternalForces]:
    out = []
    for i in range(n + 1):
        x = L * i / n
        out.append(InternalForces(member_id=member, station_m=x, Vz_kN=Q * (L / 2 - x), Mz_kNm=Q * x * (L - x) / 2))
    return out


def main() -> None:
    fs = estaciones("V-12")
    print(f"  {'x [m]':>5} {'V_z [kN]':>9} {'M_z [kN·m]':>10}")
    for f in fs:
        print(f"  {f.station_m:5.1f} {f.Vz_kN:9.1f} {f.Mz_kNm:10.1f}")
    vmax = max(fs, key=lambda f: abs(f.Vz_kN))
    mmax = max(fs, key=lambda f: f.Mz_kNm)
    print(f"\nEnvolvente: |V_z| máx = {abs(vmax.Vz_kN):.1f} kN en x = {vmax.station_m:.1f} m (q·L/2 = {Q * L / 2:.1f}); "
          f"M_z máx = {mmax.Mz_kNm:.1f} kN·m en x = {mmax.station_m:.1f} m (q·L²/8 = {Q * L ** 2 / 8:.1f})")
    print(f"Serializado: {len(fs)} estaciones, {len(fs[6].model_dump_json())} bytes cada una; ejemplo: {fs[6].model_dump_json()}")
    print("N, V_y, T y M_y quedan en 0,0 por defecto: un estado parcial es válido y explícito.")


if __name__ == "__main__":
    main()

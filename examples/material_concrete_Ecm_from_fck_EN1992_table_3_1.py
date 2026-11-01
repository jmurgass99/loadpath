"""Hormigones C20/25 a C50/60 con E_cm derivado de f_ck según EN 1992-1-1 Tabla 3.1.

    f_cm = f_ck + 8 MPa          E_cm = 22·(f_cm/10)^0,3 GPa          (Tabla 3.1, cuarcita)

La tabla imprime E_cm redondeado al GPa: C20/25 → 30, C30/37 → 33, C40/50 → 35, C50/60 → 37.
Se construye un `StructuralMaterial` por clase, se compara con el valor tabulado y se añade el
factor para áridos de caliza (×0,9) y arenisca (×0,7) de §3.1.3(2). ν = 0,2 (§3.1.3(4)) y
ρ = 2 500 kg/m³ (hormigón armado, EN 1991-1-1 Tabla A.1).

Ejecutar:  python examples/material_concrete_Ecm_from_fck_EN1992_table_3_1.py
"""
from loadpath import StructuralMaterial

TABLA_3_1 = {20: 30, 25: 31, 30: 33, 35: 34, 40: 35, 45: 36, 50: 37}   # f_ck → E_cm [GPa]
CUBO = {20: 25, 25: 30, 30: 37, 35: 45, 40: 50, 45: 55, 50: 60}             # f_ck,cyl → f_ck,cube


def hormigon(fck: int, arido: str = "cuarcita") -> StructuralMaterial:
    fcm = fck + 8.0
    Ecm = 22.0 * (fcm / 10.0) ** 0.3 * 1000.0
    Ecm *= {"cuarcita": 1.0, "caliza": 0.9, "arenisca": 0.7, "basalto": 1.2}[arido]
    return StructuralMaterial(name=f"C{fck}/{CUBO[fck]} {arido}", material_type="concrete",
                              E_MPa=Ecm, poisson=0.2, density_kg_m3=2500, fc_MPa=fck, damping_ratio=0.05)


def main() -> None:
    print(f"  {'clase':16} {'f_ck':>5} {'f_cm':>5} {'E_cm calc [GPa]':>15} {'Tabla 3.1':>9} {'desvío':>7}")
    for fck, Et in TABLA_3_1.items():
        m = hormigon(fck)
        print(f"  {m.name:16} {m.fc_MPa:5.0f} {fck + 8:5.0f} {m.E_MPa / 1000:15.2f} {Et:9d} {(m.E_MPa / 1000 - Et) / Et * 100:+6.1f} %")
    print("\nEfecto del árido para C30/37 (§3.1.3(2)):")
    for arido in ("cuarcita", "caliza", "arenisca", "basalto"):
        print(f"  {arido:9} E_cm = {hormigon(30, arido).E_MPa / 1000:5.1f} GPa")
    print("\nLa fórmula reproduce la tabla con desvíos < 2 % (la tabla redondea al GPa; C25/30 es el peor caso, 31,5 frente a 31); el módulo que viaja en el esquema es el calculado, no el redondeado.")


if __name__ == "__main__":
    main()

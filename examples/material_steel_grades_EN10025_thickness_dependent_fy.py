"""Aceros S235 a S460 con el límite elástico que depende del espesor (EN 10025-2 Tabla 7 y EN 1993-1-1 Tabla 3.1).

El límite elástico nominal baja con el espesor del producto: para S355, 355 MPa hasta 16 mm,
345 entre 16 y 40, 335 entre 40 y 63, 325 entre 63 y 80 (EN 10025-2); EN 1993-1-1 Tabla 3.1
simplifica a dos tramos (t <= 40: 355; 40 < t <= 80: 335). Un material por grado y tramo de
espesor evita el error clásico de usar 355 en una chapa de 50 mm. Se construye el catálogo con
los tramos de EN 10025-2 y se compara con la simplificación de EN 1993-1-1 para t = 50 mm.

Ejecutar:  python examples/material_steel_grades_EN10025_thickness_dependent_fy.py
"""
from loadpath import StructuralMaterial

# EN 10025-2 Tabla 7: (t_max [mm], f_y) por grado; f_u del tramo 3–100 mm
EN10025 = {
    "S235": ([(16, 235), (40, 225), (63, 215), (80, 215)], 360),
    "S275": ([(16, 275), (40, 265), (63, 255), (80, 245)], 410),
    "S355": ([(16, 355), (40, 345), (63, 335), (80, 325)], 470),
    "S460": ([(16, 460), (40, 440), (63, 430), (80, 410)], 540),
}
EN1993 = {"S235": (235, 215), "S275": (275, 255), "S355": (355, 335), "S460": (440, 410)}   # t <= 40 / 40 < t <= 80


def acero(grado: str, t_mm: float) -> StructuralMaterial:
    tramos, fu = EN10025[grado]
    fy = next(f for tmax, f in tramos if t_mm <= tmax)
    return StructuralMaterial(name=f"{grado} t={t_mm:g} mm", material_type="steel", E_MPa=210_000, poisson=0.3,
                              density_kg_m3=7850, Fy_MPa=fy, Fu_MPa=fu)


def main() -> None:
    print(f"  {'grado':6}" + "".join(f"{'t=' + str(t):>9}" for t in (10, 20, 50, 70)) + "   (f_y en MPa, EN 10025-2)")
    for g in EN10025:
        print(f"  {g:6}" + "".join(f"{acero(g, t).Fy_MPa:9.0f}" for t in (10, 20, 50, 70)))
    print("\nChapa de 50 mm: EN 10025-2 frente a la simplificación de EN 1993-1-1 Tabla 3.1 (40 < t <= 80):")
    for g in EN10025:
        print(f"  {g}: {acero(g, 50).Fy_MPa:.0f} MPa frente a {EN1993[g][1]} MPa; usar el nominal de t <= 16 ({EN10025[g][0][0][1]}) sobrestimaría un {(EN10025[g][0][0][1] / acero(g, 50).Fy_MPa - 1) * 100:.0f} %")
    m = acero("S355", 50)
    print(f"\nEjemplo serializado: {m.model_dump_json()}")


if __name__ == "__main__":
    main()

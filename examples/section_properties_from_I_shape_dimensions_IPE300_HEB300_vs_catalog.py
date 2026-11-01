"""Propiedades de un perfil en I a partir de sus dimensiones y contraste con el catálogo (IPE 300, HEB 300).

Fórmulas de la sección idealizada (tres rectángulos) más la corrección de área por acuerdos
(4 − π)·r²:
    A = 2·b·t_f + (h − 2·t_f)·t_w + (4 − π)·r²
    I_x = [b·h³ − (b − t_w)·(h − 2·t_f)³]/12            I_y = [2·t_f·b³ + (h − 2·t_f)·t_w³]/12
    W_el,x = 2·I_x/h        W_pl,x = b·t_f·(h − t_f) + t_w·(h − 2·t_f)²/4
    I_t ≈ [2·b·t_f³ + (h − 2·t_f)·t_w³]/3   (pared delgada, sin acuerdos)      I_w = I_y·(h − t_f)²/4

Catálogo (EN 10365 / ArcelorMittal): IPE 300 A = 53,8 cm², I_y = 8 356, I_z = 604, W_pl = 628 cm³,
I_t = 20,1 cm⁴, I_w = 126·10³ cm⁶; HEB 300 A = 149,1, I_y = 25 170, I_z = 8 563, W_pl = 1 869, I_t = 185,
I_w = 1 688·10³. La torsión sin acuerdos queda un 20–25 % corta: para I_t hay que usar el catálogo.
Nota de ejes: en el esquema x es el eje fuerte (I_x), que los catálogos europeos llaman y-y.

Ejecutar:  python examples/section_properties_from_I_shape_dimensions_IPE300_HEB300_vs_catalog.py
"""
from math import pi

from loadpath import FrameSection

PERFILES = {  # h, b, tw, tf, r  [mm]  y catálogo (A cm², Ix cm⁴, Iy cm⁴, Wpl cm³, It cm⁴, Iw 1e3 cm⁶)
    "IPE 300": ((300.0, 150.0, 7.1, 10.7, 15.0), (53.8, 8356, 604, 628, 20.1, 126)),
    "HEB 300": ((300.0, 300.0, 11.0, 19.0, 27.0), (149.1, 25170, 8563, 1869, 185, 1688)),
}


def i_shape(name: str, h: float, b: float, tw: float, tf: float, r: float) -> FrameSection:
    hw = h - 2 * tf
    A = 2 * b * tf + hw * tw + (4 - pi) * r ** 2
    Ix = (b * h ** 3 - (b - tw) * hw ** 3) / 12
    Iy = (2 * tf * b ** 3 + hw * tw ** 3) / 12
    J = (2 * b * tf ** 3 + hw * tw ** 3) / 3
    Cw = Iy * (h - tf) ** 2 / 4
    Sx = 2 * Ix / h
    Zx = b * tf * (h - tf) + tw * hw ** 2 / 4
    Sy = 2 * Iy / b
    Zy = (tf * b ** 2) / 2 + hw * tw ** 2 / 4
    return FrameSection(name=name, A_mm2=A, Ix_mm4=Ix, Iy_mm4=Iy, J_mm4=J, Cw_mm6=Cw, Sx_mm3=Sx, Zx_mm3=Zx, Sy_mm3=Sy, Zy_mm3=Zy,
                        depth_mm=h, width_mm=b)


def main() -> None:
    for name, (dims, cat) in PERFILES.items():
        s = i_shape(name, *dims)
        calc = (s.A_mm2 / 1e2, s.Ix_mm4 / 1e4, s.Iy_mm4 / 1e4, s.Zx_mm3 / 1e3, s.J_mm4 / 1e4, s.Cw_mm6 / 1e9)
        print(f"{name}: h = {dims[0]:.0f}, b = {dims[1]:.0f}, t_w = {dims[2]}, t_f = {dims[3]}, r = {dims[4]:.0f} mm")
        print(f"  {'':10} {'A [cm²]':>8} {'I_x [cm⁴]':>10} {'I_y [cm⁴]':>10} {'W_pl,x [cm³]':>12} {'I_t [cm⁴]':>9} {'I_w [10³ cm⁶]':>13}")
        print(f"  {'calculado':10} {calc[0]:8.1f} {calc[1]:10.0f} {calc[2]:10.0f} {calc[3]:12.0f} {calc[4]:9.1f} {calc[5]:13.0f}")
        print(f"  {'catálogo':10} {cat[0]:8.1f} {cat[1]:10.0f} {cat[2]:10.0f} {cat[3]:12.0f} {cat[4]:9.1f} {cat[5]:13.0f}")
        print(f"  {'desvío':10} " + " ".join(f"{(c / k - 1) * 100:+{w}.1f} %" for c, k, w in zip(calc, cat, (6, 8, 8, 10, 7, 11))))
        print()
    print("La corrección (4 − π)·r² deja el área exacta; en I_x y W_pl los acuerdos aportan ~4 % y en I_t un 20–25 %: I_y e I_w salen bien, I_t se toma de catálogo.")


if __name__ == "__main__":
    main()

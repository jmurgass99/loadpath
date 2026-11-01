"""Perfiles tubulares: RHS 200×100×8 y CHS 219,1×8 desde sus dimensiones, contrastados con EN 10210.

    CHS: A = π·(D² − d²)/4, I = π·(D⁴ − d⁴)/64, I_t = 2·I, W_el = 2·I/D, W_pl = (D³ − d³)/6
    RHS (esquinas vivas): A = b·h − b_i·h_i, I = (b·h³ − b_i·h_i³)/12,
         I_t ≈ 4·A_m²·t/p_m (Bredt, línea media), W_pl = b·t·(h − t) + t·(h − 2t)²/2

Catálogo EN 10210 (acabado en caliente): RHS 200×100×8 A = 44,8 cm², I_y = 2 269, I_z = 747,
I_t = 1 804 cm⁴, W_pl,y = 283 cm³; CHS 219,1×8 A = 53,1 cm², I = 2 960 cm⁴, I_t = 5 919 cm⁴,
W_pl = 357 cm³. Las esquinas redondeadas (r_o = 1,5·t) explican el 1–3 % de desvío del RHS;
el CHS sale exacto. El alabeo de un tubo cerrado es despreciable: C_w = 0.

Ejecutar:  python examples/section_hollow_sections_RHS_CHS_from_dimensions_vs_EN10210.py
"""
from math import pi

from loadpath import FrameSection


def chs(name: str, D: float, t: float) -> FrameSection:
    d = D - 2 * t
    A = pi * (D ** 2 - d ** 2) / 4
    I = pi * (D ** 4 - d ** 4) / 64
    return FrameSection(name=name, A_mm2=A, Ix_mm4=I, Iy_mm4=I, J_mm4=2 * I, Cw_mm6=0.0,
                        Sx_mm3=2 * I / D, Sy_mm3=2 * I / D, Zx_mm3=(D ** 3 - d ** 3) / 6, Zy_mm3=(D ** 3 - d ** 3) / 6,
                        depth_mm=D, width_mm=D)


def rhs(name: str, h: float, b: float, t: float) -> FrameSection:
    hi, bi = h - 2 * t, b - 2 * t
    A = b * h - bi * hi
    Ix = (b * h ** 3 - bi * hi ** 3) / 12
    Iy = (h * b ** 3 - hi * bi ** 3) / 12
    Am, pm = (b - t) * (h - t), 2 * ((b - t) + (h - t))
    J = 4 * Am ** 2 * t / pm
    return FrameSection(name=name, A_mm2=A, Ix_mm4=Ix, Iy_mm4=Iy, J_mm4=J, Cw_mm6=0.0,
                        Sx_mm3=2 * Ix / h, Sy_mm3=2 * Iy / b,
                        Zx_mm3=b * t * (h - t) + t * hi ** 2 / 2, Zy_mm3=h * t * (b - t) + t * bi ** 2 / 2,
                        depth_mm=h, width_mm=b)


def main() -> None:
    casos = [
        (rhs("RHS 200x100x8", 200.0, 100.0, 8.0), (44.8, 2269, 747, 1804, 283)),
        (chs("CHS 219.1x8", 219.1, 8.0), (53.1, 2960, 2960, 5919, 357)),
    ]
    print(f"  {'perfil':16} {'':10} {'A [cm²]':>8} {'I_x [cm⁴]':>10} {'I_y [cm⁴]':>10} {'I_t [cm⁴]':>10} {'W_pl,x [cm³]':>12}")
    for s, cat in casos:
        calc = (s.A_mm2 / 1e2, s.Ix_mm4 / 1e4, s.Iy_mm4 / 1e4, s.J_mm4 / 1e4, s.Zx_mm3 / 1e3)
        print(f"  {s.name:16} {'calculado':10} {calc[0]:8.1f} {calc[1]:10.0f} {calc[2]:10.0f} {calc[3]:10.0f} {calc[4]:12.0f}")
        print(f"  {'':16} {'EN 10210':10} {cat[0]:8.1f} {cat[1]:10.0f} {cat[2]:10.0f} {cat[3]:10.0f} {cat[4]:12.0f}")
        print(f"  {'':16} {'desvío':10} " + " ".join(f"{(c / k - 1) * 100:+{w}.1f} %" for c, k, w in zip(calc, cat, (6, 8, 8, 8, 10))))
    print("\nEl RHS sale 1–3 % alto por las esquinas vivas (el catálogo tiene r_o = 1,5·t); Bredt da la torsión a −2,6 %. El CHS es exacto porque la fórmula es la geometría real.")


if __name__ == "__main__":
    main()

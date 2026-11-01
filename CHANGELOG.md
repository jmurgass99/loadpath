# Changelog

## 0.1.1 — 2026-11-01

Sin cambios de comportamiento en el paquete; revisión de documentación, ejemplos y tests.

- Tests de forma cerrada nuevos (`tests/test_fea_closed_form_golden.py`): flexibilidad del voladizo con EI(x) = EI₀·(1 + x/L) (D₀₀ = (4·ln 2 − 5/2)·L³/EI₀, D₀₁ = (2·ln 2 − 1)·L²/EI₀, D₁₁ = ln 2·L/EI₀), convergencia de orden 4 de Simpson y las fórmulas de Monforton y Wu (1963) para resortes iguales y distintos (γ = 1/(1 + 3EI/(R·L)), k_θiθi = (4EI/L)·3γ_i/(4 − γ_iγ_j)). Hasta ahora las ayudas FEA solo tenían los límites rígido/articulado y cotas.
- 20 casos de uso ejecutados en `examples/` (materiales, secciones, esfuerzos y contrato JSON, ayudas FEA) con su salida en `examples/output/`. Sustituyen a los dos ejemplos genéricos; el de nudos semirrígidos pasaba una rigidez adimensional (k·L/EI) donde el helper espera kN·m/rad y todo salía articulado.
- README reescrito; descripción y keywords del paquete.

## 0.1.0

Publicación inicial como repositorio independiente (origen: `loadpath-core` del monorepo Structural JM).

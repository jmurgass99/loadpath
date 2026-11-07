# Limitaciones conocidas de loadpath

Lo que el paquete no hace o hace de forma simplificada.

- No hay catálogo de perfiles ni de materiales: el paquete valida lo que recibe, no lo rellena.
- `FrameSection` no distingue secciones de clase 4 ni almacena geometría (alas, almas); las propiedades eficaces son responsabilidad del productor.
- `InternalForces` es una estación de barra; no modela esfuerzos de placa, apoyos ni combinaciones (el identificador de combinación va en `member_id` o en el modelo compuesto del consumidor).
- `beam_stiffness_2d` es flexión plana con hipótesis de Euler-Bernoulli (sin deformación por cortante) y EI(x) dado por el usuario; con EI a trozos, pasa los quiebros en `breakpoints_x` (Simpson por tramos) o usa un n suficiente para que caigan cerca de un nodo de Simpson.
- `semi_rigid_bending_stiffness` recibe R en las unidades de K_b (kN·m/rad si K_b está en kN y m); pasar una rigidez relativa k·L/EI hace que todo salga articulado.
- Los convenios de ejes (x fuerte, M_z fuerte) son los del ecosistema Loadpath y de SAP2000; otros programas usan otros y el mapeo es tarea del importador.

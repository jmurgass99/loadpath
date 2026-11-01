"""Mapeo semántico -> malla MEF (``GeometryMapping``) y solver de pórticos 2D
con uniones semirrígidas (Monforton-Wu / EN 1993-1-8) y cargas distribuidas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import math
import numpy as np

from .semi_rigid import (
    classify_connection_ec3,
    fixity_factor_monforton_wu,
    semi_rigid_bending_stiffness,
)


@dataclass
class GeometryMapping:
    """Mapeo bidireccional entre geometría semántica y malla discreta MEF."""

    point_to_nodes: Dict[int, int] = field(default_factory=dict)
    line_to_elements: Dict[int, List[int]] = field(default_factory=dict)
    nodes: List[Tuple[float, float, float]] = field(default_factory=list)
    elements: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class SemanticFrameInput:
    """Modelo semántico de pórtico con apoyos, cargas por barra y resortes rotacionales."""

    points: Dict[int, Tuple[float, float, float]]
    lines: Dict[int, Tuple[int, int]]
    supports: Dict[int, Tuple[bool, bool, bool]] = field(default_factory=dict)
    point_loads_kN: Dict[int, Tuple[float, float, float]] = field(default_factory=dict)
    distributed_loads_kN_m: Dict[int, float] = field(default_factory=dict)
    end_springs_kNm_rad: Dict[int, Tuple[float, float]] = field(default_factory=dict)
    E_MPa: float = 210_000.0
    A_mm2: float = 5_380.0
    I_mm4: float = 8.356e7
    divisions: int = 5


def build_frame_mesh(inp: SemanticFrameInput) -> GeometryMapping:
    """Subdivide cada barra semántica en ``inp.divisions`` elementos finitos
    manteniendo invariantes ``point_to_nodes`` y ``line_to_elements``.
    """
    n_div = max(1, int(inp.divisions))
    point_to_nodes: Dict[int, int] = {}
    line_to_elements: Dict[int, List[int]] = {}
    nodes: List[Tuple[float, float, float]] = []
    elements: List[Tuple[int, int]] = []

    for pt_id in sorted(inp.points.keys()):
        c = inp.points[pt_id]
        point_to_nodes[pt_id] = len(nodes)
        nodes.append((float(c[0]), float(c[1]), float(c[2])))

    for line_id in sorted(inp.lines.keys()):
        p1, p2 = inp.lines[line_id]
        n1 = point_to_nodes[p1]
        n2 = point_to_nodes[p2]
        c1, c2 = nodes[n1], nodes[n2]

        chain: List[int] = [n1]
        for k in range(1, n_div):
            t = k / float(n_div)
            chain.append(len(nodes))
            nodes.append((
                c1[0] + t * (c2[0] - c1[0]),
                c1[1] + t * (c2[1] - c1[1]),
                c1[2] + t * (c2[2] - c1[2]),
            ))
        chain.append(n2)

        el_ids: List[int] = []
        for k in range(n_div):
            el_ids.append(len(elements))
            elements.append((chain[k], chain[k + 1]))
        line_to_elements[line_id] = el_ids

    return GeometryMapping(
        point_to_nodes=point_to_nodes,
        line_to_elements=line_to_elements,
        nodes=nodes,
        elements=elements,
    )


def solve_semantic_frame(inp: SemanticFrameInput) -> Dict[str, object]:
    """Ensambla y resuelve el pórtico subdividido en el plano X-Z considerando
    resortes semirrígidos en extremos de barra semántica y cargas distribuidas.
    """
    mapping = build_frame_mesh(inp)
    n_nodes = len(mapping.nodes)
    n_dof = 3 * n_nodes  # [ux, uz, ry] en metros y radianes, fuerzas en N

    E = float(inp.E_MPa) * 1e6     # Pa
    A = float(inp.A_mm2) * 1e-6    # m^2
    I = float(inp.I_mm4) * 1e-12   # m^4

    K = np.zeros((n_dof, n_dof), dtype=float)
    F = np.zeros(n_dof, dtype=float)

    for pt_id, (fx, fz, my) in inp.point_loads_kN.items():
        if pt_id in mapping.point_to_nodes:
            ni = mapping.point_to_nodes[pt_id]
            F[3 * ni] += float(fx) * 1e3
            F[3 * ni + 1] += float(fz) * 1e3
            F[3 * ni + 2] += float(my) * 1e3

    elem_records = []
    connection_classes: Dict[int, str] = {}

    for line_id, el_indices in mapping.line_to_elements.items():
        p1, p2 = inp.lines[line_id]
        c_start = mapping.nodes[mapping.point_to_nodes[p1]]
        c_end = mapping.nodes[mapping.point_to_nodes[p2]]
        L_line_m = math.hypot(c_end[0] - c_start[0], c_end[2] - c_start[2]) or 1.0

        s_pair = inp.end_springs_kNm_rad.get(line_id, (1e12, 1e12))
        sj_i_Nm = float(s_pair[0]) * 1e3
        sj_j_Nm = float(s_pair[1]) * 1e3
        cls_info = classify_connection_ec3(
            Sj_ini=min(sj_i_Nm, sj_j_Nm),
            EI=E * I,
            L=L_line_m,
        )
        connection_classes[line_id] = cls_info["classification"].replace("-", "_")

        q_N_m = float(inp.distributed_loads_kN_m.get(line_id, 0.0)) * 1e3
        n_el = len(el_indices)

        for pos_idx, e_idx in enumerate(el_indices):
            na, nb = mapping.elements[e_idx]
            ca, cb = mapping.nodes[na], mapping.nodes[nb]
            dx = cb[0] - ca[0]
            dz = cb[2] - ca[2]
            L = math.hypot(dx, dz) or 1.0
            c, s = dx / L, dz / L

            # Apply rotational spring only at the first/last sub-element of the semantic line
            ri_Nm = sj_i_Nm if pos_idx == 0 else math.inf
            rj_Nm = sj_j_Nm if pos_idx == n_el - 1 else math.inf

            k12 = 12.0 * E * I / (L ** 3)
            k6 = 6.0 * E * I / (L ** 2)
            k4 = 4.0 * E * I / L
            k2 = 2.0 * E * I / L
            Kb_base = np.array([
                [k12, k6, -k12, k6],
                [k6, k4, -k6, k2],
                [-k12, -k6, k12, -k6],
                [k6, k2, -k6, k4],
            ], dtype=float)
            k_b = semi_rigid_bending_stiffness(Kb_base, Ri=ri_Nm, Rj=rj_Nm)

            ea_L = E * A / L
            k_loc = np.zeros((6, 6), dtype=float)
            k_loc[0, 0] = ea_L
            k_loc[0, 3] = -ea_L
            k_loc[3, 0] = -ea_L
            k_loc[3, 3] = ea_L
            b_idx = [1, 2, 4, 5]
            k_loc[np.ix_(b_idx, b_idx)] = k_b

            T = np.array([
                [c, s, 0, 0, 0, 0],
                [-s, c, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [0, 0, 0, c, s, 0],
                [0, 0, 0, -s, c, 0],
                [0, 0, 0, 0, 0, 1],
            ], dtype=float)

            dofs = [3 * na, 3 * na + 1, 3 * na + 2, 3 * nb, 3 * nb + 1, 3 * nb + 2]
            K[np.ix_(dofs, dofs)] += T.T @ k_loc @ T

            if abs(q_N_m) > 1e-9:
                f_loc = np.array([0.0, 0.5 * q_N_m * L, q_N_m * L * L / 12.0, 0.0, 0.5 * q_N_m * L, -q_N_m * L * L / 12.0])
                F[dofs] += T.T @ f_loc
            else:
                f_loc = np.zeros(6, dtype=float)

            elem_records.append((line_id, dofs, k_loc, T, f_loc))

    fixed: List[int] = []
    for pt_id, flags in inp.supports.items():
        if pt_id in mapping.point_to_nodes:
            ni = mapping.point_to_nodes[pt_id]
            if flags[0]:
                fixed.append(3 * ni)
            if flags[1]:
                fixed.append(3 * ni + 1)
            if flags[2]:
                fixed.append(3 * ni + 2)

    all_dofs = np.arange(n_dof)
    free = np.setdiff1d(all_dofs, np.unique(fixed))
    u = np.zeros(n_dof, dtype=float)
    if free.size > 0:
        u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])

    reactions = K @ u - F
    deformed_positions: List[float] = []
    for i, (nx, ny, nz) in enumerate(mapping.nodes):
        deformed_positions.extend([
            round(nx + float(u[3 * i]), 6),
            round(ny, 6),
            round(nz + float(u[3 * i + 1]), 6),
        ])

    line_max_moment_kNm: Dict[int, float] = {lid: 0.0 for lid in mapping.line_to_elements}
    line_max_shear_kN: Dict[int, float] = {lid: 0.0 for lid in mapping.line_to_elements}
    for lid, dofs, k_loc, T, f_eq in elem_records:
        f_int = k_loc @ (T @ u[dofs]) - f_eq
        v_max = max(abs(float(f_int[1])), abs(float(f_int[4]))) / 1e3
        m_max = max(abs(float(f_int[2])), abs(float(f_int[5]))) / 1e3
        if v_max > line_max_shear_kN[lid]:
            line_max_shear_kN[lid] = round(v_max, 4)
        if m_max > line_max_moment_kNm[lid]:
            line_max_moment_kNm[lid] = round(m_max, 4)

    return {
        "nodes": [list(c) for c in mapping.nodes],
        "elements": [list(e) for e in mapping.elements],
        "geometry_mapping": {
            "point_to_nodes": mapping.point_to_nodes,
            "line_to_elements": mapping.line_to_elements,
        },
        "deformed_positions": deformed_positions,
        "max_displacement_mm": round(float(np.max(np.abs(u[0::3]) + np.abs(u[1::3]))) * 1e3, 4),
        "line_max_moment_kNm": line_max_moment_kNm,
        "line_max_shear_kN": line_max_shear_kN,
        "connection_classes": connection_classes,
        "base_reactions_kN": {
            pt_id: [
                round(float(reactions[3 * mapping.point_to_nodes[pt_id]]) / 1e3, 4),
                round(float(reactions[3 * mapping.point_to_nodes[pt_id] + 1]) / 1e3, 4),
                round(float(reactions[3 * mapping.point_to_nodes[pt_id] + 2]) / 1e3, 4),
            ]
            for pt_id in inp.supports
            if pt_id in mapping.point_to_nodes
        },
    }

"""Elementos finitos de barra (Suite 5).

- non_prismatic: rigidez elástica de vigas de sección variable (Simpson).
- semi_rigid: conexiones semirrígidas con resortes rotacionales de extremo.
- geometry_mapping: mapeo semántico -> malla MEF (point_to_nodes, line_to_elements).
"""
from loadpath.fea.geometry_mapping import (
    GeometryMapping,
    SemanticFrameInput,
    build_frame_mesh,
    solve_semantic_frame,
)
from loadpath.fea.non_prismatic import beam_stiffness_2d
from loadpath.fea.semi_rigid import (
    classify_connection_ec3,
    fixity_factor_monforton_wu,
    semi_rigid_bending_stiffness,
)

__all__ = [
    "beam_stiffness_2d",
    "semi_rigid_bending_stiffness",
    "fixity_factor_monforton_wu",
    "classify_connection_ec3",
    "GeometryMapping",
    "SemanticFrameInput",
    "build_frame_mesh",
    "solve_semantic_frame",
]

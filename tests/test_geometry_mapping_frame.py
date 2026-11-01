from __future__ import annotations

import pytest

from loadpath.fea import (
    SemanticFrameInput,
    build_frame_mesh,
    solve_semantic_frame,
)


def test_build_frame_mesh_and_solve_semantic_frame():
    inp = SemanticFrameInput(
        points={
            1: (0.0, 0.0, 0.0),
            2: (8.0, 0.0, 0.0),
            3: (0.0, 0.0, 4.5),
            4: (8.0, 0.0, 4.5),
        },
        lines={
            1: (1, 3),
            2: (2, 4),
            3: (3, 4),
        },
        supports={1: (True, True, True), 2: (True, True, True)},
        point_loads_kN={3: (35.0, 0.0, 0.0)},
        distributed_loads_kN_m={3: -24.0},
        end_springs_kNm_rad={3: (15_000.0, 15_000.0)},
        divisions=5,
    )
    mapping = build_frame_mesh(inp)
    assert len(mapping.nodes) == 16
    assert len(mapping.elements) == 15
    assert len(mapping.line_to_elements[3]) == 5

    res = solve_semantic_frame(inp)
    assert res["max_displacement_mm"] > 1.0
    assert res["connection_classes"][3] == "semi_rigid"
    assert res["line_max_moment_kNm"][3] > 10.0
    assert res["line_max_shear_kN"][3] > 20.0

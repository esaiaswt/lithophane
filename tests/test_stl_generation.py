# Tests for stl_generation module
# Property-based tests for mesh correctness

import io
from collections import defaultdict

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from stl import mesh as stl_mesh_module

from stl_generation import create_stl_mesh, export_stl, generate_vertices


# --- Hypothesis strategies ---

def thickness_map_strategy():
    """Generate thickness maps with values in [0.4, 2.0] and shapes from (2,2) to (10,10)."""
    return st.tuples(
        st.integers(min_value=2, max_value=10),
        st.integers(min_value=2, max_value=10),
    ).flatmap(
        lambda shape: st.tuples(
            st.just(shape[0]),
            st.just(shape[1]),
            st.lists(
                st.floats(min_value=0.4, max_value=2.0, allow_nan=False, allow_infinity=False),
                min_size=shape[0] * shape[1],
                max_size=shape[0] * shape[1],
            ),
        )
    ).map(
        lambda t: np.array(t[2], dtype=np.float64).reshape(t[0], t[1])
    )


def dimensions_strategy():
    """Generate width/height in mm from 10 to 200."""
    return st.floats(min_value=10.0, max_value=200.0, allow_nan=False, allow_infinity=False)


# --- Property 8: Mesh Watertightness ---


@pytest.mark.parametrize("tag", ["Feature: lithophane-generator, Property 8: Mesh Watertightness"])
@settings(max_examples=100)
@given(
    thickness_map=thickness_map_strategy(),
    width_mm=dimensions_strategy(),
    height_mm=dimensions_strategy(),
)
def test_mesh_watertightness(tag, thickness_map, width_mm, height_mm):
    """Property 8: Mesh Watertightness

    For any valid thickness map (2D, values in [0.4, 2.0], at least 2x2),
    create_stl_mesh should produce a mesh where every edge is shared by exactly
    2 triangles (manifold condition).

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
    """
    stl_mesh = create_stl_mesh(thickness_map, width_mm, height_mm)

    # Count edge occurrences across all triangles
    edge_count = defaultdict(int)

    for triangle in stl_mesh.vectors:
        # Each triangle has 3 vertices, forming 3 edges
        for i in range(3):
            v1 = tuple(np.round(triangle[i], decimals=8))
            v2 = tuple(np.round(triangle[(i + 1) % 3], decimals=8))
            # Sort edge vertices to create a canonical edge representation
            edge = tuple(sorted([v1, v2]))
            edge_count[edge] += 1

    # Every edge must be shared by exactly 2 triangles for a watertight mesh
    for edge, count in edge_count.items():
        assert count == 2, (
            f"Edge {edge} is shared by {count} triangles (expected 2). "
            f"Mesh is not watertight."
        )


# --- Property 9: Vertex Height Correctness ---


@pytest.mark.parametrize("tag", ["Feature: lithophane-generator, Property 9: Vertex Height Correctness"])
@settings(max_examples=100)
@given(
    thickness_map=thickness_map_strategy(),
    width_mm=dimensions_strategy(),
    height_mm=dimensions_strategy(),
)
def test_vertex_height_correctness(tag, thickness_map, width_mm, height_mm):
    """Property 9: Vertex Height Correctness

    Top surface vertices should have Z = thickness_map values.
    Bottom surface vertices should have Z = 0.
    X/Y should be linearly spaced across the physical dimensions.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
    """
    vertices = generate_vertices(thickness_map, width_mm, height_mm)

    rows, cols = thickness_map.shape
    n_vertices = rows * cols

    # Top surface vertices (first rows*cols entries)
    top_vertices = vertices[:n_vertices]
    # Bottom surface vertices (next rows*cols entries)
    bottom_vertices = vertices[n_vertices:]

    # Check Z values for top surface match thickness map (row-major order)
    expected_z_top = thickness_map.ravel()
    np.testing.assert_allclose(
        top_vertices[:, 2], expected_z_top, rtol=1e-7,
        err_msg="Top surface Z values do not match thickness map"
    )

    # Check Z values for bottom surface are all 0
    np.testing.assert_allclose(
        bottom_vertices[:, 2], np.zeros(n_vertices), atol=1e-10,
        err_msg="Bottom surface Z values should all be 0"
    )

    # Check X coordinates are linearly spaced across width_mm
    expected_x = np.linspace(0, width_mm, cols)
    for i in range(rows):
        row_start = i * cols
        row_end = row_start + cols
        np.testing.assert_allclose(
            top_vertices[row_start:row_end, 0], expected_x, rtol=1e-7,
            err_msg=f"Top surface X coords at row {i} not linearly spaced"
        )
        np.testing.assert_allclose(
            bottom_vertices[row_start:row_end, 0], expected_x, rtol=1e-7,
            err_msg=f"Bottom surface X coords at row {i} not linearly spaced"
        )

    # Check Y coordinates are linearly spaced across height_mm
    expected_y = np.linspace(0, height_mm, rows)
    for i in range(rows):
        row_start = i * cols
        row_end = row_start + cols
        expected_y_val = expected_y[i]
        np.testing.assert_allclose(
            top_vertices[row_start:row_end, 1],
            np.full(cols, expected_y_val),
            rtol=1e-7,
            err_msg=f"Top surface Y coords at row {i} should be {expected_y_val}"
        )
        np.testing.assert_allclose(
            bottom_vertices[row_start:row_end, 1],
            np.full(cols, expected_y_val),
            rtol=1e-7,
            err_msg=f"Bottom surface Y coords at row {i} should be {expected_y_val}"
        )


# --- Property 10: STL Export Round-Trip ---


@pytest.mark.parametrize("tag", ["Feature: lithophane-generator, Property 10: STL Export Round-Trip"])
@settings(max_examples=100)
@given(
    thickness_map=thickness_map_strategy(),
    width_mm=dimensions_strategy(),
    height_mm=dimensions_strategy(),
)
def test_stl_export_round_trip(tag, thickness_map, width_mm, height_mm):
    """Property 10: STL Export Round-Trip

    Export mesh to binary STL, re-import, verify vertex positions match
    within floating-point tolerance.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
    """
    # Create and export mesh
    stl_mesh = create_stl_mesh(thickness_map, width_mm, height_mm)
    stl_bytes = export_stl(stl_mesh, binary=True)

    # Re-import from bytes
    buffer = io.BytesIO(stl_bytes)
    reimported_mesh = stl_mesh_module.Mesh.from_file('', fh=buffer)

    # Compare vertex positions
    np.testing.assert_allclose(
        reimported_mesh.vectors, stl_mesh.vectors, atol=1e-5,
        err_msg="Round-trip STL export/import produced different vertex positions"
    )

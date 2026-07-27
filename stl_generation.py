# Lithophane Generator - STL Mesh Generation Module
# Mesh vertex/face generation, STL file creation (functional style, no classes)

import io
import numpy as np
import stl
from stl import mesh as stl_mesh_module


def generate_vertices(thickness_map: np.ndarray, width_mm: float, height_mm: float) -> np.ndarray:
    """Generate 3D vertex positions from thickness map.

    Top surface z = thickness_map values.
    Bottom surface z = 0.
    X/Y positions mapped to physical dimensions.

    Args:
        thickness_map: 2D numpy array of shape (rows, cols), dtype float64
        width_mm: physical width in mm
        height_mm: physical height in mm

    Returns:
        (2 * rows * cols, 3) float64 array of vertex coordinates.
        First rows*cols vertices are top surface (row-major order),
        next rows*cols are bottom surface.
    """
    rows, cols = thickness_map.shape

    # Create linearly spaced coordinates
    x_coords = np.linspace(0, width_mm, cols)
    y_coords = np.linspace(0, height_mm, rows)

    # Create meshgrid (x varies with cols, y varies with rows)
    xx, yy = np.meshgrid(x_coords, y_coords)

    # Flatten in row-major order
    x_flat = xx.ravel()
    y_flat = yy.ravel()
    z_top = thickness_map.ravel()
    z_bottom = np.zeros(rows * cols, dtype=np.float64)

    # Top surface vertices: (x, y, thickness)
    top_vertices = np.column_stack([x_flat, y_flat, z_top])

    # Bottom surface vertices: (x, y, 0)
    bottom_vertices = np.column_stack([x_flat, y_flat, z_bottom])

    # Concatenate: top first, then bottom
    vertices = np.vstack([top_vertices, bottom_vertices])

    return vertices.astype(np.float64)

def generate_top_faces(rows: int, cols: int) -> np.ndarray:
    """Generate triangle face indices for the top surface grid.

    Each grid cell (i, j) is split into 2 triangles with counter-clockwise
    winding order when viewed from outside (positive Z direction).

    Args:
        rows: number of vertex rows in the grid
        cols: number of vertex columns in the grid

    Returns:
        (M, 3) int32 array of vertex indices, where M = 2*(rows-1)*(cols-1)
    """
    faces = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            # Top-left vertex of this grid cell
            tl = i * cols + j
            tr = i * cols + j + 1
            bl = (i + 1) * cols + j
            br = (i + 1) * cols + j + 1

            # Triangle 1: top-left, top-right, bottom-left (CCW from +Z)
            faces.append([tl, tr, bl])
            # Triangle 2: top-right, bottom-right, bottom-left (CCW from +Z)
            faces.append([tr, br, bl])

    return np.array(faces, dtype=np.int32)


def generate_bottom_faces(rows: int, cols: int, vertex_offset: int) -> np.ndarray:
    """Generate triangle face indices for the bottom (flat) surface.

    Same grid layout as top but with reversed winding order (faces outward
    in -Z direction) and vertex indices offset by vertex_offset.

    Args:
        rows: number of vertex rows in the grid
        cols: number of vertex columns in the grid
        vertex_offset: offset added to all indices (rows * cols for bottom surface)

    Returns:
        (M, 3) int32 array of vertex indices, where M = 2*(rows-1)*(cols-1)
    """
    v = vertex_offset
    faces = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            tl = v + i * cols + j
            tr = v + i * cols + j + 1
            bl = v + (i + 1) * cols + j
            br = v + (i + 1) * cols + j + 1

            # Triangle 1: top-left, bottom-left, top-right (CW from +Z = CCW from -Z)
            faces.append([tl, bl, tr])
            # Triangle 2: top-right, bottom-left, bottom-right (CW from +Z = CCW from -Z)
            faces.append([tr, bl, br])

    return np.array(faces, dtype=np.int32)


def generate_side_faces(rows: int, cols: int, vertex_offset: int) -> np.ndarray:
    """Generate triangle face indices for the four perimeter walls.

    Connects top surface perimeter edges to corresponding bottom surface edges
    to create a watertight mesh. Each perimeter edge segment produces 2 triangles.

    The four sides are:
    - Top edge (row=0): faces outward in -Y direction
    - Bottom edge (row=rows-1): faces outward in +Y direction
    - Left edge (col=0): faces outward in -X direction
    - Right edge (col=cols-1): faces outward in +X direction

    Args:
        rows: number of vertex rows in the grid
        cols: number of vertex columns in the grid
        vertex_offset: offset to bottom surface vertices (rows * cols)

    Returns:
        (K, 3) int32 array of vertex indices,
        where K = 2 * (2*(rows-1) + 2*(cols-1))
    """
    v = vertex_offset
    faces = []

    # Top edge (row=0): connects columns 0..cols-1, normal faces -Y
    for j in range(cols - 1):
        top_left = j
        top_right = j + 1
        bot_left = v + j
        bot_right = v + j + 1
        # Winding for outward normal in -Y direction
        faces.append([top_left, bot_left, top_right])
        faces.append([top_right, bot_left, bot_right])

    # Bottom edge (row=rows-1): connects columns 0..cols-1, normal faces +Y
    for j in range(cols - 1):
        top_left = (rows - 1) * cols + j
        top_right = (rows - 1) * cols + j + 1
        bot_left = v + (rows - 1) * cols + j
        bot_right = v + (rows - 1) * cols + j + 1
        # Winding for outward normal in +Y direction
        faces.append([top_left, top_right, bot_left])
        faces.append([top_right, bot_right, bot_left])

    # Left edge (col=0): connects rows 0..rows-1, normal faces -X
    for i in range(rows - 1):
        top_upper = i * cols
        top_lower = (i + 1) * cols
        bot_upper = v + i * cols
        bot_lower = v + (i + 1) * cols
        # Winding for outward normal in -X direction
        faces.append([top_upper, top_lower, bot_upper])
        faces.append([top_lower, bot_lower, bot_upper])

    # Right edge (col=cols-1): connects rows 0..rows-1, normal faces +X
    for i in range(rows - 1):
        top_upper = i * cols + (cols - 1)
        top_lower = (i + 1) * cols + (cols - 1)
        bot_upper = v + i * cols + (cols - 1)
        bot_lower = v + (i + 1) * cols + (cols - 1)
        # Winding for outward normal in +X direction
        faces.append([top_upper, bot_upper, top_lower])
        faces.append([top_lower, bot_upper, bot_lower])

    return np.array(faces, dtype=np.int32)


def create_stl_mesh(thickness_map: np.ndarray, width_mm: float, height_mm: float) -> stl_mesh_module.Mesh:
    """Assemble complete watertight mesh from thickness map.

    Combines top, bottom, and side faces into a single numpy-stl Mesh object.

    Args:
        thickness_map: 2D numpy array of shape (rows, cols), dtype float64,
                       values in [0.4, 2.0] mm
        width_mm: physical width in mm
        height_mm: physical height in mm

    Returns:
        numpy-stl Mesh object with all faces assembled.
    """
    rows, cols = thickness_map.shape

    # Generate vertices
    vertices = generate_vertices(thickness_map, width_mm, height_mm)

    # Calculate vertex offset (top surface vertex count)
    vertex_offset = rows * cols

    # Generate all face groups
    top_faces = generate_top_faces(rows, cols)
    bottom_faces = generate_bottom_faces(rows, cols, vertex_offset)
    side_faces = generate_side_faces(rows, cols, vertex_offset)

    # Concatenate all faces
    all_faces = np.concatenate([top_faces, bottom_faces, side_faces], axis=0)
    total_faces = all_faces.shape[0]

    # Create numpy-stl Mesh object
    stl_mesh = stl_mesh_module.Mesh(np.zeros(total_faces, dtype=stl_mesh_module.Mesh.dtype))

    # Assign vertex positions for each face
    for i in range(total_faces):
        for j in range(3):
            stl_mesh.vectors[i][j] = vertices[all_faces[i][j]]

    return stl_mesh


def export_stl(stl_mesh: stl_mesh_module.Mesh, binary: bool = True) -> bytes:
    """Serialize mesh to STL format bytes.

    Args:
        stl_mesh: numpy-stl Mesh object to export
        binary: True for binary STL format, False for ASCII STL format

    Returns:
        bytes containing the serialized STL data.
    """
    buffer = io.BytesIO()

    if binary:
        stl_mesh.save('output', fh=buffer, mode=stl.Mode.BINARY)
    else:
        stl_mesh.save('output', fh=buffer, mode=stl.Mode.ASCII)

    return buffer.getvalue()

"""Generate an 85 mm pneumatic cube with a spherical bladder cavity."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import math
from pathlib import Path
import struct

import manifold3d as m3d
import numpy as np
from skimage.measure import marching_cubes

from model_archive import preserve_models

MODEL_VERSION = "pneumatic-v02-85mm-r15-spherical-cavity"
OUTER_SIZE = 85.0
OUTER_RADIUS = 15.0
WALL_THICKNESS = 3.0
CAVITY_RADIUS = OUTER_SIZE / 2 - WALL_THICKNESS
OUTER_BLEND = 0.5
INNER_BLEND = 1.25
INNER_CHANNEL_SCALE = 0.65
GRID_STEP = 0.22
MESH_TOLERANCE = 0.018
PRINT_ORIENTATION = "edge"
OUTPUT = Path("output/pneumatic_cube")


@dataclass(frozen=True)
class Opening:
    u: float
    v: float
    diameter: float
    straight: float = 0.0


A = (Opening(-17.5, 17.5, 31.5), Opening(17.5, 17.5, 31.5), Opening(0, -17.5, 31.5))
B1 = (Opening(-19, 0, 34.5), Opening(19, 0, 34.5))
B2 = (Opening(0, -20, 28, 36), Opening(0, 20, 28, 36))
C = (Opening(0, 0, 10),)

# The drawing shows B2 and B1 on adjacent sides and A above. Put C underneath.
# Signed axis indices give local horizontal, up and outward coordinates.
FACES = (
    ("front", "B2", (-1, 3, 2), B2),
    ("right", "B1", (2, 3, 1), B1),
    ("back", "A", (1, 3, -2), A),
    ("left", "A", (-2, 3, -1), A),
    ("top", "A", (1, 2, 3), A),
    ("bottom", "C", (1, -2, -3), C),
)
OPENING_COUNT = sum(len(openings) for _, _, _, openings in FACES)


def box(size, center=(0, 0, 0)):
    return m3d.Manifold.cube(size, center=True).translate(center)


def cavity_body():
    return m3d.Manifold.sphere(CAVITY_RADIUS, 96)


def cavity_distance(x, y, z):
    return np.sqrt(x * x + y * y + z * z) - CAVITY_RADIUS


def outer_distance(x, y, z):
    flat_half = OUTER_SIZE / 2 - OUTER_RADIUS
    dx, dy, dz = (np.abs(a) - flat_half for a in (x, y, z))
    return (
        np.sqrt(np.maximum(dx, 0)**2 + np.maximum(dy, 0)**2 + np.maximum(dz, 0)**2)
        + np.minimum(np.maximum(np.maximum(dx, dy), dz), 0)
        - OUTER_RADIUS
    )


def rounded_intersection(a, b, radius):
    """Intersect two signed fields, rounding the material edge at the join."""
    shifted_a = a + radius
    shifted_b = b + radius
    return (
        np.hypot(np.maximum(shifted_a, 0), np.maximum(shifted_b, 0))
        + np.minimum(np.maximum(shifted_a, shifted_b), 0)
        - radius
    )


def local_coords(coords, axes):
    return tuple(coords[axis - 1] if axis > 0 else -coords[-axis - 1] for axis in axes)


def opening_distance(u, v, depth, opening):
    # Keep the full profile at the mouth. The smooth taper toward the center
    # lets the far side of each opening meet the sphere without a blind ledge.
    progress = np.clip((depth - 18.0) / (38.5 - 18.0), 0, 1)
    scale = INNER_CHANNEL_SCALE + (1 - INNER_CHANNEL_SCALE) * progress**2 * (3 - 2 * progress)
    du = np.maximum(np.abs(u - scale * opening.u) - scale * opening.straight / 2, 0)
    dv = v - scale * opening.v
    profile = np.hypot(du, dv) - scale * opening.diameter / 2
    return np.maximum(profile, 14.0 - depth)


def material_distance(x, y, z):
    """Negative inside material, positive in the cavity, channels and exterior."""
    outer = outer_distance(x, y, z)
    sphere = cavity_distance(x, y, z)
    channels = np.full_like(sphere, np.inf)
    for _, _, axes, openings in FACES:
        u, v, depth = local_coords((x, y, z), axes)
        for opening in openings:
            np.minimum(channels, opening_distance(u, v, depth, opening), out=channels)
    void = -rounded_intersection(-sphere, -channels, INNER_BLEND)
    return rounded_intersection(outer, -void, OUTER_BLEND)


def build_model():
    grid = np.arange(-44.07, 44.2, GRID_STEP).astype(np.float32)
    field = np.empty((len(grid),) * 3, dtype=np.float32)
    y, z = grid[None, :, None], grid[None, None, :]
    for start in range(0, len(grid), 8):
        block = slice(start, start + 8)
        field[block] = material_distance(grid[block, None, None], y, z)

    vertices, triangles, _, _ = marching_cubes(
        field, level=0, spacing=(GRID_STEP,) * 3, gradient_direction="descent", allow_degenerate=False
    )
    vertices += float(grid[0])
    mesh = m3d.Mesh64(
        vert_properties=np.ascontiguousarray(vertices, dtype=np.float64),
        tri_verts=np.ascontiguousarray(triangles, dtype=np.uint64),
    )
    solid = m3d.Manifold(mesh)
    if solid.status() != m3d.Error.NoError or solid.is_empty():
        raise ValueError(f"Pneumatic cube surface extraction failed: {solid.status()}")
    return solid.simplify(MESH_TOLERANCE)


def mesh_arrays(solid):
    mesh = solid.to_mesh64()
    return np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts)


def print_rotation(orientation):
    if orientation == "face":
        return np.eye(3)
    if orientation == "edge":
        return np.array([[1, 0, 0], [0, 1, -1], [0, 1, 1]]) / np.sqrt([[1], [2], [2]])
    if orientation == "corner":
        return np.array([[1, -1, 0], [1, 1, -2], [1, 1, 1]]) / np.sqrt([[2], [6], [3]])
    raise ValueError(orientation)


def print_transform(solid, orientation=PRINT_ORIENTATION):
    rotation = print_rotation(orientation)
    matrix = np.column_stack((rotation, np.zeros(3)))
    oriented = solid.transform(matrix.tolist())
    vertices, _ = mesh_arrays(oriented)
    shift = -float(vertices[:, 2].min())
    matrix[2, 3] = shift
    return oriented.translate((0, 0, shift)), matrix


def write_stl(solid, path):
    vertices, faces = mesh_arrays(solid)
    triangles = vertices[faces].astype("<f4")
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    lengths = np.linalg.norm(cross, axis=1)
    if (lengths == 0).any():
        raise ValueError("Degenerate triangles after float32 STL conversion")
    records = np.zeros(len(triangles), dtype=[("normal", "<f4", 3), ("points", "<f4", (3, 3)), ("attribute", "<u2")])
    records["normal"] = cross / lengths[:, None]
    records["points"] = triangles
    with path.open("wb") as stream:
        stream.write(MODEL_VERSION.encode()[:80].ljust(80, b"\0"))
        stream.write(struct.pack("<I", len(faces)))
        stream.write(records.tobytes())


def model_point(axes, local_point):
    point = np.zeros(3)
    for axis, value in zip(axes, local_point):
        point[abs(axis) - 1] = value if axis > 0 else -value
    return point


def validate(solid):
    assert solid.volume() > 0
    assert len(solid.decompose()) == 1
    vertices, faces = mesh_arrays(solid)
    edges = Counter(tuple(sorted((int(face[i]), int(face[(i + 1) % 3])))) for face in faces for i in range(3))
    assert all(count == 2 for count in edges.values())
    euler = len(vertices) - len(edges) + len(faces)
    assert euler == 2 - 2 * (OPENING_COUNT - 1), ("Separate openings", euler)
    assert np.allclose(np.ptp(vertices, axis=0), OUTER_SIZE, atol=0.001)
    cavity_overlap = (solid ^ m3d.Manifold.sphere(CAVITY_RADIUS - 0.06, 96)).volume()
    assert cavity_overlap < 1e-5, cavity_overlap

    for name, _, axes, openings in FACES:
        for opening in openings:
            start = model_point(axes, (opening.u, opening.v, 35.0))
            end = model_point(axes, (opening.u, opening.v, 44.0))
            assert (solid ^ box((0.3, 0.3, 0.3), start)).volume() < 1e-7, (name, opening)
            assert (solid ^ box((0.3, 0.3, 0.3), end)).volume() < 1e-7, (name, opening)

    # Midpoints of the closest pairs are solid at nominal mouth depth.
    for axes, local_point in ((FACES[4][2], (0, 17.5, 41)),
                              (FACES[1][2], (0, 0, 41)),
                              (FACES[0][2], (0, 0, 41))):
        probe = box((2.49, 2.49, 0.25), model_point(axes, local_point))
        assert math.isclose((solid ^ probe).volume(), probe.volume(), abs_tol=1e-5)

    oriented, matrix = print_transform(solid)
    pv, _ = mesh_arrays(oriented)
    return {
        "model_version": MODEL_VERSION,
        "body_bounds_mm": np.ptp(vertices, axis=0).round(4).tolist(),
        "outer_radius_mm": OUTER_RADIUS,
        "spherical_cavity_diameter_mm": 2 * CAVITY_RADIUS,
        "face_center_wall_mm": WALL_THICKNESS,
        "hole_count": OPENING_COUNT,
        "faces": {name: {"type": kind, "openings": [
            {"center_uv_mm": [o.u, o.v], "width_mm": o.diameter + o.straight, "height_mm": o.diameter}
            for o in openings]} for name, kind, _, openings in FACES},
        "minimum_nominal_web_between_circular_mouths_mm": 2.5,
        "outer_blend_field_radius_mm": OUTER_BLEND,
        "cavity_blend_field_radius_mm": INNER_BLEND,
        "connected_solids": 1,
        "euler_characteristic": euler,
        "boundary_edges": 0,
        "non_manifold_edges": 0,
        "volume_mm3": solid.volume(),
        "print_orientation": PRINT_ORIENTATION,
        "print_transform_3x4": matrix.tolist(),
        "print_bounds_mm": np.ptp(pv, axis=0).round(4).tolist(),
        "limits": "Physical print, aperture finish and membrane behavior require a test.",
    }


@preserve_models("pneumatic_cube")
def main():
    solid = build_model()
    report = validate(solid)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    oriented, _ = print_transform(solid)
    for name, model in (("pneumatic_cube", solid), ("pneumatic_cube_print", oriented)):
        write_stl(model, OUTPUT / f"{name}.stl")
        print(f"{name}: boundary_edges=0, one connected solid; {len(mesh_arrays(model)[1])} triangles", flush=True)
    (OUTPUT / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

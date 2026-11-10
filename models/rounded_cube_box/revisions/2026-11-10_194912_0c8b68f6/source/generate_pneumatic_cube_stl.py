"""One-piece pneumatic cube with eighteen doubly rounded membrane apertures."""
from __future__ import annotations

from collections import Counter
import itertools
import json
import math
from pathlib import Path
import struct

import manifold3d as m3d
import numpy as np

from model_archive import preserve_models

MODEL_VERSION = "pneumatic-v01-80mm-r8-27mm-rounded-apertures"
OUTER_SIZE = 80.0
OUTER_RADIUS = 8.0
WALL_THICKNESS = 4.0
HOLE_DIAMETER = 27.0
HOLE_EDGE_RADIUS = 1.6
HOLE_OFFSET = 16.7
HOLE_CENTERS = ((-HOLE_OFFSET, HOLE_OFFSET), (HOLE_OFFSET, HOLE_OFFSET), (0.0, -HOLE_OFFSET))
CURVE_SEGMENTS = 96
HOLE_SEGMENTS = 128
FILLET_STEPS = 20
OUTPUT = Path("output/pneumatic_cube")

# Right-handed local face frames: local Z points outward, local Y is picture up.
FACE_FRAMES = (
    ("front", (-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    ("right", (0, 1, 0), (0, 0, 1), (1, 0, 0)),
    ("back", (1, 0, 0), (0, 0, 1), (0, -1, 0)),
    ("left", (0, -1, 0), (0, 0, 1), (-1, 0, 0)),
    ("top", (1, 0, 0), (0, 1, 0), (0, 0, 1)),
    ("bottom", (1, 0, 0), (0, -1, 0), (0, 0, -1)),
)


def box(size, center=(0, 0, 0)):
    return m3d.Manifold.cube(size, center=True).translate(center)


def rounded_body(radius):
    return box((OUTER_SIZE - 2 * OUTER_RADIUS,) * 3).minkowski_sum(
        m3d.Manifold.sphere(radius, CURVE_SEGMENTS))


def aperture_profile():
    """Radial/axial cutter section: circular R1.6 blends on BOTH wall faces.

    The two quarter circles are tangent to the plane and cylindrical bore.
    They are not conical chamfers. Their mouths stay entirely on flat face
    regions, avoiding sharp intersections with the exterior R8 edge rounding.
    """
    r, blend = HOLE_DIAMETER / 2, HOLE_EDGE_RADIUS
    outside = OUTER_SIZE / 2
    inside = outside - WALL_THICKNESS
    result = [(0, inside - 1), (r + blend, inside - 1), (r + blend, inside)]
    for theta in np.linspace(math.pi / 2, 0, FILLET_STEPS + 1)[1:]:
        result.append((r + blend - blend * math.cos(theta), inside + blend - blend * math.sin(theta)))
    result.append((r, outside - blend))
    for theta in np.linspace(0, math.pi / 2, FILLET_STEPS + 1)[1:]:
        result.append((r + blend - blend * math.cos(theta), outside - blend + blend * math.sin(theta)))
    result.extend([(r + blend, outside + 1), (0, outside + 1)])
    return result


def face_transform(frame, center):
    _, u, v, n = frame
    u, v, n = np.asarray(u), np.asarray(v), np.asarray(n)
    return np.column_stack((u, v, n, center[0] * u + center[1] * v)).tolist()


def build_model():
    assert WALL_THICKNESS >= 2 * HOLE_EDGE_RADIUS
    assert OUTER_RADIUS > WALL_THICKNESS
    mouth = HOLE_DIAMETER / 2 + HOLE_EDGE_RADIUS
    flat_half = OUTER_SIZE / 2 - OUTER_RADIUS
    assert max(max(abs(a), abs(b)) + mouth for a, b in HOLE_CENTERS) < flat_half
    outer = rounded_body(OUTER_RADIUS)
    inner = rounded_body(OUTER_RADIUS - WALL_THICKNESS)
    shell = outer - inner
    tool = m3d.CrossSection([aperture_profile()]).revolve(HOLE_SEGMENTS)
    cutters = [tool.transform(face_transform(frame, center)) for frame in FACE_FRAMES for center in HOLE_CENTERS]
    return m3d.Manifold.batch_boolean([shell, *cutters], m3d.OpType.Subtract)


def mesh_arrays(solid):
    mesh = solid.to_mesh64()
    return np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts)


def print_transform(solid, orientation="corner"):
    """Orient a fresh copy; the assembled/model geometry remains unchanged."""
    if orientation == "face":
        rotation = np.eye(3)
    elif orientation == "edge":
        rotation = np.array([[1, 0, 0], [0, 1 / math.sqrt(2), -1 / math.sqrt(2)],
                             [0, 1 / math.sqrt(2), 1 / math.sqrt(2)]])
    elif orientation == "corner":
        rotation = np.array([[1, -1, 0], [1, 1, -2], [1, 1, 1]]) / np.sqrt([[2], [6], [3]])
    else:
        raise ValueError(orientation)
    matrix = np.column_stack((rotation, np.zeros(3)))
    oriented = solid.transform(matrix.tolist())
    vertices, _ = mesh_arrays(oriented)
    shift = -float(vertices[:, 2].min())
    matrix[2, 3] = shift
    return oriented.translate((0, 0, shift)), matrix


def write_stl(solid, path):
    vertices, faces = mesh_arrays(solid)
    # Record the actual serialized (float32 STL) geometry in independent checks.
    with path.open("wb") as stream:
        stream.write(MODEL_VERSION.encode()[:80].ljust(80, b"\0"))
        stream.write(struct.pack("<I", len(faces)))
        for face in faces:
            a, b, c = vertices[face]
            normal = np.cross(b - a, c - a)
            length = np.linalg.norm(normal)
            normal = normal / length if length else normal
            stream.write(struct.pack("<12fH", *normal, *a, *b, *c, 0))


def validate(solid):
    assert solid.status() == m3d.Error.NoError
    assert len(solid.decompose()) == 1
    vertices, faces = mesh_arrays(solid)
    edge_uses = Counter(tuple(sorted((int(face[i]), int(face[(i + 1) % 3])))) for face in faces for i in range(3))
    assert all(count == 2 for count in edge_uses.values())
    euler = len(vertices) - len(edge_uses) + len(faces)
    assert euler == 2 - 2 * (18 - 1), ("Eighteen distinct shell openings", euler)
    assert np.allclose(np.ptp(vertices, axis=0), OUTER_SIZE, atol=1e-6)
    assert (solid ^ box((60, 60, 60))).volume() < 1e-6
    mouth = HOLE_DIAMETER + 2 * HOLE_EDGE_RADIUS
    gaps = [math.dist(a, b) - mouth for a, b in itertools.combinations(HOLE_CENTERS, 2)]
    assert min(gaps) >= 3.19
    for frame, center in itertools.product(FACE_FRAMES, HOLE_CENTERS):
        probe = m3d.Manifold.cylinder(6, HOLE_DIAMETER / 2 - .02, circular_segments=HOLE_SEGMENTS)
        probe = probe.translate((0, 0, OUTER_SIZE / 2 - WALL_THICKNESS - 1)).transform(face_transform(frame, center))
        assert (solid ^ probe).volume() < 1e-5, (frame[0], center, "blocked opening")
    oriented, matrix = print_transform(solid)
    pv, _ = mesh_arrays(oriented)
    return {"model_version": MODEL_VERSION, "body_bounds_mm": np.ptp(vertices, axis=0).round(6).tolist(),
            "outer_radius_mm": OUTER_RADIUS, "wall_mm": WALL_THICKNESS,
            "hole_count": 18, "holes_per_face": 3, "hole_throat_diameter_mm": HOLE_DIAMETER,
            "hole_mouth_diameter_mm": mouth, "inner_and_outer_hole_blend_radius_mm": HOLE_EDGE_RADIUS,
            "minimum_face_web_between_blends_mm": round(min(gaps), 6),
            "hole_centers_face_uv_mm": HOLE_CENTERS, "connected_solids": 1, "euler_characteristic": euler,
            "boundary_edges": 0, "non_manifold_edges": 0,
            "volume_mm3": solid.volume(), "print_orientation": "corner",
            "print_transform_3x4": matrix.tolist(), "print_bounds_mm": np.ptp(pv, axis=0).round(6).tolist(),
            "interior": "Empty: no mounts, thermal pads, fasteners or seam.",
            "reference_adjustment": "User approved aperture/layout changes while retaining 80 mm and R8. Reference diameter/pitch 35 mm would leave zero web.",
            "limits": "Nominal geometry only. Printed rims require deburring/smoothing and tactile inspection before inserting a balloon. No pressure or membrane-durability test performed."}


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

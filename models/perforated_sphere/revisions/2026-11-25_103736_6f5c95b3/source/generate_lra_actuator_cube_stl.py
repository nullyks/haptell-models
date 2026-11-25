"""Generate the six-actuator cube from the 2026-11-25 customer drawing."""

from __future__ import annotations

import json
from pathlib import Path

import manifold3d as m3d
import numpy as np

import generate_rounded_cube_box_stl as rounded
from model_archive import preserve_models

MODEL_VERSION = "lra-cube-v01-fit-trial"
OUTPUT = Path("output/lra_actuator_cube")
SIZE = 85.0
RADIUS = 15.0
WALL = 3.2
HALF = SIZE / 2
INNER_HALF = HALF - WALL
FLAT_HALF = HALF - RADIUS
NOTCH_RADIUS = 6.0
ACTUATOR_RADIUS = 5.0
ACTUATOR_DEPTH = 4.0
POCKET_RADIUS = 5.2
POCKET_DEPTH = 4.05
CLIP_WALL = 1.8
CLIP_TIP_RADIUS = 4.85
SEAT_HEIGHT = 1.0
SIDE_HEIGHT = 19.5


def cube(radius: float) -> m3d.Manifold:
    return rounded.box((2 * FLAT_HALF,) * 3).minkowski_sum(
        m3d.Manifold.sphere(radius, rounded.CURVE_SEGMENTS)
    )


def cable_notch() -> m3d.Manifold:
    # Cut the lower half and its guide rail. The upper half closes the U.
    throat = m3d.Manifold.cylinder(12, NOTCH_RADIUS, circular_segments=64, center=True)
    throat = throat.rotate((90, 0, 0)).translate((0, -INNER_HALF, 0))
    rail_cut = rounded.box((2 * NOTCH_RADIUS, 12, 8), (0, -INNER_HALF, 4))
    return throat + rail_cut


def lra_holder() -> m3d.Manifold:
    outside = POCKET_RADIUS + CLIP_WALL
    seat = m3d.Manifold.cylinder(SEAT_HEIGHT + 0.6, outside, circular_segments=64)
    seat = seat.translate((0, 0, -SEAT_HEIGHT - 0.6))
    # Three tapered retaining clips. The gap around local +X clears the leads.
    clip_profile = m3d.CrossSection([[
        (POCKET_RADIUS, -0.75), (outside, -0.75), (outside, POCKET_DEPTH + 0.3),
        (outside - 0.5, POCKET_DEPTH + 1.2), (POCKET_RADIUS, POCKET_DEPTH + 1.2),
        (CLIP_TIP_RADIUS, POCKET_DEPTH + 0.3), (POCKET_RADIUS, POCKET_DEPTH),
    ]])
    clip = clip_profile.revolve(circular_segments=64, revolve_degrees=46)
    return rounded.union([seat, *(clip.rotate((0, 0, angle - 23)) for angle in (60, 180, 300))])


def frame(normal, wire_direction, height=0.0):
    normal = np.asarray(normal)
    wire_direction = np.asarray(wire_direction)
    inward = -normal
    center = normal * (INNER_HALF - SEAT_HEIGHT) + np.array((0, 0, height))
    return np.column_stack((wire_direction, np.cross(inward, wire_direction), inward, center))


def mount_frames():
    # Side holders alternate between lid and base around the seam.
    return {
        "lid_center": frame((0, 0, 1), (0, -1, 0)),
        "lid_right": frame((1, 0, 0), (0, 0, -1), SIDE_HEIGHT),
        "lid_left": frame((-1, 0, 0), (0, 0, -1), SIDE_HEIGHT),
        "bottom_center": frame((0, 0, -1), (0, -1, 0)),
        "bottom_front": frame((0, -1, 0), (0, 0, 1), -SIDE_HEIGHT),
        "bottom_back": frame((0, 1, 0), (0, 0, 1), -SIDE_HEIGHT),
    }


def build_parts() -> tuple[m3d.Manifold, m3d.Manifold]:
    shell = cube(RADIUS) - cube(RADIUS - WALL)
    holder = lra_holder()
    mounts = mount_frames()
    lid = rounded.union([shell ^ rounded.half_space(top=True),
                         *(holder.transform(matrix) for name, matrix in mounts.items()
                           if name.startswith("lid_"))])
    lid = rounded.subtract(lid, rounded.snap_sockets(INNER_HALF))
    bottom = rounded.union([shell ^ rounded.half_space(top=False),
                            rounded.registration(INNER_HALF, rail_width=53),
                            *(holder.transform(matrix) for name, matrix in mounts.items()
                              if name.startswith("bottom_"))])
    return lid, bottom - cable_notch()


def validate(lid: m3d.Manifold, bottom: m3d.Manifold) -> dict:
    for name, solid in (("lid", lid), ("bottom", bottom)):
        if solid.status() != m3d.Error.NoError or len(solid.decompose()) != 1:
            raise ValueError(f"{name} must be one connected solid")
    overlap = (lid ^ bottom).volume()
    if abs(overlap) > 1e-5:
        raise ValueError(f"Closed shell halves overlap by {overlap:.5f} mm³")
    assembly = lid + bottom
    bounds = rounded.mesh_bounds(rounded.to_mesh(assembly))[2]
    if not np.allclose(bounds, [SIZE] * 3, atol=1e-5):
        raise ValueError(f"Unexpected assembly dimensions: {bounds}")
    actuator = m3d.Manifold.cylinder(ACTUATOR_DEPTH, ACTUATOR_RADIUS, circular_segments=64)
    collisions = {}
    for name, matrix in mount_frames().items():
        collision = (assembly ^ actuator.transform(matrix)).volume()
        lead_exit = rounded.box((3, 1.5, 1.2), (5.5, 0, 1.5)).transform(matrix)
        if abs(collision) > 1e-5 or abs((assembly ^ lead_exit).volume()) > 1e-5:
            raise ValueError(f"Nominal actuator or lead collides at {name}")
        collisions[name] = round(abs(collision), 8)
    for x, z in ((-5.8, -0.3), (5.8, -0.3), (0, -5.8)):
        probe = rounded.box((0.2, 11, 0.2), (x, -INNER_HALF, z))
        if abs((assembly ^ probe).volume()) > 1e-5:
            raise ValueError("The shell or registration rail obstructs the cable exit")
    return {
        "model_version": MODEL_VERSION,
        "assembly_bounds_mm": bounds.tolist(),
        "outer_radius_mm": RADIUS,
        "nominal_wall_mm": WALL,
        "cable_notch_mm": [2 * NOTCH_RADIUS, NOTCH_RADIUS],
        "seated_overlap_mm3": round(abs(overlap), 8),
        "nominal_actuator_overlap_mm3": collisions,
        "shell_snap_count": 4 * len(rounded.SNAP_POSITIONS),
        "shell_snap_interference_mm": round(rounded.SNAP_PROTRUSION - rounded.LIP_CLEARANCE, 3),
        "shell_snap_seated_clearance_mm": round(
            rounded.SNAP_SOCKET_DEPTH - rounded.SNAP_PROTRUSION + rounded.LIP_CLEARANCE, 3
        ),
        "actuator_clip_radial_overlap_mm": round(ACTUATOR_RADIUS - CLIP_TIP_RADIUS, 3),
        "scope": "Nominal geometry only. Clip retention, opening force and fatigue require a test print.",
    }


@preserve_models("lra_actuator_cube")
def main() -> None:
    lid, bottom = build_parts()
    validation = validate(lid, bottom)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, solid in (("lid", lid.rotate((180, 0, 0))), ("bottom", bottom)):
        # Seam down so the rounded end and its visible perimeter print upward.
        mesh = rounded.to_mesh(solid.translate((0, 0, -solid.bounding_box()[2])))
        if rounded.boundary_edge_count(mesh) or rounded.signed_volume(mesh) <= 0:
            raise ValueError(f"{name} is not a closed print mesh")
        path = OUTPUT / f"lra_actuator_cube_{name}.stl"
        rounded.write_binary_stl(mesh, str(path), f"{MODEL_VERSION}-{name}")
        print(f"{path}: {len(mesh.faces)} triangles, boundary_edges=0")
    (OUTPUT / "validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()

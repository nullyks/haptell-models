from __future__ import annotations

import itertools
import json
import os
import struct
from collections import Counter
from dataclasses import dataclass

import manifold3d as m3d
import numpy as np

from model_archive import preserve_models


# Millimetres. Client reference supplied 2026-11-10: 80 mm cube, R8, no dimples.
MODEL_VERSION = "v07-80mm-r8-fan-only-eight-snaps"
OUTER_SIZE = 80.0
OUTER_RADIUS = 8.0
SHELL_WALL = 3.2
END_WALL = 1.2
THERMAL_PAD_SIZE = 45.0
THERMAL_PAD_CORNER_RADIUS = 4.0
HALF = OUTER_SIZE / 2.0
INNER_HALF = HALF - SHELL_WALL
PAD_FACE_Z = HALF - END_WALL
CURVE_SEGMENTS = 64
OUTPUT_DIR = os.path.join("output", "rounded_cube_box")
PRINT_OPEN_SIDE_UP = True  # First trial; compare slicing before final orientation.

# Two independent reinforced tongues on each wall; no electronics keep-outs.
LIP_CLEARANCE = 0.25
LIP_THICKNESS = 2.2
LIP_HEIGHT = 6.8
LIP_OUTER = INNER_HALF - LIP_CLEARANCE
LIP_INNER = LIP_OUTER - LIP_THICKNESS
SNAP_POSITIONS = (-16.0, 16.0)
SNAP_WIDTH = 10.0
SNAP_ROOT_Z = -14.0
SNAP_FLEX_START_Z = -11.3
SNAP_HOOK_BOTTOM = 4.1
SNAP_HOOK_PEAK_Z = 4.5
SNAP_HOOK_TOP = 6.4
SNAP_PROTRUSION = 0.95
SNAP_SOCKET_DEPTH = 1.15
SNAP_AXIAL_CLEARANCE = 0.25
SNAP_SIDE_CLEARANCE = 0.50

# JZK B0CTMDY7F1: nominal 50 x 50 x 10. Accept up to 12 mm body depth.
# Seller does not specify mounting pitch: 40 mm is provisional. M3 slots accept
# 38-42 mm pitch horizontally; verify vertical hole position before printing.
FAN_SIZE = 50.0
FAN_MAX_DEPTH = 12.0
FAN_SIDE_CLEARANCE = 0.35
FAN_MOUNT_PITCH = 40.0
FAN_SLOT_LENGTH = 7.4
FAN_SCREW_DIAMETER = 3.4
FAN_BACKING_Y = FAN_MAX_DEPTH / 2.0 + 0.6
FAN_SEAT_Z = -FAN_SIZE / 2.0
FAN_BRACKET_WALL = 4.4
FAN_SEAT_THICKNESS = 2.8
FAN_CHEEK_WALL = 3.2
FLOOR_ANCHOR_Z = -INNER_HALF - 0.2

# The thermal contact membranes are wall features, not electronics holders.
PELTIER_SIZE = 40.0
PELTIER_THICKNESS = 3.4
PELTIER_INTERFACE = 0.2
VENT_LENGTH = 10.0
VENT_HEIGHT = 2.0
VENT_CENTERS = (-20.0, 0.0, 20.0)
VENT_LEVELS = (26.0, 30.2)


@dataclass
class Mesh:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int]]


def box(size, center=(0.0, 0.0, 0.0)) -> m3d.Manifold:
    return m3d.Manifold.cube(size, center=True).translate(center)


def union(solids: list[m3d.Manifold]) -> m3d.Manifold:
    return m3d.Manifold.batch_boolean(solids, m3d.OpType.Add)


def subtract(solid: m3d.Manifold, cutters: list[m3d.Manifold]) -> m3d.Manifold:
    return m3d.Manifold.batch_boolean([solid, *cutters], m3d.OpType.Subtract)


def rounded_extrusion(width: float, depth: float, height: float, radius: float):
    profile = m3d.CrossSection.square((width - 2 * radius, depth - 2 * radius), center=True)
    return profile.offset(radius, circular_segments=CURVE_SEGMENTS).extrude(height).translate((0, 0, -height / 2))


def outer_solid() -> m3d.Manifold:
    # Circular rounding on all twelve edges, spherical corner patches.
    return box((OUTER_SIZE - 2 * OUTER_RADIUS,) * 3).minkowski_sum(
        m3d.Manifold.sphere(OUTER_RADIUS, CURVE_SEGMENTS))


def plain_shell() -> m3d.Manifold:
    # Offset the R8 exterior consistently. An inner sharp cube would break
    # through the rounded outer corners at this radius.
    inner = box((OUTER_SIZE - 2 * OUTER_RADIUS,) * 3).minkowski_sum(
        m3d.Manifold.sphere(OUTER_RADIUS - SHELL_WALL, CURVE_SEGMENTS))
    cutters = [inner]
    for sign in (-1, 1):
        # Preserve the v02 centered 45 mm pad and its 1.2 mm end wall.
        depth = SHELL_WALL - END_WALL + 0.1
        cutters.append(rounded_extrusion(THERMAL_PAD_SIZE, THERMAL_PAD_SIZE, depth,
                                        THERMAL_PAD_CORNER_RADIUS)
                       .translate((0, 0, sign * (PAD_FACE_Z - depth / 2))))
    return subtract(outer_solid(), cutters)


def half_space(*, top: bool) -> m3d.Manifold:
    return box((100, 100, 50), (0, 0, 25 if top else -25))


def prism_xz(profile, y0: float, y1: float) -> m3d.Manifold:
    return m3d.Manifold.hull_points([(x, y, z) for x, z in profile for y in (y0, y1)])


def prism_yz(profile, x0: float, x1: float) -> m3d.Manifold:
    return m3d.Manifold.hull_points([(x, y, z) for y, z in profile for x in (x0, x1)])


def snap_beam(y: float) -> m3d.Manifold:
    stem = box((LIP_THICKNESS, SNAP_WIDTH, LIP_HEIGHT - SNAP_ROOT_Z),
               ((LIP_OUTER - LIP_THICKNESS / 2), y,
                (LIP_HEIGHT + SNAP_ROOT_Z) / 2))
    # Steep extraction ramp below, long insertion ramp above.
    profile = [(LIP_OUTER - 0.1, SNAP_HOOK_BOTTOM),
               (LIP_OUTER, SNAP_HOOK_BOTTOM),
               (LIP_OUTER + SNAP_PROTRUSION, SNAP_HOOK_PEAK_Z),
               (LIP_OUTER, SNAP_HOOK_TOP), (LIP_OUTER - 0.1, SNAP_HOOK_TOP)]
    hook = m3d.Manifold.hull_points([
        (x, y + dy, z) for x, z in profile
        for dy in (-SNAP_WIDTH / 2, SNAP_WIDTH / 2)])
    # Broad, tapered root grows from the wall in the opening-down direction.
    # Nothing braces the flexible span above SNAP_FLEX_START_Z.
    root_brace = prism_xz([(LIP_INNER - 0.8, SNAP_ROOT_Z - 1.0),
                          (INNER_HALF + 0.5, SNAP_ROOT_Z - 1.0),
                          (INNER_HALF + 0.5, SNAP_FLEX_START_Z)],
                         y - (SNAP_WIDTH + 2.4) / 2,
                         y + (SNAP_WIDTH + 2.4) / 2)
    return union([stem, hook, root_brace])


def registration() -> m3d.Manifold:
    pieces = []
    cuts = [box((8, SNAP_WIDTH + 2 * SNAP_SIDE_CLEARANCE, 32),
                (INNER_HALF - 1, y, 0)) for y in SNAP_POSITIONS]
    rail = box((LIP_THICKNESS, 60, LIP_HEIGHT + 1.8),
               (LIP_OUTER - LIP_THICKNESS / 2, 0, (LIP_HEIGHT - 1.8) / 2))
    foot = box((3.8, 60, 1.8), (INNER_HALF - 0.5, 0, -0.9))
    brace = prism_xz([(LIP_INNER - 0.2, -1.7), (INNER_HALF + 0.4, -1.7),
                      (INNER_HALF + 0.4, -5.0)], -30, 30)
    wall = subtract(union([rail, foot, brace]), cuts)
    wall = union([wall, *(snap_beam(y) for y in SNAP_POSITIONS)])
    pieces.extend(wall.rotate((0, 0, angle)) for angle in (0, 90, 180, 270))
    return union(pieces)


def snap_sockets() -> list[m3d.Manifold]:
    return [box((SNAP_SOCKET_DEPTH + 0.02, SNAP_WIDTH + 0.8,
                 SNAP_HOOK_TOP - SNAP_HOOK_BOTTOM + 2 * SNAP_AXIAL_CLEARANCE),
                (INNER_HALF + SNAP_SOCKET_DEPTH / 2 - 0.01, y,
                 (SNAP_HOOK_BOTTOM + SNAP_HOOK_TOP) / 2)).rotate((0, 0, angle))
            for angle in (0, 90, 180, 270) for y in SNAP_POSITIONS]


def capsule(length: float, width: float, depth: float) -> m3d.Manifold:
    return rounded_extrusion(length, width, depth, width / 2 - 0.001)


def vents() -> list[m3d.Manifold]:
    cuts = []
    for sign, level, along, wall in itertools.product(
            (-1, 1), VENT_LEVELS, VENT_CENTERS, range(4)):
        cuts.append(capsule(VENT_LENGTH, VENT_HEIGHT, 8).rotate((90, 0, 0))
                    .translate((along, HALF - SHELL_WALL / 2, sign * level))
                    .rotate((0, 0, 90 * wall)))
    return cuts


def fan_bracket() -> m3d.Manifold:
    pieces, holes = [], []
    for sign in (-1, 1):
        x = sign * FAN_MOUNT_PITCH / 2
        backing_center = FAN_BACKING_Y + FAN_BRACKET_WALL / 2
        pieces.append(box((10.4, FAN_BRACKET_WALL, 10.4),
                          (x, backing_center, -FAN_MOUNT_PITCH / 2)))
        length = INNER_HALF + 0.4 - abs(x)
        pieces.append(box((length, FAN_BRACKET_WALL, 3.6),
                          (sign * (abs(x) + length / 2), backing_center, -25.3)))
        pieces.append(box((6.0, FAN_MAX_DEPTH + 3.8, FAN_SEAT_THICKNESS),
                          (sign * 23.0, 0.7, FAN_SEAT_Z - FAN_SEAT_THICKNESS / 2)))
        cheek_height = 22.0 + FAN_SEAT_THICKNESS
        pieces.append(box((FAN_CHEEK_WALL, FAN_MAX_DEPTH + 3.8, cheek_height),
                          (sign * (FAN_SIZE / 2 + FAN_SIDE_CLEARANCE + FAN_CHEEK_WALL / 2),
                           0.7, -3.0 - cheek_height / 2)))
        pieces.append(box((5.0, FAN_BRACKET_WALL, 5.0),
                          (sign * 24, backing_center, -23.5)))
        # Sloped load paths grow from the thick end perimeter. The floor feet
        # start outside the complete 45 mm thermal pad, not on its thin membrane.
        pieces.append(prism_xz([(sign * 23.2, FLOOR_ANCHOR_Z),
                                (sign * (INNER_HALF + 0.4), FLOOR_ANCHOR_Z),
                                (sign * (INNER_HALF + 0.4), -25.2), (sign * 14.8, -25.2)],
                               FAN_BACKING_Y, FAN_BACKING_Y + FAN_BRACKET_WALL))
        pieces.append(prism_xz([(sign * 23.2, FLOOR_ANCHOR_Z),
                                (sign * 28.55, FLOOR_ANCHOR_Z),
                                (sign * 28.55, -27.7), (sign * 20.0, -27.7)],
                               -7.2, 8.6))
        holes.append(capsule(FAN_SLOT_LENGTH, FAN_SCREW_DIAMETER, 8)
                     .rotate((90, 0, 0))
                     .translate((x, backing_center, -FAN_MOUNT_PITCH / 2)))
    return subtract(union(pieces), holes)


def build_parts() -> tuple[m3d.Manifold, m3d.Manifold]:
    shell = plain_shell()
    bottom = union([shell ^ half_space(top=False), registration(),
                    fan_bracket()])
    lid = shell ^ half_space(top=True)
    bottom = subtract(bottom, vents())
    lid = subtract(lid, [*vents(), *snap_sockets()])
    return lid, bottom


def component_envelopes() -> dict[str, m3d.Manifold]:
    components = {"fan_max_12mm_depth": box((FAN_SIZE, FAN_MAX_DEPTH, FAN_SIZE))}
    for sign, name in ((-1, "bottom_peltier"), (1, "top_peltier")):
        components[name] = box((PELTIER_SIZE, PELTIER_SIZE, PELTIER_THICKNESS),
                              (0, 0, sign * (PAD_FACE_Z - PELTIER_INTERFACE
                                              - PELTIER_THICKNESS / 2)))
    return components


def to_mesh(solid: m3d.Manifold) -> Mesh:
    mesh = solid.to_mesh()
    return Mesh([tuple(float(v) for v in row[:3]) for row in mesh.vert_properties],
                [tuple(int(i) for i in row) for row in mesh.tri_verts])


def mesh_bounds(mesh: Mesh):
    points = np.asarray(mesh.vertices)
    minimum, maximum = points.min(axis=0), points.max(axis=0)
    return minimum, maximum, maximum - minimum


def boundary_edge_count(mesh: Mesh) -> int:
    edges = Counter(tuple(sorted(edge)) for a, b, c in mesh.faces
                    for edge in ((a, b), (b, c), (c, a)))
    return sum(n != 2 for n in edges.values())


def signed_volume(mesh: Mesh) -> float:
    triangles = np.asarray(mesh.vertices)[np.asarray(mesh.faces)]
    return float(np.einsum("ij,ij->i", triangles[:, 0],
                          np.cross(triangles[:, 1], triangles[:, 2])).sum() / 6)


def write_binary_stl(mesh: Mesh, path: str, name: str) -> None:
    triangles = np.asarray(mesh.vertices)[np.asarray(mesh.faces)]
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    if np.any(lengths <= 1e-10):
        raise ValueError(f"Degenerate triangles in {name}")
    normals /= lengths[:, None]
    with open(path, "wb") as handle:
        handle.write(name.encode("ascii")[:80].ljust(80, b" "))
        handle.write(struct.pack("<I", len(triangles)))
        for normal, triangle in zip(normals, triangles):
            handle.write(struct.pack("<12fH", *normal, *triangle.flatten(), 0))


def validate(lid: m3d.Manifold, bottom: m3d.Manifold) -> dict:
    result = {"model_version": MODEL_VERSION, "assembly_bounds_mm": [OUTER_SIZE] * 3,
              "outer_edge_radius_mm": OUTER_RADIUS, "shell_wall_mm": SHELL_WALL,
              "snap_count": 8, "snap_width_mm": SNAP_WIDTH,
              "snap_beam_thickness_mm": LIP_THICKNESS,
              "snap_radial_interference_mm":
              LIP_OUTER + SNAP_PROTRUSION - INNER_HALF,
              "snap_seated_clearance_mm": INNER_HALF + SNAP_SOCKET_DEPTH
              - LIP_OUTER - SNAP_PROTRUSION,
              "socket_remaining_wall_mm": SHELL_WALL - SNAP_SOCKET_DEPTH,
              "vent_count_per_half": len(vents()) // 2,
              "component_collisions_mm3": {}}
    assert result["snap_radial_interference_mm"] > 0
    assert result["snap_seated_clearance_mm"] > 0
    assert result["socket_remaining_wall_mm"] >= 2.0
    for name, solid in (("lid", lid), ("bottom", bottom)):
        assert solid.status() == m3d.Error.NoError, (name, solid.status())
        assert len(solid.decompose()) == 1, (name, "detached geometry")
        mesh = to_mesh(solid)
        assert boundary_edge_count(mesh) == 0, name
        assert signed_volume(mesh) > 0, name
    overlap = (lid ^ bottom).volume()
    assert overlap < 1e-5, ("seated halves overlap", overlap)
    result["halves_overlap_mm3"] = overlap
    assembly_size = mesh_bounds(to_mesh(m3d.Manifold.compose([lid, bottom])))[2]
    assert np.allclose(assembly_size, [OUTER_SIZE] * 3, atol=1e-5), assembly_size
    # Probe the entire flat contact area rather than only its center point.
    for sign in (-1, 1):
        for x, y in itertools.product((-19.5, 0, 19.5), repeat=2):
            probe = box((0.2, 0.2, 4), (x, y, sign * (HALF - 1)))
            thickness = (probe ^ (lid if sign == 1 else bottom)).volume() / 0.04
            assert abs(thickness - END_WALL) < 1e-4, ("thermal pad", x, y, thickness)
    result["thermal_pad_thickness_mm"] = END_WALL
    components = component_envelopes()
    enclosure = union([lid, bottom])
    for name, component in components.items():
        overlap = (component ^ enclosure).volume()
        result["component_collisions_mm3"][name] = overlap
        assert overlap < 1e-4, (name, "enclosure collision", overlap)
    for (name_a, a), (name_b, b) in itertools.combinations(components.items(), 2):
        overlap = (a ^ b).volume()
        assert overlap < 1e-5, (name_a, name_b, "components overlap", overlap)
    # Fan must enter the lower half from the open seam.
    for name in ("fan_max_12mm_depth",):
        for height in np.linspace(0, 80, 41):
            overlap = (components[name].translate((0, 0, float(height))) ^ bottom).volume()
            assert overlap < 1e-4, (name, "blocked insertion", height, overlap)
    result["loading_check"] = "Fan enters bottom half from above."
    result["vent_size_mm"] = [VENT_LENGTH, VENT_HEIGHT]
    result["retained_internal_features"] = ["fan cradle", "eight snap tongues", "seam registration"]
    result["removed_features"] = ["UNO shelf", "battery shelf and guides", "charger shelf", "USB-C aperture"]
    result["print_open_side_up"] = PRINT_OPEN_SIDE_UP
    result["fit_scope"] = (
        "Nominal fan and Peltier envelopes only. Fan mounting pitch remains provisional. "
        "No measured snap force, physical print verification or thermal certification.")
    return result


@preserve_models("rounded_cube_box")
def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    lid, bottom = build_parts()
    validation = validate(lid, bottom)
    bottom_print = (bottom.translate((0, 0, HALF)) if PRINT_OPEN_SIDE_UP else
                    bottom.rotate((180, 0, 0)).translate((0, 0, LIP_HEIGHT)))
    lid_print = (lid.rotate((180, 0, 0)).translate((0, 0, HALF))
                 if PRINT_OPEN_SIDE_UP else lid)
    outputs = [
        ("rounded_cube_bottom", bottom_print),
        ("rounded_cube_lid", lid_print),
        ("rounded_cube_assembly_preview", union([bottom, lid]))]
    for name, solid in outputs:
        mesh = to_mesh(solid)
        path = os.path.join(OUTPUT_DIR, f"{name}.stl")
        write_binary_stl(mesh, path, f"{name}_{MODEL_VERSION}")
        _, _, size = mesh_bounds(mesh)
        print(f"{name}: triangles={len(mesh.faces)}, boundary_edges={boundary_edge_count(mesh)}, "
              f"bounds={size[0]:.3f} x {size[1]:.3f} x {size[2]:.3f} mm")
        print(f"wrote {path}")
    with open(os.path.join(OUTPUT_DIR, "validation.json"), "w", encoding="utf-8") as handle:
        json.dump(validation, handle, indent=2)
        handle.write("\n")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()

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


# Millimetres. Drawing supplied 2026-10-10; all three exterior axes are 76 mm.
# The drawing's thread annotation is superseded by the user's snap request.
MODEL_VERSION = "v03-76mm-snap-fan"
OUTER_SIZE = 76.0
OUTER_RADIUS = 1.0
SHELL_WALL = 2.8
END_WALL = 1.2
THERMAL_PAD_SIZE = 45.0
THERMAL_PAD_CORNER_RADIUS = 4.0
HALF = OUTER_SIZE / 2.0
INNER_HALF = HALF - SHELL_WALL
PAD_FACE_Z = HALF - END_WALL
CURVE_SEGMENTS = 64
OUTPUT_DIR = os.path.join("output", "rounded_cube_box")

# Independent cantilevers on the X sides. Back clearance is reserved for UNO.
LIP_CLEARANCE = 0.20
LIP_THICKNESS = 1.6
LIP_HEIGHT = 6.4
LIP_OUTER = INNER_HALF - LIP_CLEARANCE
LIP_INNER = LIP_OUTER - LIP_THICKNESS
SNAP_Y = (-10.0, 10.0)
SNAP_WIDTH = 7.2
SNAP_ROOT_Z = -10.0
SNAP_FLEX_START_Z = -8.0
SNAP_HOOK_BOTTOM = 4.0
SNAP_HOOK_PEAK_Z = 4.3
SNAP_HOOK_TOP = 6.1
SNAP_PROTRUSION = 0.70
SNAP_SOCKET_DEPTH = 0.95
SNAP_AXIAL_CLEARANCE = 0.20
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

# Seller: battery 65 x 35 x 10; TP4056 PCB 26 x 17; UNO outline 68.6 x 53.4.
# UNO component depth and TP4056 component height are provisional envelopes.
UNO_SIZE = (68.6, 14.0, 53.4)
UNO_CENTER = (0.0, -27.5, 0.0)
BATTERY_SIZE = (65.0, 10.0, 35.0)
BATTERY_CENTER = (0.0, 26.5, 0.5)
CHARGER_SIZE = (26.0, 17.0, 5.0)
CHARGER_CENTER = (0.0, 24.5, 25.5)
PELTIER_SIZE = 40.0
PELTIER_THICKNESS = 3.4
PELTIER_INTERFACE = 0.2
VENT_LENGTH = 18.0
VENT_HEIGHT = 2.4
VENT_CENTERS = (-23.0, 0.0, 23.0)
VENT_LEVELS = (15.0, 22.0, 29.0)


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
    cutters = [box((2 * INNER_HALF,) * 3)]
    for sign in (-1, 1):
        # Preserve the v02 centered 45 mm pad and its 1.2 mm end wall.
        depth = SHELL_WALL - END_WALL + 0.1
        cutters.append(rounded_extrusion(THERMAL_PAD_SIZE, THERMAL_PAD_SIZE, depth,
                                        THERMAL_PAD_CORNER_RADIUS)
                       .translate((0, 0, sign * (PAD_FACE_Z - depth / 2))))
    return subtract(outer_solid(), cutters)


def half_space(*, top: bool) -> m3d.Manifold:
    return box((100, 100, 50), (0, 0, 25 if top else -25))


def snap_beam(sign: int, y: float) -> m3d.Manifold:
    stem = box((LIP_THICKNESS, SNAP_WIDTH, LIP_HEIGHT - SNAP_ROOT_Z),
               (sign * (LIP_OUTER - LIP_THICKNESS / 2), y,
                (LIP_HEIGHT + SNAP_ROOT_Z) / 2))
    # Steep extraction ramp below, long insertion ramp above.
    profile = [(LIP_OUTER - 0.1, SNAP_HOOK_BOTTOM),
               (LIP_OUTER, SNAP_HOOK_BOTTOM),
               (LIP_OUTER + SNAP_PROTRUSION, SNAP_HOOK_PEAK_Z),
               (LIP_OUTER, SNAP_HOOK_TOP), (LIP_OUTER - 0.1, SNAP_HOOK_TOP)]
    hook = m3d.Manifold.hull_points([
        (sign * x, y + dy, z) for x, z in profile
        for dy in (-SNAP_WIDTH / 2, SNAP_WIDTH / 2)])
    root = box((3.6, SNAP_WIDTH + 2.4, 2.4),
               (sign * 34.0, y, SNAP_ROOT_Z + 1.2))
    return union([stem, hook, root])


def registration() -> m3d.Manifold:
    pieces = []
    for sign in (-1, 1):
        rail = box((LIP_THICKNESS, 36, LIP_HEIGHT + 1.6),
                   (sign * (LIP_OUTER - LIP_THICKNESS / 2), 0, (LIP_HEIGHT - 1.6) / 2))
        cuts = [box((6, SNAP_WIDTH + 2 * SNAP_SIDE_CLEARANCE, 20),
                    (sign * 34, y, 2)) for y in SNAP_Y]
        pieces.append(subtract(rail, cuts))
        pieces.append(subtract(box((3.6, 36, 1.6), (sign * 34, 0, -0.8)), cuts))
        pieces.extend(snap_beam(sign, y) for y in SNAP_Y)
    pieces.extend([
        box((56, LIP_THICKNESS, LIP_HEIGHT + 1.6),
            (0, LIP_OUTER - LIP_THICKNESS / 2, (LIP_HEIGHT - 1.6) / 2)),
        box((56, 3.6, 1.6), (0, 34, -0.8))])
    return union(pieces)


def snap_sockets() -> list[m3d.Manifold]:
    return [box((SNAP_SOCKET_DEPTH + 0.02, SNAP_WIDTH + 0.8,
                 SNAP_HOOK_TOP - SNAP_HOOK_BOTTOM + 2 * SNAP_AXIAL_CLEARANCE),
                (sign * (INNER_HALF + SNAP_SOCKET_DEPTH / 2 - 0.01), y,
                 (SNAP_HOOK_BOTTOM + SNAP_HOOK_TOP) / 2))
            for sign in (-1, 1) for y in SNAP_Y]


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
        pieces.append(box((10.4, 3.2, 10.4),
                          (x, FAN_BACKING_Y + 1.6, -FAN_MOUNT_PITCH / 2)))
        length = INNER_HALF + 0.4 - abs(x)
        pieces.append(box((length, 3.2, 2.4),
                          (sign * (abs(x) + length / 2), FAN_BACKING_Y + 1.6, -24.7)))
        pieces.append(box((6.0, FAN_MAX_DEPTH + 3.8, 1.6),
                          (sign * 23.0, 0.7, FAN_SEAT_Z - 0.8)))
        pieces.append(box((2.0, FAN_MAX_DEPTH + 3.8, 22.0),
                          (sign * (FAN_SIZE / 2 + FAN_SIDE_CLEARANCE + 1.0),
                           0.7, FAN_SEAT_Z + 11.0)))
        pieces.append(box((5.0, 3.2, 5.0),
                          (sign * 24, FAN_BACKING_Y + 1.6, -23.5)))
        holes.append(capsule(FAN_SLOT_LENGTH, FAN_SCREW_DIAMETER, 8)
                     .rotate((90, 0, 0))
                     .translate((x, FAN_BACKING_Y + 1.6, -FAN_MOUNT_PITCH / 2)))
    return subtract(union(pieces), holes)


def electronics_shelves(*, top: bool) -> m3d.Manifold:
    if top:
        # Charger horizontal above battery; USB-C points toward +Y.
        return union([
            box((29.2, 21.0, 1.6), (0, 25.0, 22.2)),
            box((1.6, 20, 3.2), (-14.0, 25, 24.0)),
            box((1.6, 20, 3.2), (14.0, 25, 24.0))])
    # Battery and UNO use foam/tape/straps, without a guessed PCB hole pattern
    # or pressure clips on the LiPo pouch. Shelf contacts are nominal supports.
    return union([
        box((67.4, 14, 2), (0, 28.5, -18.0)),
        box((2, 10, 8), (-33.8, 30.5, -14)),
        box((2, 10, 8), (33.8, 30.5, -14)),
        box((69.6, 15.5, 1.6), (0, -27.75, -28.0)),
        box((40, 1.6, 3.2), (0, -19.5, -25.6))])


def build_parts() -> tuple[m3d.Manifold, m3d.Manifold]:
    shell = plain_shell()
    bottom = union([shell ^ half_space(top=False), registration(),
                    fan_bracket(), electronics_shelves(top=False)])
    lid = union([shell ^ half_space(top=True), electronics_shelves(top=True)])
    bottom = subtract(bottom, vents())
    lid = subtract(lid, [*vents(), *snap_sockets(),
                        box((12.0, 8, 6.0), (0, 37, 26.5))])
    return lid, bottom


def component_envelopes() -> dict[str, m3d.Manifold]:
    components = {
        "fan_max_12mm_depth": box((FAN_SIZE, FAN_MAX_DEPTH, FAN_SIZE)),
        "arduino_uno_provisional_depth": box(UNO_SIZE, UNO_CENTER),
        "battery": box(BATTERY_SIZE, BATTERY_CENTER),
        "tp4056_provisional_height": box(CHARGER_SIZE, CHARGER_CENTER)}
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
              "snap_count": 4, "snap_radial_interference_mm":
              LIP_OUTER + SNAP_PROTRUSION - INNER_HALF,
              "snap_seated_clearance_mm": INNER_HALF + SNAP_SOCKET_DEPTH
              - LIP_OUTER - SNAP_PROTRUSION,
              "socket_remaining_wall_mm": SHELL_WALL - SNAP_SOCKET_DEPTH,
              "vent_count_per_half": len(vents()) // 2,
              "component_collisions_mm3": {}}
    assert result["snap_radial_interference_mm"] > 0
    assert result["snap_seated_clearance_mm"] > 0
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
            probe = box((0.2, 0.2, 4), (x, y, sign * 37))
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
    # Fan, UNO and battery must enter the lower half from the open seam.
    for name in ("fan_max_12mm_depth", "arduino_uno_provisional_depth", "battery"):
        for height in np.linspace(0, 80, 41):
            overlap = (components[name].translate((0, 0, float(height))) ^ bottom).volume()
            assert overlap < 1e-4, (name, "blocked insertion", height, overlap)
    # Allow a separate small power board; this is empty space, not a specified
    # or modeled electrical component. TP4056 itself is not a 5 V boost supply.
    power_reserve = box((16, 20, 6), (25, 23, 26))
    assert (power_reserve ^ enclosure).volume() < 1e-4
    assert all((power_reserve ^ c).volume() < 1e-4 for c in components.values())
    result["extra_power_board_space_mm"] = [16, 20, 6]
    result["loading_check"] = "Fan, UNO and battery enter bottom half from above."
    result["fit_scope"] = (
        "Nominal body envelopes only. UNO component depth 14 mm and TP4056 height "
        "5 mm are assumptions; connector overhang, plugs, wiring, straps, and "
        "power-converter/Peltier-driver hardware need measured verification. "
        "No heatsinks requested. Not a thermal-performance certification.")
    return result


@preserve_models("rounded_cube_box")
def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    lid, bottom = build_parts()
    validation = validate(lid, bottom)
    # Both openings face the bed. Bottom lip defines its bed height.
    outputs = [
        ("rounded_cube_bottom", bottom.rotate((180, 0, 0)).translate((0, 0, LIP_HEIGHT))),
        ("rounded_cube_lid", lid),
        ("rounded_cube_assembly_preview", m3d.Manifold.compose([bottom, lid]))]
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

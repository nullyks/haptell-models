from __future__ import annotations

import math
import os
from dataclasses import dataclass

import numpy as np

import generate_egg_box_stl as egg


# Units are millimetres.
MODEL_VERSION = "balance-shift-v01"
OUTPUT_DIR = os.path.join("output", "balance_shift")

# Servo working envelope: MiuZei MS24 / DS3218 class. The cradle keeps the
# narrow-long top-view footprint visible in the actual MS24 photos, while the
# output shaft axis is aligned with the egg's longitudinal Z axis.
SERVO_BODY_X = 20.0
SERVO_BODY_Y = 40.5
SERVO_BODY_Z = 40.0
SERVO_BODY_CLEARANCE = 0.8
SERVO_SHAFT_Z = -10.0
SERVO_BODY_TOP_Z = SERVO_SHAFT_Z
SERVO_BODY_BOTTOM_Z = SERVO_BODY_TOP_Z - SERVO_BODY_Z
SERVO_EAR_X = 6.0
SERVO_EAR_Y = 26.0
SERVO_EAR_RADIUS = 3.2

# Moving mass first-pass case. A 35 mm mass-center radius is not compatible
# with this shell, a 12 mm end weight, and 3-4 mm shell clearance, so this is
# the largest conservative value that clears the current bottom-half interior.
ARM_PLANE_Z = SERVO_SHAFT_Z
ARM_WEIGHT_CENTER_RADIUS = 31.8
ARM_WIDTH = 6.0
ARM_THICKNESS = 3.0
END_WEIGHT_DIAMETER = 12.0
END_WEIGHT_HEIGHT = 4.0
MOVING_MASS_CLEARANCE = 3.5

# Servo cradle / clamp geometry.
CRADLE_RAIL_WALL = 2.6
CRADLE_RAIL_TOP_Z = -12.8
CRADLE_RAIL_BOTTOM_Z = -42.0
CRADLE_SIDE_RAIL_X0 = SERVO_BODY_X / 2.0 + SERVO_BODY_CLEARANCE
CRADLE_SIDE_RAIL_X1 = CRADLE_SIDE_RAIL_X0 + CRADLE_RAIL_WALL
CRADLE_SIDE_RAIL_Y = SERVO_BODY_Y / 2.0 + 0.8
CRADLE_SADDLE_TOP_Z = SERVO_BODY_BOTTOM_Z + 2.5
CRADLE_SADDLE_BOTTOM_Z = SERVO_BODY_BOTTOM_Z
CLAMP_BOSS_RADIUS = 3.0
CLAMP_PILOT_RADIUS = 1.1
CLAMP_BOSS_TOP_Z = -12.8
CLAMP_BOSS_BOTTOM_Z = -26.0
CABLE_CHANNEL_TOP_Z = -14.0
CABLE_CHANNEL_BOTTOM_Z = -19.2


@dataclass(frozen=True)
class BalanceShiftValidation:
    safe_arm_radius: float
    achieved_arm_radius: float
    moving_clearance: float
    servo_corner_clearance: float
    exterior_overrun: float


def add_box(mesh: egg.Mesh, min_corner: tuple[float, float, float], max_corner: tuple[float, float, float]) -> None:
    x0, y0, z0 = min_corner
    x1, y1, z1 = max_corner
    vertices = [
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    ]
    ids = [mesh.add_vertex(v) for v in vertices]
    faces = [
        (0, 1, 2), (0, 2, 3),
        (4, 6, 5), (4, 7, 6),
        (0, 4, 5), (0, 5, 1),
        (1, 5, 6), (1, 6, 2),
        (2, 6, 7), (2, 7, 3),
        (3, 7, 4), (3, 4, 0),
    ]
    mesh.faces.extend((ids[a], ids[b], ids[c]) for a, b, c in faces)


def add_z_cylinder(
    mesh: egg.Mesh,
    *,
    center: tuple[float, float],
    radius: float,
    z0: float,
    z1: float,
    segments: int = 64,
) -> None:
    cx, cy = center
    bottom = []
    top = []
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        bottom.append(mesh.add_vertex((x, y, z0)))
        top.append(mesh.add_vertex((x, y, z1)))

    bottom_center = mesh.add_vertex((cx, cy, z0))
    top_center = mesh.add_vertex((cx, cy, z1))
    for i in range(segments):
        j = (i + 1) % segments
        mesh.faces.append((bottom[i], bottom[j], top[j]))
        mesh.faces.append((bottom[i], top[j], top[i]))
        mesh.faces.append((top_center, top[i], top[j]))
        mesh.faces.append((bottom_center, bottom[j], bottom[i]))


def add_z_tube(
    mesh: egg.Mesh,
    *,
    center: tuple[float, float],
    outer_radius: float,
    inner_radius: float,
    z0: float,
    z1: float,
    segments: int = 64,
) -> None:
    cx, cy = center
    outer_bottom = []
    outer_top = []
    inner_bottom = []
    inner_top = []
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        outer_bottom.append(mesh.add_vertex((cx + outer_radius * cos_a, cy + outer_radius * sin_a, z0)))
        outer_top.append(mesh.add_vertex((cx + outer_radius * cos_a, cy + outer_radius * sin_a, z1)))
        inner_bottom.append(mesh.add_vertex((cx + inner_radius * cos_a, cy + inner_radius * sin_a, z0)))
        inner_top.append(mesh.add_vertex((cx + inner_radius * cos_a, cy + inner_radius * sin_a, z1)))

    for i in range(segments):
        j = (i + 1) % segments
        mesh.faces.append((outer_bottom[i], outer_bottom[j], outer_top[j]))
        mesh.faces.append((outer_bottom[i], outer_top[j], outer_top[i]))
        mesh.faces.append((inner_bottom[i], inner_top[j], inner_bottom[j]))
        mesh.faces.append((inner_bottom[i], inner_top[i], inner_top[j]))
        mesh.faces.append((outer_top[i], inner_top[i], inner_top[j]))
        mesh.faces.append((outer_top[i], inner_top[j], outer_top[j]))
        mesh.faces.append((outer_bottom[i], inner_bottom[j], inner_bottom[i]))
        mesh.faces.append((outer_bottom[i], outer_bottom[j], inner_bottom[j]))


def build_plain_top(outer: np.ndarray) -> egg.Mesh:
    mesh = egg.Mesh([], [])

    outer_rings = []
    outer_pole = None
    for z, scale in egg.dome_profile(egg.TOP_HEIGHT, power=egg.TOP_POWER):
        if scale <= 0.0001:
            outer_pole = (0.0, 0.0, z)
        else:
            outer_rings.append(mesh.add_ring(egg.scaled(outer, scale), z))
    for a, b in zip(outer_rings, outer_rings[1:]):
        egg.add_ring_strip(mesh, a, b)
    if outer_pole is not None:
        egg.add_pole_cap(mesh, outer_rings[-1], outer_pole, normal_up=True)
    else:
        egg.add_cap(mesh, outer_rings[-1], normal_up=True)

    socket_radius = egg.lid_socket_radius()
    inner_socket = egg.ring_at_radius(outer, socket_radius)
    inner_rings = []
    for z, radius in egg.detent_profile(socket_radius, egg.DETENT_GROOVE_DEPTH):
        inner_rings.append(mesh.add_ring(egg.ring_at_radius(outer, radius), z))
    inner_rings.append(mesh.add_ring(inner_socket, egg.SOCKET_DEPTH))
    for radius, z in egg.offset_dome_profile(egg.TOP_HEIGHT, egg.TOP_POWER, egg.WALL_THICKNESS, top=True):
        if z > egg.SOCKET_DEPTH:
            inner_rings.append(mesh.add_ring(egg.ring_at_radius(outer, radius), z))
    for a, b in zip(inner_rings, inner_rings[1:]):
        egg.add_ring_strip(mesh, a, b, inward=True)
    egg.add_cap(mesh, inner_rings[-1], normal_up=False)

    egg.add_annulus(mesh, outer_rings[0], inner_rings[0], normal_up=False)
    return mesh


def build_plain_bottom(outer: np.ndarray) -> egg.Mesh:
    mesh = egg.Mesh([], [])
    lip_outer_radius = egg.lid_socket_radius() - egg.CLEARANCE
    lip_inner_radius = lip_outer_radius - egg.LIP_THICKNESS
    lip_outer = egg.ring_at_radius(outer, lip_outer_radius)
    lip_outer_chamfer = egg.ring_at_radius(outer, lip_outer_radius - 0.35)
    lip_inner = egg.ring_at_radius(outer, lip_inner_radius)
    lip_inner_chamfer = egg.ring_at_radius(outer, lip_inner_radius - 0.35)

    outer_rings = []
    outer_pole = None
    for z, scale in egg.dome_profile(egg.BOTTOM_HEIGHT, power=egg.BOTTOM_POWER):
        if scale <= 0.0001:
            outer_pole = (0.0, 0.0, -z)
        else:
            outer_rings.append(mesh.add_ring(egg.scaled(outer, scale), -z))
    for a, b in zip(outer_rings, outer_rings[1:]):
        egg.add_ring_strip(mesh, a, b, inward=True)
    if outer_pole is not None:
        egg.add_pole_cap(mesh, outer_rings[-1], outer_pole, normal_up=False)
    else:
        egg.add_cap(mesh, outer_rings[-1], normal_up=False)

    inner_rings = [mesh.add_ring(lip_inner, 0.0), mesh.add_ring(lip_inner, -egg.SOCKET_DEPTH)]
    for radius, z in egg.offset_dome_profile(egg.BOTTOM_HEIGHT, egg.BOTTOM_POWER, egg.WALL_THICKNESS, top=False):
        if z < -egg.SOCKET_DEPTH:
            inner_rings.append(mesh.add_ring(egg.ring_at_radius(outer, radius), z))
    for a, b in zip(inner_rings, inner_rings[1:]):
        egg.add_ring_strip(mesh, a, b)
    egg.add_cap(mesh, inner_rings[-1], normal_up=True)

    lip_outer_rings = []
    for z, radius in egg.detent_profile(lip_outer_radius, egg.DETENT_PROTRUSION):
        lip_outer_rings.append(mesh.add_ring(egg.ring_at_radius(outer, radius), z))
    lip_base_outer = lip_outer_rings[0]
    lip_base_inner = inner_rings[0]
    egg.add_annulus(mesh, outer_rings[0], lip_base_outer, normal_up=True)

    lip_upper_outer = mesh.add_ring(lip_outer, egg.LIP_HEIGHT - 0.9)
    lip_upper_inner = mesh.add_ring(lip_inner, egg.LIP_HEIGHT - 0.9)
    lip_top_outer = mesh.add_ring(lip_outer_chamfer, egg.LIP_HEIGHT)
    lip_top_inner = mesh.add_ring(lip_inner_chamfer, egg.LIP_HEIGHT)

    lip_outer_rings.append(lip_upper_outer)
    for a, b in zip(lip_outer_rings, lip_outer_rings[1:]):
        egg.add_ring_strip(mesh, a, b)
    egg.add_ring_strip(mesh, lip_base_inner, lip_upper_inner, inward=True)
    egg.add_ring_strip(mesh, lip_upper_outer, lip_top_outer)
    egg.add_ring_strip(mesh, lip_upper_inner, lip_top_inner, inward=True)
    egg.add_annulus(mesh, lip_top_outer, lip_top_inner, normal_up=True)

    add_servo_cradle(mesh)
    return mesh


def add_servo_cradle(mesh: egg.Mesh) -> None:
    # Central saddle supports the servo body from below.
    add_box(
        mesh,
        (-8.2, -16.8, CRADLE_SADDLE_BOTTOM_Z),
        (8.2, 16.8, CRADLE_SADDLE_TOP_Z),
    )

    # Side rails match the narrow-long servo footprint visible from above.
    add_box(
        mesh,
        (CRADLE_SIDE_RAIL_X0, -CRADLE_SIDE_RAIL_Y, CRADLE_RAIL_BOTTOM_Z),
        (CRADLE_SIDE_RAIL_X1, CRADLE_SIDE_RAIL_Y, CRADLE_RAIL_TOP_Z),
    )
    add_box(
        mesh,
        (-CRADLE_SIDE_RAIL_X1, -CRADLE_SIDE_RAIL_Y, CRADLE_RAIL_BOTTOM_Z),
        (-CRADLE_SIDE_RAIL_X0, CRADLE_SIDE_RAIL_Y, CRADLE_RAIL_TOP_Z),
    )

    # Short end bridges stiffen the rails near the mounting ears without
    # blocking the arm sweep around the shaft plane.
    add_box(mesh, (-12.8, 19.5, -34.0), (12.8, 24.0, -21.0))
    add_box(mesh, (-12.8, -24.0, -34.0), (12.8, -19.5, -21.0))

    # Mounting ear bosses are placed at the servo's two short ends, matching
    # the real servo top view more closely than the earlier left-right layout.
    for y in (-SERVO_EAR_Y, SERVO_EAR_Y):
        add_box(mesh, (-12.6, y - 2.2, -30.0), (12.6, y + 2.2, -18.5))
        for x in (-SERVO_EAR_X, SERVO_EAR_X):
            add_z_tube(
                mesh,
                center=(x, y),
                outer_radius=CLAMP_BOSS_RADIUS,
                inner_radius=CLAMP_PILOT_RADIUS,
                z0=CLAMP_BOSS_BOTTOM_Z,
                z1=CLAMP_BOSS_TOP_Z,
                segments=32,
            )

    # Outer buttresses tie the rails into the shell wall while keeping the
    # centerline volume open for the arm swing.
    add_box(mesh, (13.0, -27.0, -38.0), (21.0, 27.0, -24.0))
    add_box(mesh, (-21.0, -27.0, -38.0), (-13.0, 27.0, -24.0))

    # Cable guide toward the upper seam end of the servo.
    add_box(mesh, (-4.4, 20.0, CABLE_CHANNEL_BOTTOM_Z), (-2.6, 39.0, CABLE_CHANNEL_TOP_Z))
    add_box(mesh, (2.6, 20.0, CABLE_CHANNEL_BOTTOM_Z), (4.4, 39.0, CABLE_CHANNEL_TOP_Z))
    for x in (-2.0, 2.0):
        add_z_cylinder(mesh, center=(x, 27.0), radius=1.3, z0=CABLE_CHANNEL_BOTTOM_Z, z1=CABLE_CHANNEL_TOP_Z, segments=24)


def build_servo_envelope() -> egg.Mesh:
    mesh = egg.Mesh([], [])
    add_box(
        mesh,
        (-SERVO_BODY_X / 2.0, -SERVO_BODY_Y / 2.0, SERVO_BODY_BOTTOM_Z),
        (SERVO_BODY_X / 2.0, SERVO_BODY_Y / 2.0, SERVO_BODY_TOP_Z),
    )
    for y in (-SERVO_EAR_Y, SERVO_EAR_Y):
        add_box(mesh, (-12.0, y - 2.0, SERVO_BODY_TOP_Z - 1.2), (12.0, y + 2.0, SERVO_BODY_TOP_Z + 1.2))
        for x in (-SERVO_EAR_X, SERVO_EAR_X):
            add_z_cylinder(mesh, center=(x, y), radius=SERVO_EAR_RADIUS, z0=SERVO_BODY_TOP_Z - 1.2, z1=SERVO_BODY_TOP_Z + 1.2, segments=24)

    # The output shaft axis follows the egg's longitudinal Z axis.
    add_z_cylinder(mesh, center=(0.0, 0.0), radius=3.0, z0=SERVO_BODY_TOP_Z, z1=SERVO_BODY_TOP_Z + 5.0, segments=32)
    add_z_cylinder(mesh, center=(0.0, 0.0), radius=5.5, z0=ARM_PLANE_Z - 0.8, z1=ARM_PLANE_Z + 0.8, segments=40)
    return mesh


def build_moving_mass_envelope() -> egg.Mesh:
    mesh = egg.Mesh([], [])
    add_box(
        mesh,
        (0.0, -ARM_WIDTH / 2.0, ARM_PLANE_Z - ARM_THICKNESS / 2.0),
        (ARM_WEIGHT_CENTER_RADIUS, ARM_WIDTH / 2.0, ARM_PLANE_Z + ARM_THICKNESS / 2.0),
    )
    add_z_cylinder(
        mesh,
        center=(ARM_WEIGHT_CENTER_RADIUS, 0.0),
        radius=END_WEIGHT_DIAMETER / 2.0,
        z0=ARM_PLANE_Z - END_WEIGHT_HEIGHT / 2.0,
        z1=ARM_PLANE_Z + END_WEIGHT_HEIGHT / 2.0,
        segments=48,
    )
    # Preview-only sweep envelope for the end weight around the vertical shaft.
    add_z_tube(
        mesh,
        center=(0.0, 0.0),
        outer_radius=ARM_WEIGHT_CENTER_RADIUS + END_WEIGHT_DIAMETER / 2.0,
        inner_radius=ARM_WEIGHT_CENTER_RADIUS - END_WEIGHT_DIAMETER / 2.0,
        z0=ARM_PLANE_Z - END_WEIGHT_HEIGHT / 2.0,
        z1=ARM_PLANE_Z + END_WEIGHT_HEIGHT / 2.0,
        segments=96,
    )
    return mesh


def bottom_inner_radius_at_z(z: float) -> float:
    lip_outer_radius = egg.lid_socket_radius() - egg.CLEARANCE
    lip_inner_radius = lip_outer_radius - egg.LIP_THICKNESS
    if -egg.SOCKET_DEPTH <= z <= 0.0:
        return lip_inner_radius

    profile = sorted((z0, radius) for radius, z0 in egg.offset_dome_profile(egg.BOTTOM_HEIGHT, egg.BOTTOM_POWER, egg.WALL_THICKNESS, top=False))
    if z <= profile[0][0]:
        return profile[0][1]
    for (z0, r0), (z1, r1) in zip(profile, profile[1:]):
        if z <= z1:
            ratio = (z - z0) / (z1 - z0)
            return r0 + ratio * (r1 - r0)
    return profile[-1][1]


def moving_mass_clearance() -> tuple[float, float]:
    weight_radius = END_WEIGHT_DIAMETER / 2.0
    z_values = np.linspace(ARM_PLANE_Z - END_WEIGHT_HEIGHT / 2.0, ARM_PLANE_Z + END_WEIGHT_HEIGHT / 2.0, 25)
    safe_radius = min(bottom_inner_radius_at_z(float(z)) - weight_radius - MOVING_MASS_CLEARANCE for z in z_values)
    achieved_clearance = min(bottom_inner_radius_at_z(float(z)) - ARM_WEIGHT_CENTER_RADIUS - weight_radius for z in z_values)
    return safe_radius, achieved_clearance


def servo_corner_clearance() -> float:
    clearances = []
    for x in (-SERVO_BODY_X / 2.0, SERVO_BODY_X / 2.0):
        for y in (-SERVO_BODY_Y / 2.0, SERVO_BODY_Y / 2.0):
            corner_radius = math.hypot(x, y)
            for z in (SERVO_BODY_TOP_Z, SERVO_BODY_BOTTOM_Z):
                clearances.append(bottom_inner_radius_at_z(z) - corner_radius)
    return min(clearances)


def exterior_overrun(mesh: egg.Mesh) -> float:
    overrun = 0.0
    for x, y, z in mesh.vertices:
        if z > 0.0 or z < -egg.BOTTOM_HEIGHT:
            continue
        outer_radius = egg.radius_at_height(egg.BOTTOM_HEIGHT, egg.BOTTOM_POWER, -z)
        overrun = max(overrun, math.hypot(x, y) - outer_radius)
    return overrun


def validate(bottom_assembled: egg.Mesh) -> BalanceShiftValidation:
    safe_radius, clearance = moving_mass_clearance()
    return BalanceShiftValidation(
        safe_arm_radius=safe_radius,
        achieved_arm_radius=ARM_WEIGHT_CENTER_RADIUS,
        moving_clearance=clearance,
        servo_corner_clearance=servo_corner_clearance(),
        exterior_overrun=exterior_overrun(bottom_assembled),
    )


def write_report(mesh: egg.Mesh, filename: str, name: str) -> None:
    path = os.path.join(OUTPUT_DIR, filename)
    egg.write_binary_stl(mesh, path, name)
    mins, maxs, size = egg.mesh_bounds(mesh)
    print(f"{filename}:")
    print(f"  vertices={len(mesh.vertices)} faces={len(mesh.faces)} boundary_edges={egg.boundary_edge_count(mesh)}")
    print(f"  bounds min={mins.round(3).tolist()} max={maxs.round(3).tolist()} size={size.round(3).tolist()}")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outer = egg.make_outline()

    top_print = build_plain_top(outer)
    bottom_assembled = build_plain_bottom(outer)
    bottom_print = egg.translate_mesh(bottom_assembled, (0.0, 0.0, egg.BOTTOM_HEIGHT))
    assembly_preview = egg.combine_meshes([bottom_print, egg.translate_mesh(top_print, (0.0, 0.0, egg.BOTTOM_HEIGHT))])
    mechanism_preview = egg.combine_meshes(
        [
            assembly_preview,
            egg.translate_mesh(build_servo_envelope(), (0.0, 0.0, egg.BOTTOM_HEIGHT)),
            egg.translate_mesh(build_moving_mass_envelope(), (0.0, 0.0, egg.BOTTOM_HEIGHT)),
        ]
    )

    files = [
        (top_print, "balance_shift_lid.stl", "balance_shift_lid"),
        (bottom_print, "balance_shift_bottom.stl", "balance_shift_bottom"),
        (assembly_preview, "balance_shift_assembly_preview.stl", "balance_shift_assembly_preview"),
        (mechanism_preview, "balance_shift_mechanism_preview.stl", "balance_shift_mechanism_preview"),
    ]
    for mesh, filename, name in files:
        write_report(mesh, filename, name)

    validation = validate(bottom_assembled)
    print("parameters:")
    print(f"  model version={MODEL_VERSION}")
    print(f"  output dir={OUTPUT_DIR}")
    print(f"  max diameter={egg.DIAMETER:.1f} mm")
    print(f"  assembled length={egg.TOTAL_HEIGHT:.1f} mm")
    print(f"  wall thickness={egg.WALL_THICKNESS:.1f} mm")
    print(f"  shaft center relative to seam={SERVO_SHAFT_Z:.1f} mm")
    print(f"  servo body envelope={SERVO_BODY_X:.1f} x {SERVO_BODY_Y:.1f} x {SERVO_BODY_Z:.1f} mm")
    print(f"  moving weight envelope diameter={END_WEIGHT_DIAMETER:.1f} mm height={END_WEIGHT_HEIGHT:.1f} mm")
    print(f"  achieved weight-center arm radius={ARM_WEIGHT_CENTER_RADIUS:.2f} mm")
    print(f"  computed safe arm radius={validation.safe_arm_radius:.2f} mm")
    print(f"  moving weight shell clearance={validation.moving_clearance:.2f} mm")
    print(f"  servo body corner clearance={validation.servo_corner_clearance:.2f} mm")
    print(f"  bottom exterior overrun={validation.exterior_overrun:.4f} mm")


if __name__ == "__main__":
    main()

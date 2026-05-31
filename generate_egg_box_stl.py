from __future__ import annotations

import math
import os
import struct
from collections import Counter
from dataclasses import dataclass

import numpy as np


# Units are millimetres.
MODEL_VERSION = "v02"
DIAMETER = 90.0
TOTAL_HEIGHT = 130.0
BOTTOM_HEIGHT = 62.0
TOP_HEIGHT = TOTAL_HEIGHT - BOTTOM_HEIGHT

WALL_THICKNESS = 2.8
CLEARANCE = 0.1
LIP_THICKNESS = 2.8
LIP_HEIGHT = 6.4
SOCKET_DEPTH = 7.4
DETENT_CENTER_Z = 3.6
DETENT_WIDTH = 0.9
DETENT_RAMP = 0.9
DETENT_PROTRUSION = 0.24
DETENT_GROOVE_DEPTH = 0.22

RING_SEGMENTS = 224
CURVE_STEPS = 80
POLE_SCALE = 0.0
OUTPUT_DIR = "output"
EQUATOR_RADIUS = DIAMETER / 2.0
TOP_POWER = 0.60
BOTTOM_POWER = 0.46

MOUNT_RADIAL_CLEARANCE = 0.2
MOUNT_CLIP_WALL = 1.2
MOUNT_SEAT_MARGIN = 1.0
MOUNT_SEAT_EMBED = 0.8
MOUNT_MIN_SEAT_STANDOFF = 0.6
MOUNT_SEAT_STANDOFF_FACTOR = 0.012
MOUNT_CLIP_HEAD = 0.7
MOUNT_LIP_OVERLAP = 0.35
MOUNT_PRELOAD = 0.15
MOUNT_WIRE_SLOT_DEGREES = 70.0
MOUNT_CLIP_ARC_DEGREES = 34.0
MOUNT_ARC_STEPS = 6
MOUNT_SEAT_SEGMENTS = 64


@dataclass
class Mesh:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int]]

    def add_vertex(self, point: tuple[float, float, float]) -> int:
        self.vertices.append(point)
        return len(self.vertices) - 1

    def add_ring(self, points: np.ndarray, z: float) -> list[int]:
        return [self.add_vertex((float(x), float(y), float(z))) for x, y in points]


@dataclass(frozen=True)
class HapticMount:
    name: str
    diameter: float
    thickness: float
    z: float
    angle_degrees: float
    clip_count: int
    wire_slot_degrees: float = 0.0
    depth_extra: float = 0.0
    clip_wall: float = MOUNT_CLIP_WALL
    clip_arc_degrees: float = MOUNT_CLIP_ARC_DEGREES
    seat_margin: float = MOUNT_SEAT_MARGIN
    seat_embed: float = MOUNT_SEAT_EMBED
    clip_head: float = MOUNT_CLIP_HEAD

    @property
    def pocket_depth(self) -> float:
        return self.thickness + self.depth_extra


HAPTIC_MOUNTS = [
    HapticMount(
        "VG2230001H",
        diameter=22.0,
        thickness=30.0,
        z=36.0,
        angle_degrees=90.0,
        clip_count=4,
        clip_wall=2.4,
        clip_arc_degrees=48.0,
        seat_margin=1.6,
        seat_embed=0.6,
        clip_head=1.0,
    ),
    HapticMount(
        "VG1040003D",
        diameter=10.0,
        thickness=4.05,
        z=38.0,
        angle_degrees=225.0,
        clip_count=3,
        clip_wall=1.8,
        clip_arc_degrees=46.0,
        seat_margin=1.4,
        clip_head=0.9,
    ),
    HapticMount(
        "small_position_10x4_holder",
        diameter=10.0,
        thickness=4.05,
        z=42.0,
        angle_degrees=315.0,
        clip_count=3,
        clip_wall=1.8,
        clip_arc_degrees=46.0,
        seat_margin=1.4,
        clip_head=0.9,
    ),
]


def polygon_area(points: np.ndarray) -> float:
    x = points[:, 0]
    y = points[:, 1]
    return float(0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def smooth_closed(points: np.ndarray, iterations: int = 7, alpha: float = 0.22) -> np.ndarray:
    out = points.copy()
    for _ in range(iterations):
        out = (1.0 - alpha) * out + alpha * 0.5 * (np.roll(out, 1, axis=0) + np.roll(out, -1, axis=0))
    return out


def make_outline() -> np.ndarray:
    """Circular equator for a true 3D egg of revolution."""
    t = np.linspace(0.0, 2.0 * math.pi, RING_SEGMENTS, endpoint=False)
    points = np.column_stack((np.cos(t), np.sin(t)))

    points = smooth_closed(points, iterations=2, alpha=0.12)
    points[:, 0] *= DIAMETER / (points[:, 0].max() - points[:, 0].min())
    points[:, 1] *= DIAMETER / (points[:, 1].max() - points[:, 1].min())
    points[:, 0] -= 0.5 * (points[:, 0].min() + points[:, 0].max())
    points[:, 1] -= 0.5 * (points[:, 1].min() + points[:, 1].max())

    if polygon_area(points) < 0:
        points = points[::-1]
    return points


def offset_polygon(points: np.ndarray, distance: float) -> np.ndarray:
    """Robust inward inset for a star-shaped, organic contour.

    Radial inset keeps the lid socket and bottom lip paired without creating
    slicer-visible cracks at the narrower end.
    """
    center = points.mean(axis=0)
    vectors = points - center
    radii = np.linalg.norm(vectors, axis=1)
    factors = np.maximum((radii - distance) / radii, 0.05)
    return center + vectors * factors[:, None]


def scaled(points: np.ndarray, scale: float) -> np.ndarray:
    return points * scale


def ring_at_radius(outer: np.ndarray, radius: float) -> np.ndarray:
    return scaled(outer, radius / EQUATOR_RADIUS)


def detent_profile(base_radius: float, protrusion: float) -> list[tuple[float, float]]:
    shoulder_start = DETENT_CENTER_Z - DETENT_WIDTH / 2.0 - DETENT_RAMP
    peak_start = DETENT_CENTER_Z - DETENT_WIDTH / 2.0
    peak_end = DETENT_CENTER_Z + DETENT_WIDTH / 2.0
    shoulder_end = DETENT_CENTER_Z + DETENT_WIDTH / 2.0 + DETENT_RAMP
    return [
        (0.0, base_radius),
        (shoulder_start, base_radius),
        (peak_start, base_radius + protrusion),
        (peak_end, base_radius + protrusion),
        (shoulder_end, base_radius),
    ]


def add_ring_strip(mesh: Mesh, ring_a: list[int], ring_b: list[int], *, inward: bool = False) -> None:
    n = len(ring_a)
    for i in range(n):
        j = (i + 1) % n
        a0, a1 = ring_a[i], ring_a[j]
        b0, b1 = ring_b[i], ring_b[j]
        if inward:
            mesh.faces.append((a0, b1, a1))
            mesh.faces.append((a0, b0, b1))
        else:
            mesh.faces.append((a0, a1, b1))
            mesh.faces.append((a0, b1, b0))


def add_annulus(mesh: Mesh, outer_ring: list[int], inner_ring: list[int], *, normal_up: bool) -> None:
    n = len(outer_ring)
    for i in range(n):
        j = (i + 1) % n
        o0, o1 = outer_ring[i], outer_ring[j]
        i0, i1 = inner_ring[i], inner_ring[j]
        if normal_up:
            mesh.faces.append((o0, o1, i1))
            mesh.faces.append((o0, i1, i0))
        else:
            mesh.faces.append((o0, i1, o1))
            mesh.faces.append((o0, i0, i1))


def point_in_triangle(p: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> bool:
    eps = 1e-9
    ab = orient_2d(a, b, p)
    bc = orient_2d(b, c, p)
    ca = orient_2d(c, a, p)
    return ab >= -eps and bc >= -eps and ca >= -eps


def orient_2d(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    return float((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))


def triangulate_ring(mesh: Mesh, ring: list[int]) -> list[tuple[int, int, int]]:
    points = np.asarray([(mesh.vertices[i][0], mesh.vertices[i][1]) for i in ring], dtype=np.float64)
    order = list(range(len(ring)))
    if polygon_area(points) < 0:
        order.reverse()

    triangles: list[tuple[int, int, int]] = []
    guard = 0
    while len(order) > 3 and guard < len(ring) * len(ring):
        guard += 1
        clipped = False
        for cursor, current in enumerate(order):
            previous = order[(cursor - 1) % len(order)]
            following = order[(cursor + 1) % len(order)]
            a = points[previous]
            b = points[current]
            c = points[following]
            if orient_2d(a, b, c) <= 1e-8:
                continue
            if any(
                point_in_triangle(points[other], a, b, c)
                for other in order
                if other not in (previous, current, following)
            ):
                continue
            triangles.append((ring[previous], ring[current], ring[following]))
            del order[cursor]
            clipped = True
            break
        if not clipped:
            break

    if len(order) == 3:
        triangles.append((ring[order[0]], ring[order[1]], ring[order[2]]))
    if not triangles:
        center = mesh.add_vertex(tuple(np.asarray([mesh.vertices[i] for i in ring]).mean(axis=0)))
        n = len(ring)
        triangles = [(center, ring[i], ring[(i + 1) % n]) for i in range(n)]
    return triangles


def add_cap(mesh: Mesh, ring: list[int], *, normal_up: bool) -> None:
    for a, b, c in triangulate_ring(mesh, ring):
        if normal_up:
            mesh.faces.append((a, b, c))
        else:
            mesh.faces.append((a, c, b))


def add_pole_cap(mesh: Mesh, ring: list[int], point: tuple[float, float, float], *, normal_up: bool) -> None:
    center = mesh.add_vertex(point)
    n = len(ring)
    for i in range(n):
        j = (i + 1) % n
        if normal_up:
            mesh.faces.append((center, ring[i], ring[j]))
        else:
            mesh.faces.append((center, ring[j], ring[i]))


def dome_profile(height: float, power: float) -> list[tuple[float, float]]:
    profile: list[tuple[float, float]] = [(0.0, 1.0)]
    for step in range(1, CURVE_STEPS + 1):
        u = step / CURVE_STEPS
        z = height * u
        scale = max((1.0 - u * u) ** power, POLE_SCALE)
        profile.append((z, scale))
    return profile


def radius_at_height(height: float, power: float, z: float) -> float:
    u = max(0.0, min(1.0, z / height))
    return EQUATOR_RADIUS * max((1.0 - u * u) ** power, POLE_SCALE)


def lid_socket_radius() -> float:
    return radius_at_height(TOP_HEIGHT, TOP_POWER, SOCKET_DEPTH) - WALL_THICKNESS


def offset_dome_profile(height: float, power: float, distance: float, *, top: bool) -> list[tuple[float, float]]:
    points = np.asarray([(radius_at_height(height, power, z), z if top else -z) for z, _scale in dome_profile(height, power)])
    out: list[tuple[float, float]] = []
    for index, point in enumerate(points):
        previous_point = points[max(0, index - 1)]
        next_point = points[min(len(points) - 1, index + 1)]
        tangent = next_point - previous_point
        tangent_length = np.linalg.norm(tangent)
        if tangent_length == 0:
            continue
        tangent /= tangent_length
        inward = np.array([-tangent[1], tangent[0]]) if top else np.array([tangent[1], -tangent[0]])
        offset_point = point + distance * inward
        out.append((float(max(offset_point[0], 0.0)), float(offset_point[1])))
    return out


def top_inner_profile() -> list[tuple[float, float]]:
    profile = [(SOCKET_DEPTH, lid_socket_radius())]
    profile.extend(
        (z, radius)
        for radius, z in offset_dome_profile(TOP_HEIGHT, TOP_POWER, WALL_THICKNESS, top=True)
        if z > SOCKET_DEPTH
    )
    return sorted(profile)


def top_inner_radius_at_z(z: float) -> float:
    profile = top_inner_profile()
    if z <= profile[0][0]:
        return profile[0][1]
    for (z0, r0), (z1, r1) in zip(profile, profile[1:]):
        if z <= z1:
            ratio = (z - z0) / (z1 - z0)
            return r0 + ratio * (r1 - r0)
    return profile[-1][1]


def top_inner_slope_at_z(z: float) -> float:
    dz = 0.25
    z0 = max(SOCKET_DEPTH, z - dz)
    z1 = min(TOP_HEIGHT, z + dz)
    if z1 == z0:
        return 0.0
    return (top_inner_radius_at_z(z1) - top_inner_radius_at_z(z0)) / (z1 - z0)


def local_point(
    center: np.ndarray,
    u_axis: np.ndarray,
    v_axis: np.ndarray,
    normal: np.ndarray,
    x: float,
    y: float,
    w: float,
) -> tuple[float, float, float]:
    point = center + x * u_axis + y * v_axis + w * normal
    return (float(point[0]), float(point[1]), float(point[2]))


def mount_frame(mount: HapticMount) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    theta = math.radians(mount.angle_degrees)
    radial = np.array([math.cos(theta), math.sin(theta), 0.0], dtype=np.float64)
    tangent = np.array([-math.sin(theta), math.cos(theta), 0.0], dtype=np.float64)
    radius = top_inner_radius_at_z(mount.z)
    center = np.array([radius * radial[0], radius * radial[1], mount.z], dtype=np.float64)

    slope = top_inner_slope_at_z(mount.z)
    outward_normal = radial - slope * np.array([0.0, 0.0, 1.0], dtype=np.float64)
    outward_normal /= np.linalg.norm(outward_normal)
    cavity_normal = -outward_normal
    meridian_tangent = np.cross(cavity_normal, tangent)
    meridian_tangent /= np.linalg.norm(meridian_tangent)
    return center, tangent, meridian_tangent, cavity_normal


def add_oriented_cylinder(
    mesh: Mesh,
    center: np.ndarray,
    u_axis: np.ndarray,
    v_axis: np.ndarray,
    normal: np.ndarray,
    *,
    radius: float,
    w0: float,
    w1: float,
    segments: int,
) -> None:
    bottom = []
    top = []
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        bottom.append(mesh.add_vertex(local_point(center, u_axis, v_axis, normal, x, y, w0)))
        top.append(mesh.add_vertex(local_point(center, u_axis, v_axis, normal, x, y, w1)))

    bottom_center = mesh.add_vertex(local_point(center, u_axis, v_axis, normal, 0.0, 0.0, w0))
    top_center = mesh.add_vertex(local_point(center, u_axis, v_axis, normal, 0.0, 0.0, w1))
    for i in range(segments):
        j = (i + 1) % segments
        mesh.faces.append((bottom[i], bottom[j], top[j]))
        mesh.faces.append((bottom[i], top[j], top[i]))
        mesh.faces.append((top_center, top[i], top[j]))
        mesh.faces.append((bottom_center, bottom[j], bottom[i]))


def add_annular_arc_solid(
    mesh: Mesh,
    center: np.ndarray,
    u_axis: np.ndarray,
    v_axis: np.ndarray,
    normal: np.ndarray,
    *,
    inner_radius: float,
    outer_radius: float,
    start_degrees: float,
    end_degrees: float,
    w0: float,
    w1: float,
    steps: int,
) -> None:
    angles = [math.radians(start_degrees + (end_degrees - start_degrees) * i / steps) for i in range(steps + 1)]
    inner_bottom = []
    outer_bottom = []
    inner_top = []
    outer_top = []
    for angle in angles:
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        inner_bottom.append(mesh.add_vertex(local_point(center, u_axis, v_axis, normal, inner_radius * cos_a, inner_radius * sin_a, w0)))
        outer_bottom.append(mesh.add_vertex(local_point(center, u_axis, v_axis, normal, outer_radius * cos_a, outer_radius * sin_a, w0)))
        inner_top.append(mesh.add_vertex(local_point(center, u_axis, v_axis, normal, inner_radius * cos_a, inner_radius * sin_a, w1)))
        outer_top.append(mesh.add_vertex(local_point(center, u_axis, v_axis, normal, outer_radius * cos_a, outer_radius * sin_a, w1)))

    for i in range(steps):
        j = i + 1
        mesh.faces.append((outer_bottom[i], outer_bottom[j], outer_top[j]))
        mesh.faces.append((outer_bottom[i], outer_top[j], outer_top[i]))
        mesh.faces.append((inner_bottom[i], inner_top[j], inner_bottom[j]))
        mesh.faces.append((inner_bottom[i], inner_top[i], inner_top[j]))
        mesh.faces.append((inner_top[i], outer_top[i], outer_top[j]))
        mesh.faces.append((inner_top[i], outer_top[j], inner_top[j]))
        mesh.faces.append((inner_bottom[i], outer_bottom[j], outer_bottom[i]))
        mesh.faces.append((inner_bottom[i], inner_bottom[j], outer_bottom[j]))

    mesh.faces.append((inner_bottom[0], outer_bottom[0], outer_top[0]))
    mesh.faces.append((inner_bottom[0], outer_top[0], inner_top[0]))
    mesh.faces.append((inner_bottom[-1], outer_top[-1], outer_bottom[-1]))
    mesh.faces.append((inner_bottom[-1], inner_top[-1], outer_top[-1]))


def mount_clip_centers(mount: HapticMount) -> list[float]:
    available_span = 360.0 - MOUNT_WIRE_SLOT_DEGREES
    start = mount.wire_slot_degrees + MOUNT_WIRE_SLOT_DEGREES / 2.0
    return [start + available_span * (i + 0.5) / mount.clip_count for i in range(mount.clip_count)]


def add_haptic_mount(mesh: Mesh, mount: HapticMount) -> None:
    center, u_axis, v_axis, normal = mount_frame(mount)
    motor_radius = mount.diameter / 2.0
    seat_radius = motor_radius + mount.seat_margin
    seat_top_w = max(MOUNT_MIN_SEAT_STANDOFF, MOUNT_SEAT_STANDOFF_FACTOR * seat_radius * seat_radius)
    wall_inner_radius = motor_radius + MOUNT_RADIAL_CLEARANCE
    wall_outer_radius = wall_inner_radius + mount.clip_wall
    wall_top_w = seat_top_w + mount.pocket_depth + mount.clip_head
    lip_bottom_w = seat_top_w + mount.pocket_depth - MOUNT_PRELOAD
    lip_inner_radius = max(0.0, motor_radius - MOUNT_LIP_OVERLAP)

    add_oriented_cylinder(
        mesh,
        center,
        u_axis,
        v_axis,
        normal,
        radius=seat_radius,
        w0=-mount.seat_embed,
        w1=seat_top_w,
        segments=MOUNT_SEAT_SEGMENTS,
    )

    for clip_center in mount_clip_centers(mount):
        start = clip_center - mount.clip_arc_degrees / 2.0
        end = clip_center + mount.clip_arc_degrees / 2.0
        add_annular_arc_solid(
            mesh,
            center,
            u_axis,
            v_axis,
            normal,
            inner_radius=wall_inner_radius,
            outer_radius=wall_outer_radius,
            start_degrees=start,
            end_degrees=end,
            w0=seat_top_w,
            w1=wall_top_w,
            steps=MOUNT_ARC_STEPS,
        )
        add_annular_arc_solid(
            mesh,
            center,
            u_axis,
            v_axis,
            normal,
            inner_radius=lip_inner_radius,
            outer_radius=wall_outer_radius,
            start_degrees=start,
            end_degrees=end,
            w0=lip_bottom_w,
            w1=wall_top_w,
            steps=MOUNT_ARC_STEPS,
        )


def build_top(outer: np.ndarray) -> Mesh:
    mesh = Mesh([], [])

    outer_rings = []
    outer_pole = None
    for z, scale in dome_profile(TOP_HEIGHT, power=TOP_POWER):
        if scale <= 0.0001:
            outer_pole = (0.0, 0.0, z)
        else:
            outer_rings.append(mesh.add_ring(scaled(outer, scale), z))
    for a, b in zip(outer_rings, outer_rings[1:]):
        add_ring_strip(mesh, a, b)
    if outer_pole is not None:
        add_pole_cap(mesh, outer_rings[-1], outer_pole, normal_up=True)
    else:
        add_cap(mesh, outer_rings[-1], normal_up=True)

    socket_radius = lid_socket_radius()
    inner_socket = ring_at_radius(outer, socket_radius)
    inner_rings = []
    for z, radius in detent_profile(socket_radius, DETENT_GROOVE_DEPTH):
        inner_rings.append(mesh.add_ring(ring_at_radius(outer, radius), z))
    inner_rings.append(mesh.add_ring(inner_socket, SOCKET_DEPTH))
    for radius, z in offset_dome_profile(TOP_HEIGHT, TOP_POWER, WALL_THICKNESS, top=True):
        if z > SOCKET_DEPTH:
            inner_rings.append(mesh.add_ring(ring_at_radius(outer, radius), z))
    for a, b in zip(inner_rings, inner_rings[1:]):
        add_ring_strip(mesh, a, b, inward=True)
    add_cap(mesh, inner_rings[-1], normal_up=False)

    add_annulus(mesh, outer_rings[0], inner_rings[0], normal_up=False)
    for mount in HAPTIC_MOUNTS:
        add_haptic_mount(mesh, mount)
    return mesh


def build_bottom(outer: np.ndarray) -> Mesh:
    mesh = Mesh([], [])
    lip_outer_radius = lid_socket_radius() - CLEARANCE
    lip_inner_radius = lip_outer_radius - LIP_THICKNESS
    lip_outer = ring_at_radius(outer, lip_outer_radius)
    lip_outer_chamfer = ring_at_radius(outer, lip_outer_radius - 0.35)
    lip_inner = ring_at_radius(outer, lip_inner_radius)
    lip_inner_chamfer = ring_at_radius(outer, lip_inner_radius - 0.35)

    outer_rings = []
    outer_pole = None
    for z, scale in dome_profile(BOTTOM_HEIGHT, power=BOTTOM_POWER):
        if scale <= 0.0001:
            outer_pole = (0.0, 0.0, -z)
        else:
            outer_rings.append(mesh.add_ring(scaled(outer, scale), -z))
    for a, b in zip(outer_rings, outer_rings[1:]):
        add_ring_strip(mesh, a, b, inward=True)
    if outer_pole is not None:
        add_pole_cap(mesh, outer_rings[-1], outer_pole, normal_up=False)
    else:
        add_cap(mesh, outer_rings[-1], normal_up=False)

    inner_rings = [mesh.add_ring(lip_inner, 0.0), mesh.add_ring(lip_inner, -SOCKET_DEPTH)]
    for radius, z in offset_dome_profile(BOTTOM_HEIGHT, BOTTOM_POWER, WALL_THICKNESS, top=False):
        if z < -SOCKET_DEPTH:
            inner_rings.append(mesh.add_ring(ring_at_radius(outer, radius), z))
    for a, b in zip(inner_rings, inner_rings[1:]):
        add_ring_strip(mesh, a, b)
    add_cap(mesh, inner_rings[-1], normal_up=True)

    # Flat seam surfaces and the male registration lip.
    lip_outer_rings = []
    for z, radius in detent_profile(lip_outer_radius, DETENT_PROTRUSION):
        lip_outer_rings.append(mesh.add_ring(ring_at_radius(outer, radius), z))
    lip_base_outer = lip_outer_rings[0]
    lip_base_inner = inner_rings[0]
    add_annulus(mesh, outer_rings[0], lip_base_outer, normal_up=True)

    lip_upper_outer = mesh.add_ring(lip_outer, LIP_HEIGHT - 0.9)
    lip_upper_inner = mesh.add_ring(lip_inner, LIP_HEIGHT - 0.9)
    lip_top_outer = mesh.add_ring(lip_outer_chamfer, LIP_HEIGHT)
    lip_top_inner = mesh.add_ring(lip_inner_chamfer, LIP_HEIGHT)

    lip_outer_rings.append(lip_upper_outer)
    for a, b in zip(lip_outer_rings, lip_outer_rings[1:]):
        add_ring_strip(mesh, a, b)
    add_ring_strip(mesh, lip_base_inner, lip_upper_inner, inward=True)
    add_ring_strip(mesh, lip_upper_outer, lip_top_outer)
    add_ring_strip(mesh, lip_upper_inner, lip_top_inner, inward=True)
    add_annulus(mesh, lip_top_outer, lip_top_inner, normal_up=True)

    return mesh


def face_normal(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> tuple[float, float, float]:
    normal = np.cross(b - a, c - a)
    length = float(np.linalg.norm(normal))
    if length == 0:
        return (0.0, 0.0, 0.0)
    normal /= length
    return (float(normal[0]), float(normal[1]), float(normal[2]))


def write_binary_stl(mesh: Mesh, path: str, name: str) -> None:
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    header = name.encode("ascii", errors="ignore")[:80].ljust(80, b" ")
    with open(path, "wb") as f:
        f.write(header)
        f.write(struct.pack("<I", len(mesh.faces)))
        for face in mesh.faces:
            a, b, c = vertices[list(face)]
            f.write(struct.pack("<3f", *face_normal(a, b, c)))
            f.write(struct.pack("<3f", *a))
            f.write(struct.pack("<3f", *b))
            f.write(struct.pack("<3f", *c))
            f.write(struct.pack("<H", 0))


def translate_mesh(mesh: Mesh, delta: tuple[float, float, float]) -> Mesh:
    dx, dy, dz = delta
    return Mesh(
        [(x + dx, y + dy, z + dz) for x, y, z in mesh.vertices],
        mesh.faces.copy(),
    )


def combine_meshes(meshes: list[Mesh]) -> Mesh:
    combined = Mesh([], [])
    offset = 0
    for mesh in meshes:
        combined.vertices.extend(mesh.vertices)
        combined.faces.extend((a + offset, b + offset, c + offset) for a, b, c in mesh.faces)
        offset += len(mesh.vertices)
    return combined


def mesh_bounds(mesh: Mesh) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    vertices = np.asarray(mesh.vertices)
    mins = vertices.min(axis=0)
    maxs = vertices.max(axis=0)
    return mins, maxs, maxs - mins


def boundary_edge_count(mesh: Mesh) -> int:
    edges: Counter[tuple[int, int]] = Counter()
    for face in mesh.faces:
        for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edges[tuple(sorted((a, b)))] += 1
    return sum(1 for count in edges.values() if count != 2)


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outer = make_outline()
    top_print = build_top(outer)
    bottom_assembled = build_bottom(outer)
    bottom_print = translate_mesh(bottom_assembled, (0.0, 0.0, BOTTOM_HEIGHT))
    assembly_preview = combine_meshes([bottom_print, translate_mesh(top_print, (0.0, 0.0, BOTTOM_HEIGHT))])

    files = [
        (top_print, "egg_box_lid.stl", "egg_box_lid"),
        (bottom_print, "egg_box_bottom.stl", "egg_box_bottom"),
        (assembly_preview, "egg_box_assembly_preview.stl", "egg_box_assembly_preview"),
    ]
    for mesh, filename, name in files:
        path = os.path.join(OUTPUT_DIR, filename)
        write_binary_stl(mesh, path, name)
        mins, maxs, size = mesh_bounds(mesh)
        print(f"{filename}:")
        print(f"  vertices={len(mesh.vertices)} faces={len(mesh.faces)} boundary_edges={boundary_edge_count(mesh)}")
        print(f"  bounds min={mins.round(3).tolist()} max={maxs.round(3).tolist()} size={size.round(3).tolist()}")

    print("parameters:")
    print(f"  model version={MODEL_VERSION}")
    print(f"  max diameter={DIAMETER:.1f} mm")
    print(f"  assembled length={TOTAL_HEIGHT:.1f} mm")
    print(f"  wall thickness={WALL_THICKNESS:.1f} mm")
    print(f"  fit clearance={CLEARANCE:.1f} mm")
    print(f"  lip height={LIP_HEIGHT:.1f} mm")
    print("haptic mounts:")
    for mount in HAPTIC_MOUNTS:
        print(
            f"  {mount.name}: diameter={mount.diameter:.2f} mm "
            f"thickness={mount.thickness:.2f} mm pocket_depth={mount.pocket_depth:.2f} mm "
            f"z={mount.z:.1f} mm angle={mount.angle_degrees:.1f} deg clips={mount.clip_count} "
            f"clip_wall={mount.clip_wall:.2f} mm clip_arc={mount.clip_arc_degrees:.1f} deg"
        )


if __name__ == "__main__":
    main()

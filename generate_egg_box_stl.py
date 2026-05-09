from __future__ import annotations

import math
import os
import struct
from collections import Counter
from dataclasses import dataclass

import numpy as np


# Units are millimetres.
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
DETENT_WIDTH = 1.1
DETENT_RAMP = 0.6
DETENT_PROTRUSION = 0.32
DETENT_GROOVE_DEPTH = 0.27

RING_SEGMENTS = 224
CURVE_STEPS = 80
POLE_SCALE = 0.0
OUTPUT_DIR = "output"
EQUATOR_RADIUS = DIAMETER / 2.0
TOP_POWER = 0.60
BOTTOM_POWER = 0.46


@dataclass
class Mesh:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int]]

    def add_vertex(self, point: tuple[float, float, float]) -> int:
        self.vertices.append(point)
        return len(self.vertices) - 1

    def add_ring(self, points: np.ndarray, z: float) -> list[int]:
        return [self.add_vertex((float(x), float(y), float(z))) for x, y in points]


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
    print(f"  max diameter={DIAMETER:.1f} mm")
    print(f"  assembled length={TOTAL_HEIGHT:.1f} mm")
    print(f"  wall thickness={WALL_THICKNESS:.1f} mm")
    print(f"  fit clearance={CLEARANCE:.1f} mm")
    print(f"  lip height={LIP_HEIGHT:.1f} mm")


if __name__ == "__main__":
    main()

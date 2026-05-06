from __future__ import annotations

import math
import os
import struct
from collections import Counter
from dataclasses import dataclass

import numpy as np


# Units are millimetres.
LENGTH = 150.0
WIDTH = 104.0
TOTAL_HEIGHT = 60.0

WALL_THICKNESS = 2.4
CLEARANCE = 0.2
LIP_THICKNESS = 1.6
LIP_HEIGHT = 7.2
SOCKET_DEPTH = 8.4
STRAIGHT_BAND = 9.6

RING_SEGMENTS = 224
CURVE_STEPS = 18
OUTPUT_DIR = "output"


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


def catmull_rom_open(points: np.ndarray, samples_per_segment: int) -> np.ndarray:
    out = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        p0 = points[i - 1] if i > 0 else p1 + (p1 - p2)
        p3 = points[i + 2] if i + 2 < len(points) else p2 + (p2 - p1)
        for j in range(samples_per_segment):
            t = j / samples_per_segment
            t2 = t * t
            t3 = t2 * t
            out.append(
                0.5
                * (
                    (2.0 * p1)
                    + (-p0 + p2) * t
                    + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
                    + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
                )
            )
    out.append(points[-1])
    return np.asarray(out)


def make_outline() -> np.ndarray:
    """Rounded, slightly heart-like pebble contour with no deep cleft."""
    half_samples = RING_SEGMENTS // 2
    control = np.array(
        [
            [-75.0, 0.0],
            [-68.0, 12.0],
            [-55.0, 29.0],
            [-32.0, 43.0],
            [0.0, 51.0],
            [34.0, 49.0],
            [61.0, 34.0],
            [75.5, 20.0],
            [78.0, 8.5],
            [70.5, 0.0],
        ],
        dtype=np.float64,
    )
    samples_per_segment = max(4, half_samples // (len(control) - 1))
    upper = catmull_rom_open(control, samples_per_segment)
    upper = upper[np.linspace(0, len(upper) - 1, half_samples + 1).round().astype(int)]
    lower = upper[-2:0:-1] * np.array([1.0, -1.0])
    points = np.vstack((upper, lower))

    points = smooth_closed(points, iterations=3, alpha=0.18)
    points[:, 0] *= LENGTH / (points[:, 0].max() - points[:, 0].min())
    points[:, 1] *= WIDTH / (points[:, 1].max() - points[:, 1].min())
    points[:, 0] -= 0.5 * (points[:, 0].min() + points[:, 0].max())
    points[:, 1] -= 0.5 * (points[:, 1].min() + points[:, 1].max())

    if polygon_area(points) < 0:
        points = points[::-1]
    return points


def line_intersection(p: np.ndarray, d: np.ndarray, q: np.ndarray, e: np.ndarray) -> np.ndarray:
    cross = d[0] * e[1] - d[1] * e[0]
    if abs(cross) < 1e-9:
        return 0.5 * (p + q)
    qp = q - p
    t = (qp[0] * e[1] - qp[1] * e[0]) / cross
    return p + t * d


def offset_polygon(points: np.ndarray, distance: float) -> np.ndarray:
    """Robust inward inset for a star-shaped, organic contour.

    The first version used line intersections for a mathematically cleaner
    normal offset, but tight heart points can make those offset lines cross.
    Radial inset keeps the lid socket and bottom lip paired without creating
    slicer-visible cracks at the point.
    """
    center = points.mean(axis=0)
    vectors = points - center
    radii = np.linalg.norm(vectors, axis=1)
    factors = np.maximum((radii - distance) / radii, 0.05)
    return center + vectors * factors[:, None]


def scaled(points: np.ndarray, scale: float) -> np.ndarray:
    return points * scale


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


def dome_profile(height: float, straight_band: float) -> list[tuple[float, float]]:
    profile: list[tuple[float, float]] = [(0.0, 1.0)]
    if straight_band > 0:
        profile.append((straight_band, 1.0))
    curved_height = height - straight_band
    for step in range(1, CURVE_STEPS + 1):
        u = step / CURVE_STEPS
        phi = u * math.pi * 0.5
        z = straight_band + curved_height * math.sin(phi)
        scale = max(math.cos(phi) ** 0.68, 0.015)
        profile.append((z, scale))
    return profile


def build_top(outer: np.ndarray) -> Mesh:
    mesh = Mesh([], [])
    half_height = TOTAL_HEIGHT / 2.0
    inner = offset_polygon(outer, WALL_THICKNESS)

    outer_rings = []
    for z, scale in dome_profile(half_height, STRAIGHT_BAND):
        outer_rings.append(mesh.add_ring(scaled(outer, scale), z))
    for a, b in zip(outer_rings, outer_rings[1:]):
        add_ring_strip(mesh, a, b)
    add_cap(mesh, outer_rings[-1], normal_up=True)

    inner_height = half_height - WALL_THICKNESS
    inner_rings = [mesh.add_ring(inner, 0.0), mesh.add_ring(inner, SOCKET_DEPTH)]
    for z, scale in dome_profile(inner_height - SOCKET_DEPTH, 0.0)[1:]:
        inner_rings.append(mesh.add_ring(scaled(inner, scale), SOCKET_DEPTH + z))
    for a, b in zip(inner_rings, inner_rings[1:]):
        add_ring_strip(mesh, a, b, inward=True)
    add_cap(mesh, inner_rings[-1], normal_up=False)

    add_annulus(mesh, outer_rings[0], inner_rings[0], normal_up=False)
    return mesh


def build_bottom(outer: np.ndarray) -> Mesh:
    mesh = Mesh([], [])
    half_height = TOTAL_HEIGHT / 2.0
    lip_outer = offset_polygon(outer, WALL_THICKNESS + CLEARANCE)
    lip_outer_chamfer = offset_polygon(outer, WALL_THICKNESS + CLEARANCE + 0.35)
    lip_inner = offset_polygon(outer, WALL_THICKNESS + CLEARANCE + LIP_THICKNESS)
    lip_inner_chamfer = offset_polygon(outer, WALL_THICKNESS + CLEARANCE + LIP_THICKNESS + 0.35)

    outer_rings = []
    for z, scale in dome_profile(half_height, STRAIGHT_BAND):
        outer_rings.append(mesh.add_ring(scaled(outer, scale), -z))
    for a, b in zip(outer_rings, outer_rings[1:]):
        add_ring_strip(mesh, a, b, inward=True)
    add_cap(mesh, outer_rings[-1], normal_up=False)

    inner_height = half_height - WALL_THICKNESS
    inner_rings = [mesh.add_ring(lip_inner, 0.0), mesh.add_ring(lip_inner, -SOCKET_DEPTH)]
    for z, scale in dome_profile(inner_height - SOCKET_DEPTH, 0.0)[1:]:
        inner_rings.append(mesh.add_ring(scaled(lip_inner, scale), -(SOCKET_DEPTH + z)))
    for a, b in zip(inner_rings, inner_rings[1:]):
        add_ring_strip(mesh, a, b)
    add_cap(mesh, inner_rings[-1], normal_up=True)

    # Flat seam surfaces and the male registration lip.
    lip_base_outer = mesh.add_ring(lip_outer, 0.0)
    lip_base_inner = inner_rings[0]
    add_annulus(mesh, outer_rings[0], lip_base_outer, normal_up=True)

    lip_upper_outer = mesh.add_ring(lip_outer, LIP_HEIGHT - 0.9)
    lip_upper_inner = mesh.add_ring(lip_inner, LIP_HEIGHT - 0.9)
    lip_top_outer = mesh.add_ring(lip_outer_chamfer, LIP_HEIGHT)
    lip_top_inner = mesh.add_ring(lip_inner_chamfer, LIP_HEIGHT)

    add_ring_strip(mesh, lip_base_outer, lip_upper_outer)
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
    bottom_print = translate_mesh(bottom_assembled, (0.0, 0.0, TOTAL_HEIGHT / 2.0))
    assembly_preview = combine_meshes([bottom_print, translate_mesh(top_print, (0.0, 0.0, TOTAL_HEIGHT / 2.0))])

    files = [
        (top_print, "heart_box_lid.stl", "heart_box_lid"),
        (bottom_print, "heart_box_bottom.stl", "heart_box_bottom"),
        (assembly_preview, "heart_box_assembly_preview.stl", "heart_box_assembly_preview"),
    ]
    for mesh, filename, name in files:
        path = os.path.join(OUTPUT_DIR, filename)
        write_binary_stl(mesh, path, name)
        mins, maxs, size = mesh_bounds(mesh)
        print(f"{filename}:")
        print(f"  vertices={len(mesh.vertices)} faces={len(mesh.faces)} boundary_edges={boundary_edge_count(mesh)}")
        print(f"  bounds min={mins.round(3).tolist()} max={maxs.round(3).tolist()} size={size.round(3).tolist()}")

    print("parameters:")
    print(f"  longest dimension={LENGTH:.1f} mm")
    print(f"  wall thickness={WALL_THICKNESS:.1f} mm")
    print(f"  fit clearance={CLEARANCE:.1f} mm")
    print(f"  lip height={LIP_HEIGHT:.1f} mm")


if __name__ == "__main__":
    main()

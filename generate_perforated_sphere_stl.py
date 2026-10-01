from __future__ import annotations

import math
import os
import struct
from collections import Counter
from dataclasses import dataclass

import manifold3d as m3d
import numpy as np


# Units are millimetres. Designed for PLA with a 0.4 mm nozzle.
MODEL_VERSION = "v02"
OUTER_DIAMETER = 91.0
OUTER_RADIUS = OUTER_DIAMETER / 2.0
WALL_THICKNESS = 2.8
INNER_RADIUS = OUTER_RADIUS - WALL_THICKNESS

LARGE_HOLE_DIAMETER = 45.0
SMALL_HOLE_DIAMETER = 35.0
HOLE_ELEVATION_DEGREES = 42.0
HOLE_EDGE_CHAMFER = 1.2

THREAD_BASE_RADIUS = 39.4
THREAD_HEIGHT = 0.70
THREAD_PITCH = 3.2
THREAD_ENGAGEMENT = 8.0
THREAD_RADIAL_CLEARANCE = 0.30
THREAD_MALE_INNER_RADIUS = 37.0
THREAD_FEMALE_OUTER_RADIUS = 42.4
THREAD_LEAD_IN = 0.8
CONNECTOR_WEB_THICKNESS = 0.8

SPHERE_SEGMENTS = 192
HOLE_SEGMENTS = 128
THREAD_ANGLE_STEPS = 240
THREAD_Z_STEPS = 96
OUTPUT_DIR = os.path.join("output", "perforated_sphere")


@dataclass(frozen=True)
class Hole:
    name: str
    diameter: float
    elevation_degrees: float
    azimuth_degrees: float
    part: str


HOLES = [
    Hole("top_small_center", SMALL_HOLE_DIAMETER, HOLE_ELEVATION_DEGREES, 0.0, "top"),
    Hole("top_large_120", LARGE_HOLE_DIAMETER, HOLE_ELEVATION_DEGREES, 120.0, "top"),
    Hole("top_large_240", LARGE_HOLE_DIAMETER, HOLE_ELEVATION_DEGREES, 240.0, "top"),
    Hole("bottom_small_60", SMALL_HOLE_DIAMETER, -HOLE_ELEVATION_DEGREES, 60.0, "bottom"),
    Hole("bottom_large_180", LARGE_HOLE_DIAMETER, -HOLE_ELEVATION_DEGREES, 180.0, "bottom"),
    Hole("bottom_small_300", SMALL_HOLE_DIAMETER, -HOLE_ELEVATION_DEGREES, 300.0, "bottom"),
]


@dataclass
class TriangleMesh:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int]]

    def add_ring(self, points: np.ndarray, z: float) -> list[int]:
        start = len(self.vertices)
        self.vertices.extend((float(x), float(y), float(z)) for x, y in points)
        return list(range(start, start + len(points)))


def batch_union(solids: list[m3d.Manifold]) -> m3d.Manifold:
    return m3d.Manifold.batch_boolean(solids, m3d.OpType.Add)


def batch_subtract(head: m3d.Manifold, cutters: list[m3d.Manifold]) -> m3d.Manifold:
    if not cutters:
        return head
    return m3d.Manifold.batch_boolean([head, *cutters], m3d.OpType.Subtract)


def exact_sphere(radius: float) -> m3d.Manifold:
    """Mathematically spherical exterior/interior without polar flats."""
    return m3d.Manifold.sphere(radius, SPHERE_SEGMENTS)


def direction_from_angles(elevation_degrees: float, azimuth_degrees: float) -> np.ndarray:
    elevation = math.radians(elevation_degrees)
    azimuth = math.radians(azimuth_degrees)
    return np.asarray(
        (
            math.cos(elevation) * math.sin(azimuth),
            -math.cos(elevation) * math.cos(azimuth),
            math.sin(elevation),
        ),
        dtype=np.float64,
    )


def orient_z_axis(solid: m3d.Manifold, direction: np.ndarray, center: np.ndarray) -> m3d.Manifold:
    direction = direction / np.linalg.norm(direction)
    reference = np.asarray((0.0, 0.0, 1.0) if abs(direction[2]) < 0.9 else (1.0, 0.0, 0.0))
    u_axis = np.cross(reference, direction)
    u_axis /= np.linalg.norm(u_axis)
    v_axis = np.cross(direction, u_axis)
    matrix = np.column_stack((u_axis, v_axis, direction, center))
    return solid.transform(matrix.tolist())


def hole_cutter(hole: Hole) -> m3d.Manifold:
    radius = hole.diameter / 2.0
    direction = direction_from_angles(hole.elevation_degrees, hole.azimuth_degrees)

    # The main cutter starts at the sphere centre and exits only through the
    # selected side, so it cannot create an antipodal opening.
    cutter_length = OUTER_RADIUS + 6.0
    main = m3d.Manifold.cylinder(
        cutter_length,
        radius,
        radius,
        HOLE_SEGMENTS,
        center=True,
    )
    main = orient_z_axis(main, direction, direction * (cutter_length / 2.0))

    # A shallow outer countersink removes a sharp support-scarred rim.
    nominal_surface = math.sqrt(max(OUTER_RADIUS * OUTER_RADIUS - radius * radius, 0.0))
    chamfer_depth = 2.0
    chamfer = m3d.Manifold.cylinder(
        chamfer_depth + 2.0,
        radius,
        radius + HOLE_EDGE_CHAMFER,
        HOLE_SEGMENTS,
        center=True,
    )
    chamfer_center = direction * nominal_surface
    chamfer = orient_z_axis(chamfer, direction, chamfer_center)
    return batch_union([main, chamfer])


def add_ring_strip(mesh: TriangleMesh, lower: list[int], upper: list[int], *, inward: bool) -> None:
    count = len(lower)
    for index in range(count):
        nxt = (index + 1) % count
        if inward:
            mesh.faces.append((lower[index], upper[nxt], lower[nxt]))
            mesh.faces.append((lower[index], upper[index], upper[nxt]))
        else:
            mesh.faces.append((lower[index], lower[nxt], upper[nxt]))
            mesh.faces.append((lower[index], upper[nxt], upper[index]))


def add_annulus(
    mesh: TriangleMesh,
    outer: list[int],
    inner: list[int],
    *,
    normal_up: bool,
) -> None:
    count = len(outer)
    for index in range(count):
        nxt = (index + 1) % count
        if normal_up:
            mesh.faces.append((outer[index], outer[nxt], inner[nxt]))
            mesh.faces.append((outer[index], inner[nxt], inner[index]))
        else:
            mesh.faces.append((outer[index], inner[nxt], outer[nxt]))
            mesh.faces.append((outer[index], inner[index], inner[nxt]))


def triangular_thread(phase: float) -> float:
    fraction = phase - math.floor(phase)
    return 1.0 - abs(2.0 * fraction - 1.0)


def male_outer_radius(theta: float, z: float) -> float:
    ridge = triangular_thread(z / THREAD_PITCH - theta / (2.0 * math.pi))
    top_fade = min(max((THREAD_ENGAGEMENT - z) / THREAD_LEAD_IN, 0.0), 1.0)
    return THREAD_BASE_RADIUS + THREAD_HEIGHT * ridge * top_fade


def female_inner_radius(theta: float, z: float) -> float:
    groove = triangular_thread(z / THREAD_PITCH - theta / (2.0 * math.pi))
    entrance = max(1.0 - z / THREAD_LEAD_IN, 0.0)
    return (
        THREAD_BASE_RADIUS
        + THREAD_RADIAL_CLEARANCE
        + THREAD_HEIGHT * groove
        + 0.35 * entrance
    )


def thread_tube_mesh(*, female: bool) -> TriangleMesh:
    mesh = TriangleMesh([], [])
    start_z = 0.0 if female else -0.3
    zs = np.linspace(start_z, THREAD_ENGAGEMENT, THREAD_Z_STEPS)
    angles = np.linspace(0.0, 2.0 * math.pi, THREAD_ANGLE_STEPS, endpoint=False)
    variable_rings: list[list[int]] = []
    fixed_rings: list[list[int]] = []

    for z in zs:
        if female:
            radii = np.asarray([female_inner_radius(float(theta), float(z)) for theta in angles])
            variable = np.column_stack((radii * np.cos(angles), radii * np.sin(angles)))
            fixed = np.column_stack(
                (THREAD_FEMALE_OUTER_RADIUS * np.cos(angles), THREAD_FEMALE_OUTER_RADIUS * np.sin(angles))
            )
        else:
            radii = np.asarray([male_outer_radius(float(theta), float(z)) for theta in angles])
            variable = np.column_stack((radii * np.cos(angles), radii * np.sin(angles)))
            fixed = np.column_stack(
                (THREAD_MALE_INNER_RADIUS * np.cos(angles), THREAD_MALE_INNER_RADIUS * np.sin(angles))
            )
        variable_rings.append(mesh.add_ring(variable, float(z)))
        fixed_rings.append(mesh.add_ring(fixed, float(z)))

    if female:
        for lower, upper in zip(fixed_rings, fixed_rings[1:]):
            add_ring_strip(mesh, lower, upper, inward=False)
        for lower, upper in zip(variable_rings, variable_rings[1:]):
            add_ring_strip(mesh, lower, upper, inward=True)
        add_annulus(mesh, fixed_rings[0], variable_rings[0], normal_up=False)
        add_annulus(mesh, fixed_rings[-1], variable_rings[-1], normal_up=True)
    else:
        for lower, upper in zip(variable_rings, variable_rings[1:]):
            add_ring_strip(mesh, lower, upper, inward=False)
        for lower, upper in zip(fixed_rings, fixed_rings[1:]):
            add_ring_strip(mesh, lower, upper, inward=True)
        add_annulus(mesh, variable_rings[0], fixed_rings[0], normal_up=False)
        add_annulus(mesh, variable_rings[-1], fixed_rings[-1], normal_up=True)
    return mesh


def mesh_to_manifold(mesh: TriangleMesh) -> m3d.Manifold:
    vertices = np.ascontiguousarray(mesh.vertices, dtype=np.float32)
    faces = np.ascontiguousarray(mesh.faces, dtype=np.uint32)
    solid = m3d.Manifold(m3d.Mesh(vertices, faces))
    if solid.is_empty():
        raise RuntimeError(f"Failed to create thread manifold: {solid.status()}")
    return solid


def annular_web(*, top: bool) -> m3d.Manifold:
    if top:
        z0 = THREAD_ENGAGEMENT - CONNECTOR_WEB_THICKNESS
        hole_radius = THREAD_FEMALE_OUTER_RADIUS - 0.5
    else:
        z0 = -0.9
        hole_radius = THREAD_MALE_INNER_RADIUS - 0.5
    outer = m3d.Manifold.cylinder(CONNECTOR_WEB_THICKNESS, 43.0, 43.0, THREAD_ANGLE_STEPS).translate((0.0, 0.0, z0))
    inner = m3d.Manifold.cylinder(CONNECTOR_WEB_THICKNESS + 0.4, hole_radius, hole_radius, THREAD_ANGLE_STEPS).translate(
        (0.0, 0.0, z0 - 0.2)
    )
    return batch_subtract(outer, [inner])


def build_parts() -> tuple[m3d.Manifold, m3d.Manifold]:
    outer = exact_sphere(OUTER_RADIUS)
    inner = exact_sphere(INNER_RADIUS)
    shell = batch_subtract(outer, [inner])
    top = shell.trim_by_plane((0.0, 0.0, 1.0), 0.0)
    bottom = shell.trim_by_plane((0.0, 0.0, -1.0), 0.0)

    top_cutters = [hole_cutter(hole) for hole in HOLES if hole.part == "top"]
    bottom_cutters = [hole_cutter(hole) for hole in HOLES if hole.part == "bottom"]
    top = batch_subtract(top, top_cutters)
    bottom = batch_subtract(bottom, bottom_cutters)

    top_thread = mesh_to_manifold(thread_tube_mesh(female=True))
    bottom_thread = mesh_to_manifold(thread_tube_mesh(female=False))
    top = batch_union([top, annular_web(top=True), top_thread])
    bottom = batch_union([bottom, annular_web(top=False), bottom_thread])
    return top, bottom


def manifold_mesh(solid: m3d.Manifold) -> tuple[np.ndarray, np.ndarray]:
    mesh = solid.to_mesh()
    vertices = np.asarray(mesh.vert_properties[:, :3], dtype=np.float64)
    faces = np.asarray(mesh.tri_verts, dtype=np.int64)
    return vertices, faces


def printable_bottom(vertices: np.ndarray, faces: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    transformed = vertices.copy()
    transformed[:, 2] = THREAD_ENGAGEMENT - transformed[:, 2]
    flipped = faces[:, [0, 2, 1]].copy()
    return transformed, flipped


def printable_lid(vertices: np.ndarray, faces: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return vertices.copy(), faces.copy()


def combine_meshes(meshes: list[tuple[np.ndarray, np.ndarray]]) -> tuple[np.ndarray, np.ndarray]:
    vertices: list[np.ndarray] = []
    faces: list[np.ndarray] = []
    offset = 0
    for mesh_vertices, mesh_faces in meshes:
        vertices.append(mesh_vertices)
        faces.append(mesh_faces + offset)
        offset += len(mesh_vertices)
    return np.vstack(vertices), np.vstack(faces)


def face_normal(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> tuple[float, float, float]:
    normal = np.cross(b - a, c - a)
    length = float(np.linalg.norm(normal))
    if length == 0.0:
        return (0.0, 0.0, 0.0)
    normal /= length
    return tuple(float(value) for value in normal)


def write_binary_stl(vertices: np.ndarray, faces: np.ndarray, path: str, name: str) -> None:
    header = name.encode("ascii", errors="ignore")[:80].ljust(80, b" ")
    with open(path, "wb") as handle:
        handle.write(header)
        handle.write(struct.pack("<I", len(faces)))
        for face in faces:
            a, b, c = vertices[face]
            handle.write(struct.pack("<3f", *face_normal(a, b, c)))
            handle.write(struct.pack("<3f", *a))
            handle.write(struct.pack("<3f", *b))
            handle.write(struct.pack("<3f", *c))
            handle.write(struct.pack("<H", 0))


def boundary_edge_count(faces: np.ndarray) -> int:
    edges: Counter[tuple[int, int]] = Counter()
    for a, b, c in faces:
        for edge in ((a, b), (b, c), (c, a)):
            edges[tuple(sorted((int(edge[0]), int(edge[1]))))] += 1
    return sum(count != 2 for count in edges.values())


def signed_volume(vertices: np.ndarray, faces: np.ndarray) -> float:
    triangles = vertices[faces]
    return float(np.einsum("ij,ij->i", triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])).sum() / 6.0)


def report(name: str, vertices: np.ndarray, faces: np.ndarray) -> None:
    minimum = vertices.min(axis=0)
    maximum = vertices.max(axis=0)
    size = maximum - minimum
    print(
        f"{name}: vertices={len(vertices)}, triangles={len(faces)}, "
        f"boundary_edges={boundary_edge_count(faces)}, "
        f"bounds={size[0]:.3f} x {size[1]:.3f} x {size[2]:.3f} mm, "
        f"volume={signed_volume(vertices, faces):.1f} mm^3"
    )


def validate_hole_spacing() -> float:
    minimum_gap = math.inf
    for index, first in enumerate(HOLES):
        first_direction = direction_from_angles(first.elevation_degrees, first.azimuth_degrees)
        first_half_angle = math.asin((first.diameter / 2.0) / OUTER_RADIUS)
        for second in HOLES[index + 1 :]:
            if first.part != second.part:
                continue
            second_direction = direction_from_angles(second.elevation_degrees, second.azimuth_degrees)
            second_half_angle = math.asin((second.diameter / 2.0) / OUTER_RADIUS)
            separation = math.acos(float(np.clip(np.dot(first_direction, second_direction), -1.0, 1.0)))
            minimum_gap = min(minimum_gap, OUTER_RADIUS * (separation - first_half_angle - second_half_angle))
    return minimum_gap


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    top_solid, bottom_solid = build_parts()
    top_assembled = manifold_mesh(top_solid)
    bottom_assembled = manifold_mesh(bottom_solid)
    lid_print = printable_lid(*top_assembled)
    bottom_print = printable_bottom(*bottom_assembled)
    assembly = combine_meshes([bottom_assembled, top_assembled])

    outputs = [
        ("perforated_sphere_lid", lid_print, "perforated_sphere_lid.stl"),
        ("perforated_sphere_bottom", bottom_print, "perforated_sphere_bottom.stl"),
        ("perforated_sphere_assembly_preview", assembly, "perforated_sphere_assembly_preview.stl"),
    ]
    for name, (vertices, faces), filename in outputs:
        path = os.path.join(OUTPUT_DIR, filename)
        write_binary_stl(vertices, faces, path, f"{name}_{MODEL_VERSION}")
        report(name, vertices, faces)
        print(f"wrote {path}")

    print(
        f"assembly target={OUTER_DIAMETER:.1f} mm diameter x {OUTER_DIAMETER:.1f} mm height; "
        f"wall={WALL_THICKNESS:.1f} mm; exterior=true sphere"
    )
    print(
        f"thread engagement={THREAD_ENGAGEMENT:.1f} mm ({THREAD_ENGAGEMENT / THREAD_PITCH:.2f} turns); "
        f"radial clearance={THREAD_RADIAL_CLEARANCE:.2f} mm"
    )
    print(f"minimum same-hemisphere hole edge gap={validate_hole_spacing():.2f} mm")


if __name__ == "__main__":
    main()

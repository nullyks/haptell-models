from __future__ import annotations

import math
import os
import struct
from collections import Counter
from dataclasses import dataclass

import numpy as np


# Units are millimetres.  The model is intended for a 0.4 mm nozzle and PLA.
MODEL_VERSION = "v01"
OUTER_SIZE = 91.0
OUTER_RADIUS = 15.0
SHELL_WALL = 2.8
# Thin planar end faces improve heat transfer from a Peltier element.  At a
# 0.4 mm extrusion width this remains three nominal lines thick.
END_WALL = 1.2
SEAM_Z = 0.0

# The hidden circular screw joint is used because a rounded-square thread cannot
# rotate inside a matching rounded-square socket.  These dimensions give six
# nominal 0.4 mm extrusion widths at the thinnest load-bearing sections.
THREAD_BASE_RADIUS = 37.0
THREAD_HEIGHT = 0.70
THREAD_PITCH = 3.2
THREAD_ENGAGEMENT = 4.2
THREAD_RADIAL_CLEARANCE = 0.35
MALE_INNER_RADIUS = 34.6
FEMALE_OUTER_RADIUS = 40.5
THREAD_LEAD_IN = 0.8
CONNECTOR_WEB_THICKNESS = 0.8

CORNER_STEPS = 20
VERTICAL_CURVE_STEPS = 28
THREAD_ANGLE_STEPS = 240
THREAD_Z_STEPS = 52
OUTPUT_DIR = os.path.join("output", "rounded_cube_box")


@dataclass
class Mesh:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int]]

    def add_vertex(self, point: tuple[float, float, float]) -> int:
        self.vertices.append(tuple(float(value) for value in point))
        return len(self.vertices) - 1

    def add_ring(self, points: np.ndarray, z: float) -> list[int]:
        return [self.add_vertex((x, y, z)) for x, y in points]


def rounded_square_ring(core_half: float, radius: float) -> np.ndarray:
    """Return a counter-clockwise rounded-square perimeter."""
    radius = max(radius, 0.04)  # avoids degenerate corner faces at the flat poles
    corners = [
        ((core_half, -core_half), -90.0, 0.0),
        ((core_half, core_half), 0.0, 90.0),
        ((-core_half, core_half), 90.0, 180.0),
        ((-core_half, -core_half), 180.0, 270.0),
    ]
    points: list[tuple[float, float]] = []
    for (cx, cy), start, end in corners:
        for angle in np.linspace(start, end, CORNER_STEPS, endpoint=True):
            radians = math.radians(float(angle))
            points.append((cx + radius * math.cos(radians), cy + radius * math.sin(radians)))
    return np.asarray(points, dtype=np.float64)


def circle_ring(radius: float, count: int, *, angles: np.ndarray | None = None) -> np.ndarray:
    if angles is None:
        angles = np.linspace(0.0, 2.0 * math.pi, count, endpoint=False)
    return np.column_stack((radius * np.cos(angles), radius * np.sin(angles)))


def matching_circle_ring(square_ring: np.ndarray, radius: float) -> np.ndarray:
    angles = np.arctan2(square_ring[:, 1], square_ring[:, 0])
    return circle_ring(radius, len(square_ring), angles=angles)


def spherocube_radius(z: float, *, wall_offset: float = 0.0) -> float:
    """Cross-section corner radius for a cube Minkowski-rounded by a sphere."""
    radius = OUTER_RADIUS - wall_offset
    core_half = OUTER_SIZE / 2.0 - OUTER_RADIUS
    distance_past_core = max(abs(z) - core_half, 0.0)
    if distance_past_core >= radius:
        return 0.04
    return math.sqrt(max(radius * radius - distance_past_core * distance_past_core, 0.0))


def inner_spherocube_radius(z: float) -> float:
    """Inner contour with thick side walls and thinner horizontal end faces."""
    horizontal_radius = OUTER_RADIUS - SHELL_WALL
    vertical_radius = OUTER_RADIUS - END_WALL
    core_half = OUTER_SIZE / 2.0 - OUTER_RADIUS
    distance_past_core = max(abs(z) - core_half, 0.0)
    if distance_past_core >= vertical_radius:
        return 0.04
    vertical_fraction = distance_past_core / vertical_radius
    return horizontal_radius * math.sqrt(max(1.0 - vertical_fraction * vertical_fraction, 0.0))


def outer_profile(z0: float, z1: float) -> list[tuple[float, float]]:
    core_half = OUTER_SIZE / 2.0 - OUTER_RADIUS
    values: list[float] = [z0, z1]
    for transition in (-core_half, core_half):
        lo = max(z0, transition - OUTER_RADIUS)
        hi = min(z1, transition + OUTER_RADIUS)
        if lo < hi:
            values.extend(float(z) for z in np.linspace(lo, hi, VERTICAL_CURVE_STEPS))
    values.extend(z for z in (-core_half, core_half) if z0 <= z <= z1)
    zs = sorted(set(round(value, 8) for value in values))
    return [(z, spherocube_radius(z)) for z in zs]


def inner_profile(z0: float, z1: float) -> list[tuple[float, float]]:
    inner_vertical_radius = OUTER_RADIUS - END_WALL
    core_half = OUTER_SIZE / 2.0 - OUTER_RADIUS
    inner_min = -core_half - inner_vertical_radius
    inner_max = core_half + inner_vertical_radius
    start = max(z0, inner_min)
    end = min(z1, inner_max)
    values: list[float] = [start, end]
    for transition in (-core_half, core_half):
        lo = max(start, transition - inner_vertical_radius)
        hi = min(end, transition + inner_vertical_radius)
        if lo < hi:
            values.extend(float(z) for z in np.linspace(lo, hi, VERTICAL_CURVE_STEPS))
    values.extend(z for z in (-core_half, core_half) if start <= z <= end)
    zs = sorted(set(round(value, 8) for value in values))
    return [(z, inner_spherocube_radius(z)) for z in zs]


def add_ring_strip(mesh: Mesh, lower: list[int], upper: list[int], *, inward: bool = False) -> None:
    if len(lower) != len(upper):
        raise ValueError("Ring sizes must match")
    for i in range(len(lower)):
        j = (i + 1) % len(lower)
        if inward:
            mesh.faces.append((lower[i], upper[j], lower[j]))
            mesh.faces.append((lower[i], upper[i], upper[j]))
        else:
            mesh.faces.append((lower[i], lower[j], upper[j]))
            mesh.faces.append((lower[i], upper[j], upper[i]))


def add_annulus(
    mesh: Mesh,
    outer: list[int],
    inner: list[int],
    *,
    normal_up: bool,
) -> None:
    if len(outer) != len(inner):
        raise ValueError("Ring sizes must match")
    for i in range(len(outer)):
        j = (i + 1) % len(outer)
        if normal_up:
            mesh.faces.append((outer[i], outer[j], inner[j]))
            mesh.faces.append((outer[i], inner[j], inner[i]))
        else:
            mesh.faces.append((outer[i], inner[j], outer[j]))
            mesh.faces.append((outer[i], inner[i], inner[j]))


def add_cap(mesh: Mesh, ring: list[int], *, normal_up: bool) -> None:
    points = np.asarray([mesh.vertices[index] for index in ring])
    center = mesh.add_vertex(tuple(points.mean(axis=0)))
    for i in range(len(ring)):
        j = (i + 1) % len(ring)
        if normal_up:
            mesh.faces.append((center, ring[i], ring[j]))
        else:
            mesh.faces.append((center, ring[j], ring[i]))


def build_shell(*, top: bool) -> Mesh:
    mesh = Mesh([], [])
    core_half = OUTER_SIZE / 2.0 - OUTER_RADIUS
    outer_z0, outer_z1 = ((SEAM_Z, OUTER_SIZE / 2.0) if top else (-OUTER_SIZE / 2.0, SEAM_Z))
    outer_rings: list[list[int]] = []
    for z, radius in outer_profile(outer_z0, outer_z1):
        outer_rings.append(mesh.add_ring(rounded_square_ring(core_half, radius), z))
    for lower, upper in zip(outer_rings, outer_rings[1:]):
        add_ring_strip(mesh, lower, upper)

    inner_rings: list[list[int]] = []
    for z, radius in inner_profile(outer_z0, outer_z1):
        inner_rings.append(mesh.add_ring(rounded_square_ring(core_half, radius), z))
    for lower, upper in zip(inner_rings, inner_rings[1:]):
        add_ring_strip(mesh, lower, upper, inward=True)

    if top:
        add_cap(mesh, outer_rings[-1], normal_up=True)
        add_cap(mesh, inner_rings[-1], normal_up=False)
        add_annulus(mesh, outer_rings[0], inner_rings[0], normal_up=False)
    else:
        add_cap(mesh, outer_rings[0], normal_up=False)
        add_cap(mesh, inner_rings[0], normal_up=True)
        add_annulus(mesh, outer_rings[-1], inner_rings[-1], normal_up=True)
    return mesh


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


def build_thread_tube(*, female: bool) -> Mesh:
    mesh = Mesh([], [])
    # The male tube overlaps its connector web below the seam.  Keeping its
    # closed end away from the shell's exact seam edge avoids a non-manifold
    # four-face edge while preserving the complete thread above z=0.
    start_z = 0.0 if female else -0.3
    zs = np.linspace(start_z, THREAD_ENGAGEMENT, THREAD_Z_STEPS)
    angles = np.linspace(0.0, 2.0 * math.pi, THREAD_ANGLE_STEPS, endpoint=False)
    variable_rings: list[list[int]] = []
    fixed_rings: list[list[int]] = []

    for z in zs:
        if female:
            variable = np.asarray(
                [
                    (female_inner_radius(float(theta), float(z)) * math.cos(theta),
                     female_inner_radius(float(theta), float(z)) * math.sin(theta))
                    for theta in angles
                ]
            )
            fixed = circle_ring(FEMALE_OUTER_RADIUS, THREAD_ANGLE_STEPS, angles=angles)
        else:
            variable = np.asarray(
                [
                    (male_outer_radius(float(theta), float(z)) * math.cos(theta),
                     male_outer_radius(float(theta), float(z)) * math.sin(theta))
                    for theta in angles
                ]
            )
            fixed = circle_ring(MALE_INNER_RADIUS, THREAD_ANGLE_STEPS, angles=angles)
        variable_rings.append(mesh.add_ring(variable, float(z)))
        fixed_rings.append(mesh.add_ring(fixed, float(z)))

    if female:
        for lower, upper in zip(fixed_rings, fixed_rings[1:]):
            add_ring_strip(mesh, lower, upper)
        for lower, upper in zip(variable_rings, variable_rings[1:]):
            add_ring_strip(mesh, lower, upper, inward=True)
        add_annulus(mesh, fixed_rings[0], variable_rings[0], normal_up=False)
        add_annulus(mesh, fixed_rings[-1], variable_rings[-1], normal_up=True)
    else:
        for lower, upper in zip(variable_rings, variable_rings[1:]):
            add_ring_strip(mesh, lower, upper)
        for lower, upper in zip(fixed_rings, fixed_rings[1:]):
            add_ring_strip(mesh, lower, upper, inward=True)
        add_annulus(mesh, variable_rings[0], fixed_rings[0], normal_up=False)
        add_annulus(mesh, variable_rings[-1], fixed_rings[-1], normal_up=True)
    return mesh


def build_connector_web(*, top: bool) -> Mesh:
    """Join the circular thread tube to the rounded-square shell."""
    mesh = Mesh([], [])
    core_half = OUTER_SIZE / 2.0 - OUTER_RADIUS
    if top:
        z0 = THREAD_ENGAGEMENT - CONNECTOR_WEB_THICKNESS
        z1 = THREAD_ENGAGEMENT
        hole_radius = FEMALE_OUTER_RADIUS - 0.5
    else:
        z1 = -0.1
        z0 = z1 - CONNECTOR_WEB_THICKNESS
        # Radial overlap avoids a coincident four-face edge where the web meets
        # the closed thread tube; slicers can then union the two watertight
        # volumes without producing a non-manifold seam.
        hole_radius = MALE_INNER_RADIUS - 0.5

    square0 = rounded_square_ring(core_half, spherocube_radius(z0, wall_offset=SHELL_WALL))
    square1 = rounded_square_ring(core_half, spherocube_radius(z1, wall_offset=SHELL_WALL))
    circle0 = matching_circle_ring(square0, hole_radius)
    circle1 = matching_circle_ring(square1, hole_radius)
    outer0 = mesh.add_ring(square0, z0)
    outer1 = mesh.add_ring(square1, z1)
    inner0 = mesh.add_ring(circle0, z0)
    inner1 = mesh.add_ring(circle1, z1)

    add_annulus(mesh, outer0, inner0, normal_up=False)
    add_annulus(mesh, outer1, inner1, normal_up=True)
    add_ring_strip(mesh, outer0, outer1)
    add_ring_strip(mesh, inner0, inner1, inward=True)
    return mesh


def combine_meshes(meshes: list[Mesh]) -> Mesh:
    combined = Mesh([], [])
    vertex_offset = 0
    for mesh in meshes:
        combined.vertices.extend(mesh.vertices)
        combined.faces.extend(
            (a + vertex_offset, b + vertex_offset, c + vertex_offset)
            for a, b, c in mesh.faces
        )
        vertex_offset += len(mesh.vertices)
    return combined


def translate_mesh(mesh: Mesh, delta: tuple[float, float, float]) -> Mesh:
    dx, dy, dz = delta
    return Mesh(
        [(x + dx, y + dy, z + dz) for x, y, z in mesh.vertices],
        mesh.faces.copy(),
    )


def flip_for_printing(mesh: Mesh) -> Mesh:
    """Place the lid's exterior top face on the print bed."""
    half = OUTER_SIZE / 2.0
    return Mesh(
        [(x, y, half - z) for x, y, z in mesh.vertices],
        [(a, c, b) for a, b, c in mesh.faces],
    )


def face_normal(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> tuple[float, float, float]:
    normal = np.cross(b - a, c - a)
    length = float(np.linalg.norm(normal))
    if length == 0.0:
        return (0.0, 0.0, 0.0)
    normal /= length
    return tuple(float(value) for value in normal)


def write_binary_stl(mesh: Mesh, path: str, name: str) -> None:
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    header = name.encode("ascii", errors="ignore")[:80].ljust(80, b" ")
    with open(path, "wb") as handle:
        handle.write(header)
        handle.write(struct.pack("<I", len(mesh.faces)))
        for face in mesh.faces:
            a, b, c = vertices[list(face)]
            handle.write(struct.pack("<3f", *face_normal(a, b, c)))
            handle.write(struct.pack("<3f", *a))
            handle.write(struct.pack("<3f", *b))
            handle.write(struct.pack("<3f", *c))
            handle.write(struct.pack("<H", 0))


def mesh_bounds(mesh: Mesh) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    vertices = np.asarray(mesh.vertices)
    minimum = vertices.min(axis=0)
    maximum = vertices.max(axis=0)
    return minimum, maximum, maximum - minimum


def boundary_edge_count(mesh: Mesh) -> int:
    edges: Counter[tuple[int, int]] = Counter()
    for a, b, c in mesh.faces:
        for edge in ((a, b), (b, c), (c, a)):
            edges[tuple(sorted(edge))] += 1
    return sum(count != 2 for count in edges.values())


def signed_volume(mesh: Mesh) -> float:
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    volume = 0.0
    for a, b, c in mesh.faces:
        volume += float(np.dot(vertices[a], np.cross(vertices[b], vertices[c]))) / 6.0
    return volume


def report(name: str, mesh: Mesh) -> None:
    minimum, maximum, size = mesh_bounds(mesh)
    print(
        f"{name}: vertices={len(mesh.vertices)}, triangles={len(mesh.faces)}, "
        f"boundary_edges={boundary_edge_count(mesh)}, "
        f"bounds={size[0]:.3f} x {size[1]:.3f} x {size[2]:.3f} mm, "
        f"min=({minimum[0]:.3f}, {minimum[1]:.3f}, {minimum[2]:.3f}), "
        f"max=({maximum[0]:.3f}, {maximum[1]:.3f}, {maximum[2]:.3f}), "
        f"signed_volume={signed_volume(mesh):.1f} mm^3"
    )


def validate_thread_clearance() -> tuple[float, float]:
    clearances = []
    for z in np.linspace(0.0, THREAD_ENGAGEMENT, 41):
        for theta in np.linspace(0.0, 2.0 * math.pi, 181, endpoint=False):
            clearances.append(female_inner_radius(float(theta), float(z)) - male_outer_radius(float(theta), float(z)))
    return min(clearances), max(clearances)


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    bottom_assembled = combine_meshes(
        [build_shell(top=False), build_connector_web(top=False), build_thread_tube(female=False)]
    )
    lid_assembled = combine_meshes(
        [build_shell(top=True), build_connector_web(top=True), build_thread_tube(female=True)]
    )

    bottom_print = translate_mesh(bottom_assembled, (0.0, 0.0, OUTER_SIZE / 2.0))
    lid_print = flip_for_printing(lid_assembled)
    assembly = combine_meshes([bottom_assembled, lid_assembled])

    outputs = [
        ("rounded_cube_bottom", bottom_print, "rounded_cube_bottom.stl"),
        ("rounded_cube_lid", lid_print, "rounded_cube_lid.stl"),
        ("rounded_cube_assembly_preview", assembly, "rounded_cube_assembly_preview.stl"),
    ]
    for name, mesh, filename in outputs:
        path = os.path.join(OUTPUT_DIR, filename)
        write_binary_stl(mesh, path, f"{name}_{MODEL_VERSION}")
        report(name, mesh)
        print(f"wrote {path}")

    minimum_clearance, maximum_clearance = validate_thread_clearance()
    print(
        f"thread radial clearance: min={minimum_clearance:.3f} mm, "
        f"max={maximum_clearance:.3f} mm"
    )
    print(
        f"assembly target: {OUTER_SIZE:.1f} x {OUTER_SIZE:.1f} x {OUTER_SIZE:.1f} mm; "
        f"side wall={SHELL_WALL:.1f} mm; top/bottom wall={END_WALL:.1f} mm; "
        f"corner radius={OUTER_RADIUS:.1f} mm"
    )


if __name__ == "__main__":
    main()

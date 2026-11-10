"""Read-only checks of pneumatic-cube 3MF geometry and actual G-code supports."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from scipy.spatial import cKDTree
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import generate_pneumatic_cube_stl as cube

NUMBER = re.compile(r"([XYZEFIJK])([-+]?(?:\d+(?:\.\d*)?|\.\d+))")


def extrusion_paths(path):
    position = np.zeros(3)
    feature, relative, extruder = "Custom", True, 0.0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(";TYPE:"):
            feature = line[6:].strip()
        command = line.split(";", 1)[0].strip()
        if command == "M83": relative = True
        if command == "M82": relative = False
        if not command.startswith(("G0 ", "G1 ", "G2 ", "G3 ", "G92 ")): continue
        values = {k: float(v) for k, v in NUMBER.findall(command)}
        if command.startswith("G92 "):
            extruder = values.get("E", extruder)
            continue
        target = np.array([values.get(key, position[i]) for i, key in enumerate("XYZ")])
        de = values.get("E", 0) if relative else values.get("E", extruder) - extruder
        if "E" in values: extruder = extruder + de if relative else values["E"]
        length = np.linalg.norm(target[:2] - position[:2])
        if de > 0 and (length > 1e-6 or command.startswith(("G2 ", "G3 "))):
            points = None
            if command.startswith(("G2 ", "G3 ")) and ("I" in values or "J" in values):
                center = position[:2] + [values.get("I", 0), values.get("J", 0)]
                radius = np.linalg.norm(position[:2] - center)
                a = math.atan2(position[1] - center[1], position[0] - center[0])
                b = math.atan2(target[1] - center[1], target[0] - center[0])
                angle = (b - a) % (2 * math.pi) if command.startswith("G3 ") else -((a - b) % (2 * math.pi))
                if abs(angle) < 1e-9: angle = 2 * math.pi
                length = radius * abs(angle)
                ts = np.linspace(0, 1, max(2, math.ceil(length / .4) + 1))
                points = np.column_stack((center[0] + radius * np.cos(a + ts * angle), center[1] + radius * np.sin(a + ts * angle),
                                          position[2] + ts * (target[2] - position[2])))
            if points is None:
                points = np.linspace(position, target, max(2, math.ceil(length / .4) + 1))
            points[:, :2] -= 180
            yield feature, points, de, float(length)
        position = target


def rounded_distance(points, radius):
    q = np.abs(points) - (cube.OUTER_SIZE / 2 - cube.OUTER_RADIUS)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(np.max(q, axis=1), 0) - radius


def analytic_material(points):
    material = (rounded_distance(points, cube.OUTER_RADIUS) <= 0) & (rounded_distance(points, cube.OUTER_RADIUS - cube.WALL_THICKNESS) >= 0)
    r, blend = cube.HOLE_DIAMETER / 2, cube.HOLE_EDGE_RADIUS
    outside, inside = cube.OUTER_SIZE / 2, cube.OUTER_SIZE / 2 - cube.WALL_THICKNESS
    for _, u, v, n in cube.FACE_FRAMES:
        s = points @ n
        radius = np.full(len(points), r)
        lo, hi = s < inside + blend, s > outside - blend
        radius[lo] = r + blend - np.sqrt(np.maximum(0, blend ** 2 - (s[lo] - inside - blend) ** 2))
        radius[hi] = r + blend - np.sqrt(np.maximum(0, blend ** 2 - (s[hi] - outside + blend) ** 2))
        uv = np.column_stack((points @ u, points @ v))
        for center in cube.HOLE_CENTERS:
            cut = (s >= inside - .001) & (s <= outside + .001) & (np.linalg.norm(uv - center, axis=1) < radius)
            material &= ~cut
    return material


def inspect(directory):
    directory = Path(directory)
    review = json.loads((directory / "print_review.json").read_text())
    matrix = np.array(review["transform_3x4"])
    to_model = lambda p: (p - matrix[:, 3]) @ matrix[:, :3]
    feature_mass = defaultdict(float)
    supports, interfaces, bridges = [], [], []
    for feature, points, extrusion, length in extrusion_paths(directory / "pneumatic_cube_xl_pla.gcode"):
        feature_mass[feature] += extrusion * math.pi * (1.75 / 2) ** 2 * 1.24 / 1000
        if feature.startswith("Support material"):
            supports.append(points)
            if feature == "Support material interface": interfaces.append(points)
        elif feature == "Bridge infill": bridges.append((points, length))
    support = np.concatenate(supports) if supports else np.empty((0, 3))
    interface = np.concatenate(interfaces) if interfaces else np.empty((0, 3))
    cavity_points = rounded_distance(to_model(support), cube.OUTER_RADIUS - cube.WALL_THICKNESS) < -.05 if len(support) else np.empty(0)
    maximum, worst, cache = 0.0, None, {}
    # Nominal material below a path estimates the previous layer's footprint.
    # Sampled support interfaces are additional anchors. Physical bridge quality
    # is deliberately not inferred from a maximum span alone.
    for points, length in bridges:
        key = round(points[0, 2], 4)
        if key not in cache:
            nearby = interface[(interface[:, 2] >= key - .85) & (interface[:, 2] < key - .08)]
            cache[key] = cKDTree(nearby[:, :2]) if len(nearby) else None
        lower = points.copy()
        lower[:, 2] -= .225
        anchored = analytic_material(to_model(lower))
        if cache[key] is not None:
            anchored |= cache[key].query(points[:, :2])[0] <= .6
        run, longest = 0, 0
        for yes in anchored:
            run = 0 if yes else run + 1
            longest = max(longest, run)
        span = min(length, longest * length / (len(points) - 1))
        if span > maximum:
            maximum, worst = span, {"z": key, "start": points[0].round(3).tolist(), "end": points[-1].round(3).tolist()}
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    with zipfile.ZipFile(directory / "pneumatic_cube_xl_pla.3mf") as archive:
        model, config = ET.fromstring(archive.read("3D/3dmodel.model")), ET.fromstring(archive.read("Metadata/Slic3r_PE_model.config"))
        positions = np.array([[float(p.get(k)) for k in ("x", "y", "z")] for p in model.findall("m:resources/m:object/m:mesh/m:vertices/m:vertex", ns)])
        placement = np.array([float(v) for v in model.find("m:build/m:item", ns).get("transform").split()])
        first = config.find("object/volume")
        triangles = model.findall("m:resources/m:object/m:mesh/m:triangles/m:triangle", ns)[:int(first.get("lastid")) + 1]
        used = np.unique([[int(f.get(k)) for k in ("v1", "v2", "v3")] for f in triangles])
        actual = positions[used] + placement[-3:] - [180, 180, 0]
        expected = trimesh.load_mesh(directory / "pneumatic_cube_print.stl", process=False)
        error = max(cKDTree(expected.vertices).query(actual)[0].max(), cKDTree(actual).query(expected.vertices)[0].max())
        assert error < .0001
        model_count = sum(v.find("metadata[@key='volume_type']").get("value") == "ModelPart" for v in config.findall("object/volume"))
        assert model_count == 1
    assert abs(sum(feature_mass.values()) - float(review["statistics"]["filament used [g]"])) < .2
    result = {"orientation": review["orientation"], "support_mode": review["support_mode"],
        "feature_mass_g": {k: round(v, 3) for k, v in feature_mass.items()},
        "support_mass_g": round(sum(v for k, v in feature_mass.items() if k.startswith("Support material")), 3),
        "support_samples_inside_cavity": int(np.count_nonzero(cavity_points)),
        "support_z_max_mm": round(float(support[:, 2].max()), 3) if len(support) else 0,
        "bridge_paths": len(bridges), "max_sampled_free_bridge_mm": round(maximum, 3), "worst_bridge": worst,
        "one_printable_model": True, "project_mesh_max_vertex_error_mm": float(error),
        "statistics": review["statistics"],
        "scope": "Analytic geometry and sampled actual G-code. Not a physical bridge, surface, membrane, pressure or support-removal test."}
    (directory / "toolpath_checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    inspect(parser.parse_args().directory)

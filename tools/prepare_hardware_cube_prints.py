"""Prepare and slice Prusa XL projects for the new hardware cube families."""

from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from scipy.spatial import cKDTree
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from generate_hardware_cubes_stl import thermal_lra_frames
from generate_rounded_cube_box_stl import LIP_HEIGHT, box
from tools.check_pneumatic_print import extrusion_paths
from tools.prepare_cube_prints import NS, add_enforcer, profile_values
from tools.slice_models import find_slicer

FAMILIES = ("servo_motor_cube", "voice_coil_cube", "thermal_cube")
PROFILE = ROOT / "output/rounded_cube_box/prusa_xl_04_pla.ini"


def regions(family, part):
    if part == "clamp":
        return
    shift = LIP_HEIGHT if part == "bottom" else 0
    underside = 37.5 if family == "servo_motor_cube" else 39.3
    for y in (-20, -7, 7, 20):
        yield "Interior roof strip", box((68, 2, 4), (0, y, shift + underside - .3))
    if family == "thermal_cube":
        for y in (-17, -5, 5):
            y = -y if part == "bottom" else y
            yield "Peltier runway and rails", box((29, 2.2, 7), (0, y, shift + 39))
        if part == "bottom":
            for wall, frame in thermal_lra_frames().items():
                # The base print transform flips Y and Z. Support the leading
                # arcs near the seam while leaving access through the open base.
                inward = frame[:, 2]
                dims = (7, 16, 5) if inward[0] else (16, 7, 5)
                center = (-36 * inward[0], 36 * inward[1], shift - frame[2, 3] - 5.5)
                yield f"{wall} LRA holder arcs", box(dims, center)
    if part == "bottom":
        rim = box((87, 87, 2), (0, 0, shift)) - box((74, 74, 3), (0, 0, shift))
        yield "Mating rim underside", rim
        if family == "servo_motor_cube":
            yield "Main servo screw bar", box((69, 13, 2), (0, 15.25, 15.3))
            yield "Secondary servo screw bar", box((39, 12, 2), (0, -34.25, 15.3))
        if family == "voice_coil_cube":
            yield "Cradle and clamp ears", box((35, 29, 2.5), (22, 0, 26.3))


def verify_project_mesh(stl, model, config):
    vertices = np.array([[float(node.get(k)) for k in "xyz"] for node in model.findall(".//m:vertex", NS)])
    triangles = model.findall(".//m:triangle", NS)[:int(config.find("object/volume").get("lastid")) + 1]
    ids = np.unique([[int(face.get(k)) for k in ("v1", "v2", "v3")] for face in triangles])
    source = trimesh.load_mesh(stl, process=False)
    error = max(cKDTree(source.vertices).query(vertices[ids])[0].max(),
                cKDTree(vertices[ids]).query(source.vertices)[0].max())
    if error > 0.0001 or len(triangles) != len(source.faces):
        raise ValueError(f"{stl.name} does not match the 3MF model")
    return float(error)


def inspect_toolpath(gcode, part):
    layers, support_layers, bridges = defaultdict(list), defaultdict(list), defaultdict(list)
    support_grams = 0.0
    for feature, points, extrusion, length in extrusion_paths(gcode):
        if feature in ("Custom", "Skirt/Brim"):
            continue
        z = round(float(points[-1, 2]), 4)
        if feature.startswith("Support material"):
            support_layers[z].append(points)
            support_grams += extrusion * math.pi * .875**2 * 1.24 / 1000
        else:
            layers[z].append(points)
        if feature in ("Bridge infill", "Internal bridge infill"):
            bridges[z].append((points, length))
    rim = LIP_HEIGHT if part == "bottom" else 0
    support = np.concatenate([p for layer in support_layers.values() for p in layer]) if support_layers else np.zeros((0, 3))
    rounded_distance = np.linalg.norm(np.maximum(abs(support - (0, 0, rim)) - 27.5, 0), axis=1)
    outside = (rounded_distance > 14.8) & (support[:, 2] >= rim + 1)
    longest, worst = 0.0, None
    for z, paths in bridges.items():
        anchors = [p for h, layer in layers.items() if z - .32 <= h < z - .08 for p in layer]
        anchors += [p for h, layer in support_layers.items() if z - .65 <= h < z - .08 for p in layer]
        prior = cKDTree(np.concatenate(anchors)[:, :2]) if anchors else None
        for points, length in paths:
            backed = prior.query(points[:, :2])[0] <= .65 if prior is not None else np.zeros(len(points), bool)
            runs = np.diff(np.flatnonzero(np.r_[True, backed, True])) - 1
            span = min(length, max(runs) * length / (len(points) - 1))
            if span > longest:
                longest = span
                worst = [points[0].round(2).tolist(), points[-1].round(2).tolist()]
    return {
        "estimated_support_g": round(support_grams, 2),
        "exterior_support_samples_above_seam": int(np.count_nonzero(outside)),
        "max_sampled_free_bridge_mm": round(longest, 2),
        "longest_bridge_path_mm": worst,
    }


def prepare_part(family, part, destination, slicer):
    name = f"{family}_{part}"
    stl = ROOT / "output" / family / f"{name}.stl"
    project = destination / f"{name}_xl_pla.3mf"
    gcode = destination / f"{name}_xl_pla.gcode"
    args = [str(slicer), "--center", "180,180", "--export-3mf", "--output", str(project), str(stl)]
    subprocess.run(args, check=True, capture_output=True)
    with zipfile.ZipFile(project) as archive:
        files = {path: archive.read(path) for path in archive.namelist()}
    model = ET.fromstring(files["3D/3dmodel.model"])
    model.set("xmlns:slic3rpe", "http://schemas.slic3r.org/3mf/2017/06")
    cfg = ET.fromstring(files["Metadata/Slic3r_PE_model.config"])
    mesh_error = verify_project_mesh(stl, model, cfg)
    enforcers = list(regions(family, part))
    for label, region in enforcers:
        add_enforcer(model, cfg, region, label)
    files["3D/3dmodel.model"] = ET.tostring(model, encoding="utf-8", xml_declaration=True)
    files["Metadata/Slic3r_PE_model.config"] = ET.tostring(cfg, encoding="utf-8", xml_declaration=True)
    layers = "13" if family == "servo_motor_cube" else "8"
    values = profile_values(PROFILE)
    values.update(support_material_style="snug", support_material_auto="0",
                  support_material_buildplate_only="0", support_material=str(int(bool(enforcers))),
                  top_solid_layers=layers, bottom_solid_layers=layers)
    files["Metadata/Slic3r_PE.config"] = ("; generated by PrusaSlicer 2.9.7\n"
        + "\n".join(f"; {name} = {value}" for name, value in sorted(values.items())) + "\n").encode()
    with zipfile.ZipFile(project, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, data in files.items():
            archive.writestr(path, data)
    completed = subprocess.run([str(slicer), "--export-gcode", "--output", str(gcode), str(project)],
                               capture_output=True, text=True, errors="replace")
    (destination / f"{name}.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    completed.check_returncode()
    footer = dict(line[2:].split(" = ", 1) for line in gcode.read_text(encoding="utf-8").splitlines()
                  if line.startswith("; ") and " = " in line)
    for key in ("printer_model", "layer_height", "support_material", "support_material_auto", "support_material_style"):
        if footer.get(key) != values[key]:
            raise ValueError(f"{name} embedded setting mismatch for {key}")
    result = inspect_toolpath(gcode, part)
    result.update(statistics={k: v for k, v in footer.items() if k.startswith(("filament used", "estimated printing time"))},
                  manual_enforcers=len(enforcers), mesh_vertex_error_mm=mesh_error,
                  stl_sha256=hashlib.sha256(stl.read_bytes()).hexdigest(),
                  project_sha256=hashlib.sha256(project.read_bytes()).hexdigest())
    print(name, result["estimated_support_g"], result["max_sampled_free_bridge_mm"], flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    slicer = find_slicer()
    jobs = [(family, part) for family in FAMILIES for part in ("lid", "bottom")]
    jobs.append(("voice_coil_cube", "clamp"))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda job: prepare_part(*job, destination, slicer), jobs))
    for family in FAMILIES:
        report = {"printer": "Prusa XL IS, 0.4 mm, Generic PLA", "layer_height_mm": .2,
                  "scope": "Offline slicing and sampled toolpaths. Physical fit and finish require a print.",
                  "parts": {part: result for (name, part), result in zip(jobs, results) if name == family}}
        (destination / f"{family}_print_review.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

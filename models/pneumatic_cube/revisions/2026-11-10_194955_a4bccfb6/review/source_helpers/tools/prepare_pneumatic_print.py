"""Create a fresh pneumatic-cube print project with embedded XL/PLA settings."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import generate_pneumatic_cube_stl as cube
from tools.slice_models import find_slicer

CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
NS = {"m": CORE}
ET.register_namespace("", CORE)


def profile_values(path):
    return dict(line.split(" = ", 1) for line in path.read_text(encoding="utf-8").splitlines()
                if " = " in line and not line.startswith("#"))


def append_modifier(model, config, solid, name, kind):
    obj = model.find("m:resources/m:object", NS)
    vertices = obj.find("m:mesh/m:vertices", NS)
    faces = obj.find("m:mesh/m:triangles", NS)
    start_vertex, start_face = len(vertices), len(faces)
    placement = [float(v) for v in model.find("m:build/m:item", NS).get("transform").split()]
    if placement[:9] != [1, 0, 0, 0, 1, 0, 0, 0, 1]:
        raise ValueError("Expected identity rotation for the already-oriented STL")
    positions, triangles = cube.mesh_arrays(solid)
    for x, y, z in positions:
        ET.SubElement(vertices, f"{{{CORE}}}vertex", {"x": str(x), "y": str(y), "z": str(z - placement[-1])})
    for a, b, c in triangles:
        ET.SubElement(faces, f"{{{CORE}}}triangle", {"v1": str(a + start_vertex), "v2": str(b + start_vertex), "v3": str(c + start_vertex)})
    volume = ET.SubElement(config.find("object"), "volume", {"firstid": str(start_face), "lastid": str(len(faces) - 1)})
    for key, value in (("name", name), ("volume_type", kind), ("matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1")):
        ET.SubElement(volume, "metadata", {"type": "volume", "key": key, "value": value})


def prepare(destination, orientation="edge", support="external", slicer=None):
    destination = Path(destination).resolve()
    if (ROOT / "models").resolve() in destination.parents or (ROOT / "output").resolve() in destination.parents:
        raise ValueError("Generate in a fresh review directory outside output/ and models/")
    destination.mkdir(parents=True, exist_ok=False)
    slicer = slicer or find_slicer()
    source = ROOT / "output/pneumatic_cube/pneumatic_cube.stl"
    mesh = trimesh.load_mesh(source, process=False)
    if orientation == "face":
        rotation = np.eye(3)
    elif orientation == "edge":
        rotation = np.array([[1, 0, 0], [0, 1, -1], [0, 1, 1]]) / np.sqrt([[1], [2], [2]])
    elif orientation == "corner":
        rotation = np.array([[1, -1, 0], [1, 1, -2], [1, 1, 1]]) / np.sqrt([[2], [6], [3]])
    else:
        raise ValueError(orientation)
    transform = np.column_stack((rotation, np.zeros(3)))
    transform[2, 3] = -float((mesh.vertices @ rotation.T)[:, 2].min())
    mesh.apply_transform(np.vstack((transform, [0, 0, 0, 1])))
    oriented = destination / "pneumatic_cube_print.stl"
    if orientation == cube.PRINT_ORIENTATION:
        # Use exact generator bytes for the selected orientation; do not
        # replace its archived STL with another serialization of the mesh.
        current = ROOT / "output/pneumatic_cube/pneumatic_cube_print.stl"
        from scipy.spatial import cKDTree
        native = trimesh.load_mesh(current, process=False)
        assert cKDTree(native.vertices).query(mesh.vertices)[0].max() < .00002
        oriented.write_bytes(current.read_bytes())
    else:
        mesh.export(oriented)
    # First run derives the independent printer profile from the existing XL
    # machine preset. Later runs use the pneumatic family's saved profile.
    saved = ROOT / "output/pneumatic_cube/prusa_xl_04_pla.ini"
    values = profile_values(saved if saved.exists() else ROOT / "output/rounded_cube_box/prusa_xl_04_pla_bottom.ini")
    values.update({"layer_height": "0.15", "first_layer_height": "0.2", "perimeters": "5",
        "fill_density": "100%", "fill_pattern": "rectilinear", "top_solid_layers": "6", "bottom_solid_layers": "6",
        "brim_width": "8", "bridge_speed": "20", "bridge_fan_speed": "100", "bridge_angle": "0",
        "support_material": "0" if support == "none" else "1", "support_material_auto": "1" if support == "auto" else "0",
        "support_material_style": "organic" if support == "auto" else "snug", "support_material_buildplate_only": "1",
        "support_material_threshold": "40", "support_material_contact_distance": "0.25", "support_material_bottom_contact_distance": "0.25",
        "support_material_xy_spacing": "0.4", "support_material_interface_layers": "2", "support_material_bottom_interface_layers": "2",
        "support_material_interface_spacing": "0.3", "support_material_spacing": "4", "support_material_closing_radius": "0.5",
        "support_tree_branch_distance": "2", "support_tree_top_rate": "20%", "dont_support_bridges": "1",
        "raft_layers": "0", "external_perimeter_speed": "25", "overhangs": "1"})
    profile = destination / "prusa_xl_04_pla.ini"
    profile.write_text("\n".join(f"{k} = {v}" for k, v in sorted(values.items())) + "\n", encoding="utf-8")
    project, gcode = destination / "pneumatic_cube_xl_pla.3mf", destination / "pneumatic_cube_xl_pla.gcode"
    subprocess.run([str(slicer), "--load", str(profile), "--center", "180,180", "--export-3mf", "--output", str(project), str(oriented)],
                   check=True, capture_output=True)
    with zipfile.ZipFile(project) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    model, config = ET.fromstring(files["3D/3dmodel.model"]), ET.fromstring(files["Metadata/Slic3r_PE_model.config"])
    modifiers = []
    if support == "external":
        # Only external underside startup curvature is enforced. The internal
        # upper shell is deliberately unsupported; check its actual bridges.
        append_modifier(model, config, cube.box((150, 150, 8), (0, 0, 3)), "External startup support only (Z below 7 mm)", "SupportEnforcer")
        cavity = cube.rounded_body(cube.OUTER_RADIUS - cube.WALL_THICKNESS).transform(transform.tolist())
        append_modifier(model, config, cavity, "Hollow interior: no support contacts", "SupportBlocker")
        modifiers = ["SupportEnforcer", "SupportBlocker"]
    model.set("xmlns:slic3rpe", "http://schemas.slic3r.org/3mf/2017/06")
    files["3D/3dmodel.model"] = ET.tostring(model, encoding="utf-8", xml_declaration=True)
    files["Metadata/Slic3r_PE_model.config"] = ET.tostring(config, encoding="utf-8", xml_declaration=True)
    files["Metadata/Slic3r_PE.config"] = ("; generated by PrusaSlicer 2.9.7\n" + "\n".join(f"; {k} = {v}" for k, v in sorted(values.items())) + "\n").encode()
    with zipfile.ZipFile(project, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    completed = subprocess.run([str(slicer), "--export-gcode", "--output", str(gcode), str(project)], capture_output=True, text=True, errors="replace")
    (destination / "slice.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(f"PrusaSlicer failed: {completed.stderr}")
    footer = {}
    for line in gcode.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("; ") and " = " in line:
            k, v = line[2:].split(" = ", 1)
            footer[k] = v
    for key in ("layer_height", "support_material", "support_material_auto", "support_material_style", "support_material_buildplate_only", "printer_model"):
        assert footer.get(key) == values[key], (key, footer.get(key), values[key])
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    result = {"model_version": cube.MODEL_VERSION, "orientation": orientation, "support_mode": support,
        "transform_3x4": transform.tolist(), "source_stl_sha256": sha(source), "oriented_stl_sha256": sha(oriented),
        "profile_sha256": sha(profile), "project_sha256": sha(project), "gcode_sha256": sha(gcode), "modifiers": modifiers,
        "statistics": {k: v for k, v in footer.items() if k.startswith(("estimated printing time", "filament used"))}}
    (destination / "print_review.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"orientation": orientation, "support": support, **result["statistics"]}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--orientation", choices=("face", "edge", "corner"), default="edge")
    parser.add_argument("--support", choices=("auto", "external", "none"), default="external")
    args = parser.parse_args()
    prepare(args.output_dir, args.orientation, args.support)


if __name__ == "__main__":
    main()

"""Build cube print projects with removable internal support enforcers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import generate_rounded_cube_box_stl as cube

CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
NS = {"m": CORE}
ET.register_namespace("", CORE)


def profile_values(path: Path) -> dict:
    return dict(line.split(" = ", 1) for line in path.read_text(encoding="utf-8").splitlines()
                if " = " in line and not line.startswith("#"))


def add_enforcer(model, config, solid, name):
    obj = model.find("m:resources/m:object", NS)
    vertices = obj.find("m:mesh/m:vertices", NS)
    triangles = obj.find("m:mesh/m:triangles", NS)
    start_vertex, start_face = len(vertices), len(triangles)
    transform = model.find("m:build/m:item", NS).get("transform").split()
    # Prusa exports an already-oriented STL centered within its object, and
    # puts the Z placement in the build item. Modifiers use that same frame.
    if [float(v) for v in transform[:9]] != [1, 0, 0, 0, 1, 0, 0, 0, 1]:
        raise ValueError("Unexpected project transform; use already-oriented STL files")
    offset_z = float(transform[-1])
    mesh = cube.to_mesh(solid)
    for x, y, z in mesh.vertices:
        ET.SubElement(vertices, f"{{{CORE}}}vertex", {"x": str(x), "y": str(y), "z": str(z - offset_z)})
    for a, b, c in mesh.faces:
        ET.SubElement(triangles, f"{{{CORE}}}triangle",
                      {"v1": str(a + start_vertex), "v2": str(b + start_vertex), "v3": str(c + start_vertex)})
    volume = ET.SubElement(config.find("object"), "volume",
                          {"firstid": str(start_face), "lastid": str(len(triangles) - 1)})
    for key, value in (("name", name), ("volume_type", "SupportEnforcer"),
                       ("matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1")):
        ET.SubElement(volume, "metadata", {"type": "volume", "key": key, "value": value})


def support_regions(part: str):
    height = cube.HALF + cube.LIP_HEIGHT if part == "bottom" else cube.HALF
    reach = cube.INNER_HALF - 0.8
    # Prusa can use different bridge directions in different roof regions.
    # A sparse internal grid supports both axes, including the thermal recess.
    for index, x in enumerate((-0.75 * reach, -0.25 * reach, 0.25 * reach, 0.75 * reach)):
        yield f"Internal roof X-band {index + 1}", cube.box(
            (3, 2 * reach, cube.OUTER_RADIUS + 2), (x, 0, height - 4.5))
        yield f"Internal roof Y-band {index + 1}", cube.box(
            (2 * reach, 3, cube.OUTER_RADIUS + 2), (0, x, height - 4.5))
    if part == "bottom":
        ring = cube.box((cube.OUTER_SIZE + 2, cube.OUTER_SIZE + 2, 1.2), (0, 0, cube.LIP_HEIGHT - .2))
        ring -= cube.box((66, 66, 2), (0, 0, cube.LIP_HEIGHT - .2))
        yield "Concealed mating-rim support", ring
        for sign in (-1, 1):
            for name, size, center in (
                # The printable bottom is rotated 180 degrees around X:
                # its Y coordinates have the opposite sign to the assembly.
                ("Fan cheek", (3.4, 16, .8), (sign * 26.95, -.7, cube.LIP_HEIGHT + 3.2)),
                ("Fan screw ear", (10.6, 4.6, .8), (sign * 20, -8.8, cube.LIP_HEIGHT + 15)),
                ("Fan seat", (6.2, 16, .8), (sign * 23, -.7, cube.LIP_HEIGHT - cube.FAN_SEAT_Z + .2)),
            ):
                yield f"{name} {sign:+d}", cube.box(size, center)


def build_print_projects(destination: Path, slicer: Path) -> dict:
    if cube.PRINT_OPEN_SIDE_UP:
        raise ValueError("These support regions require the v07 opening-down STL orientation")
    source = ROOT / "output/rounded_cube_box"
    result = {"model_version": cube.MODEL_VERSION, "slicer": subprocess.run(
        [str(slicer), "--help"], check=True, capture_output=True, text=True).stdout.splitlines()[0],
        "print_orientation": "Both openings down, rounded exterior faces up; STLs already oriented.",
        "manual_supports_required": True, "parts": {}}
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    for part, profile_name in (("bottom", "prusa_xl_04_pla_bottom.ini"), ("lid", "prusa_xl_04_pla.ini")):
        stl = source / f"rounded_cube_{part}.stl"
        profile = source / profile_name
        values = profile_values(profile)
        if values.get("support_material_auto") != "0" or values.get("bridge_angle") != "90":
            raise ValueError("Expected the reviewed manual-enforcer / 90-degree bridge profile")
        project = destination / f"rounded_cube_{part}_xl_pla.3mf"
        gcode = destination / f"rounded_cube_{part}_xl_pla.gcode"
        command = [str(slicer), "--load", str(profile), "--center", "180,180", "--export-3mf", "--output", str(project), str(stl)]
        subprocess.run(command, check=True, capture_output=True)
        with zipfile.ZipFile(project) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        model = ET.fromstring(files["3D/3dmodel.model"])
        model.set("xmlns:slic3rpe", "http://schemas.slic3r.org/3mf/2017/06")
        config = ET.fromstring(files["Metadata/Slic3r_PE_model.config"])
        regions = list(support_regions(part))
        for name, solid in regions:
            add_enforcer(model, config, solid, name)
        files["3D/3dmodel.model"] = ET.tostring(model, encoding="utf-8", xml_declaration=True)
        files["Metadata/Slic3r_PE_model.config"] = ET.tostring(config, encoding="utf-8", xml_declaration=True)
        files["Metadata/Slic3r_PE.config"] = (f"; generated by {result['slicer']}\n" +
            "\n".join(f"; {k} = {v}" for k, v in sorted(values.items())) + "\n").encode()
        with zipfile.ZipFile(project, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        # Re-slice the self-contained project without an external profile.
        completed = subprocess.run([str(slicer), "--export-gcode", "--output", str(gcode), str(project)],
                                   capture_output=True, text=True, errors="replace")
        (destination / f"{part}.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode:
            raise RuntimeError(f"Slicing failed for {part}: {completed.stderr}")
        footer = {}
        for line in gcode.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("; ") and " = " in line:
                key, value = line[2:].split(" = ", 1)
                footer[key] = value
        for key in ("support_material_auto", "support_material_style", "support_material_buildplate_only", "bridge_angle", "printer_model"):
            if footer.get(key) != values[key]:
                raise ValueError(f"Embedded setting mismatch: {part}/{key}")
        statistics = {key: value for key, value in footer.items()
                      if key.startswith(("filament used", "estimated printing time"))}
        result["parts"][part] = {"statistics": statistics, "source_stl_sha256": digest(stl),
            "profile_sha256": digest(profile), "gcode_sha256": digest(gcode), "project_sha256": digest(project),
            "support_enforcer_count": len(regions), "support_style": values["support_material_style"]}
        print(f"Sliced {part}: {statistics}", flush=True)
    (destination / "prusa_slicer_validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result

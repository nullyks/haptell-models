"""Slice current cube halves with their own saved profiles into a new review folder."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def find_slicer() -> Path:
    manifest = Path(os.environ.get("LOCALAPPDATA", "")) / "Haptell/Reports/tools.json"
    if manifest.is_file():
        path = Path(json.loads(manifest.read_text(encoding="utf-8"))["PrusaSlicer"]["executable"])
        if path.is_file():
            return path
    for name in ("prusa-slicer-console", "prusa-slicer"):
        if path := shutil.which(name):
            return Path(path)
    raise FileNotFoundError("PrusaSlicer not found; supply --slicer PATH")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slicer", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    slicer = args.slicer or find_slicer()
    # Each run is separate. Never replace the saved printing jobs in output/.
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S") + "_" + uuid4().hex[:8]
    destination = args.output_dir or ROOT / ".local/slicing" / run_id
    destination = destination.resolve()
    if destination == (ROOT / "output").resolve() or (ROOT / "output").resolve() in destination.parents:
        parser.error("Review output must be outside output/")
    if destination == (ROOT / "models").resolve() or (ROOT / "models").resolve() in destination.parents:
        parser.error("Review output must be outside the permanent archive")
    destination.mkdir(parents=True, exist_ok=False)
    import generate_rounded_cube_box_stl as cube
    if hasattr(cube, "PRINT_OPEN_SIDE_UP") and not cube.PRINT_OPEN_SIDE_UP:
        from tools.prepare_cube_prints import build_print_projects
        build_print_projects(destination, slicer)
        print(f"Review folder: {destination}")
        return 0
    source = ROOT / "output/rounded_cube_box"
    version = subprocess.run([str(slicer), "--help"], text=True, capture_output=True, check=True).stdout.splitlines()[0]
    result = {"slicer": version, "parts": {}, "scope": "Offline slicing only; physical print validation is separate."}
    for part, profile in (("bottom", "prusa_xl_04_pla_bottom.ini"), ("lid", "prusa_xl_04_pla.ini")):
        mesh = source / f"rounded_cube_{part}.stl"
        settings = source / profile
        target = destination / f"rounded_cube_{part}_xl_pla.gcode"
        command = [str(slicer), "--load", str(settings), "--export-gcode", "--output", str(target), str(mesh)]
        completed = subprocess.run(command, text=True, capture_output=True, errors="replace")
        (destination / f"{part}.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode:
            print(f"Slicing failed for {part}; see {destination / (part + '.log')}")
            return completed.returncode
        statistics = {}
        for line in target.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("; ") and " = " in line:
                key, value = line[2:].split(" = ", 1)
                if key.startswith(("estimated printing time", "filament used")):
                    statistics[key] = value
        result["parts"][part] = {"profile": profile,
            "source_stl_sha256": hashlib.sha256(mesh.read_bytes()).hexdigest(),
            "profile_sha256": hashlib.sha256(settings.read_bytes()).hexdigest(),
            "gcode_sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "statistics": statistics}
        print(f"Sliced {part}: {statistics}")
    (destination / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Review folder: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

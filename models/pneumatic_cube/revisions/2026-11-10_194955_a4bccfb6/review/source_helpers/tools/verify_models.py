"""Inspect serialized meshes and archive checksums without repairing model files."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]


def inspect_mesh(path: Path) -> dict:
    original = trimesh.load_mesh(path, process=False)
    if not isinstance(original, trimesh.Trimesh) or not len(original.faces):
        raise ValueError(f"No triangle mesh: {path}")
    # STL repeats coordinates per triangle. Weld exact serialized coordinates,
    # rather than using tolerance-based cleanup which can hide defects.
    vertices, inverse = np.unique(original.vertices, axis=0, return_inverse=True)
    mesh = trimesh.Trimesh(vertices=vertices, faces=inverse[original.faces], process=False)
    valid = mesh.nondegenerate_faces(height=1e-8)
    _, edge_uses = np.unique(mesh.edges_sorted, axis=0, return_counts=True)
    degenerate = int(np.count_nonzero(~valid))
    open_edges = int(np.count_nonzero(edge_uses == 1))
    non_manifold = int(np.count_nonzero(edge_uses > 2))
    winding = bool(mesh.is_winding_consistent)
    solid = bool(mesh.is_volume)
    return {
        "file": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "triangles": len(mesh.faces),
        "bounds_mm": mesh.extents.round(6).tolist(),
        "degenerate_triangles": degenerate,
        "duplicate_triangles": int(np.count_nonzero(~mesh.unique_faces())),
        "open_edges": open_edges,
        "edges_used_more_than_twice": non_manifold,
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": winding,
        "positive_closed_volume": solid,
        "passed": not (degenerate or open_edges or non_manifold) and winding and solid,
    }


def inspect_archive(directory: Path) -> dict:
    checked = 0
    revisions = 0
    failures = []
    manifests = list(directory.glob("*/revisions/*/manifest.json"))
    for manifest in sorted(manifests):
        revisions += 1
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for name, expected in data["sha256"].items():
            path = manifest.parent / name
            checked += 1
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                failures.append(str(path))
    for checksums in sorted(directory.glob("*/revisions/*/review/sha256.json")):
        for name, expected in json.loads(checksums.read_text(encoding="utf-8")).items():
            path = checksums.parent / name
            checked += 1
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                failures.append(str(path))
    return {"revisions": revisions, "files_checked": checked, "failures": failures,
            "passed": bool(manifests) and not failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="STL files; default: printable files under output/")
    parser.add_argument("--include-previews", action="store_true", help="Also inspect assembly previews, which may share mating faces")
    parser.add_argument("--report", type=Path, default=ROOT / ".local/reports/model_checks.json")
    args = parser.parse_args()
    paths = args.paths or [p for p in sorted((ROOT / "output").rglob("*.stl"))
                           if args.include_previews or "preview" not in p.stem]
    if not paths:
        parser.error("No STL files found")
    meshes = []
    for path in paths:
        try:
            item = inspect_mesh(path)
        except Exception as error:
            item = {"file": str(path), "passed": False, "error": str(error)}
        meshes.append(item)
        print(f"{'PASS' if item['passed'] else 'FAIL'} {path.name}: "
              f"degenerate={item.get('degenerate_triangles', '?')}, "
              f"open_edges={item.get('open_edges', '?')}, "
              f"non_manifold_edges={item.get('edges_used_more_than_twice', '?')}")
    archive = inspect_archive(ROOT / "models")
    result = {"meshes": meshes, "archive": archive,
              "passed": all(item["passed"] for item in meshes) and archive["passed"]}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Archive: {archive['revisions']} revisions, {archive['files_checked']} checks, "
          f"{len(archive['failures'])} failures")
    print(f"Report: {args.report}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

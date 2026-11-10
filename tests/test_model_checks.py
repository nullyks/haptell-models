import hashlib
import json

import numpy as np
import trimesh

from tools.verify_models import inspect_archive, inspect_mesh


def test_closed_mesh_passes_without_changing_file(tmp_path):
    path = tmp_path / "box.stl"
    trimesh.creation.box().export(path)
    before = path.read_bytes()
    result = inspect_mesh(path)
    assert result["passed"]
    assert result["watertight"]
    assert path.read_bytes() == before


def test_collapsed_triangle_is_detected_after_stl_serialization(tmp_path):
    mesh = trimesh.creation.box()
    vertices = np.vstack([mesh.vertices, [[9, 9, 9]] * 3])
    faces = np.vstack([mesh.faces, [[8, 9, 10]]])
    path = tmp_path / "collapsed.stl"
    trimesh.Trimesh(vertices=vertices, faces=faces, process=False).export(path)
    result = inspect_mesh(path)
    assert not result["passed"]
    assert result["degenerate_triangles"] == 1


def test_missing_triangle_is_detected(tmp_path):
    mesh = trimesh.creation.box()
    mesh.update_faces(np.arange(len(mesh.faces) - 1))
    path = tmp_path / "open.stl"
    mesh.export(path)
    result = inspect_mesh(path)
    assert not result["passed"]
    assert result["open_edges"] == 3


def test_inverted_solid_is_rejected(tmp_path):
    mesh = trimesh.creation.box()
    mesh.invert()
    path = tmp_path / "inverted.stl"
    mesh.export(path)
    result = inspect_mesh(path)
    assert not result["passed"]
    assert not result["positive_closed_volume"]


def test_archive_tampering_is_detected(tmp_path):
    revision = tmp_path / "example/revisions/sample"
    revision.mkdir(parents=True)
    model = revision / "test.stl"
    model.write_bytes(b"original bytes")
    (revision / "manifest.json").write_text(json.dumps({"sha256": {
        "test.stl": hashlib.sha256(model.read_bytes()).hexdigest()}}))
    assert inspect_archive(tmp_path)["passed"]
    model.write_bytes(b"changed bytes")
    result = inspect_archive(tmp_path)
    assert not result["passed"]
    assert result["failures"] == [str(model)]

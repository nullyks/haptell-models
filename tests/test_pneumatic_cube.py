import math

import numpy as np
import pytest

import generate_pneumatic_cube_stl as cube
from tools.check_pneumatic_print import analytic_material, extrusion_paths


@pytest.fixture(scope="module")
def solid():
    return cube.build_model()


def test_one_piece_empty_cube_has_eighteen_separate_openings(solid):
    report = cube.validate(solid)
    assert report["body_bounds_mm"] == [80, 80, 80]
    assert report["connected_solids"] == 1
    assert report["euler_characteristic"] == -32
    assert report["minimum_face_web_between_blends_mm"] >= 3.2
    assert (solid ^ cube.box((60, 60, 60))).volume() < 1e-6


def test_inner_and_outer_rims_are_rounded_and_bore_is_not_enlarged(solid):
    # Independent probe points on the bottom-center hole of the top face.
    # Both face ends must flare; the middle must retain its 27 mm throat.
    for z in (36.4, 39.6):
        for x, filled in ((13.8, False), (14.2, True)):
            probe = cube.box((.02, .02, .02), (x, -16.7, z))
            volume = (solid ^ probe).volume()
            assert volume > .000007 if filled else volume < 1e-8
    probe = cube.box((.02, .02, .02), (13.6, -16.7, 38))
    assert (solid ^ probe).volume() > .000007


def test_selected_edge_orientation_preserves_geometry(solid):
    oriented, matrix = cube.print_transform(solid)
    vertices, _ = cube.mesh_arrays(oriented)
    assert abs(vertices[:, 2].min()) < 1e-8
    assert np.allclose(matrix[:, :3] @ matrix[:, :3].T, np.eye(3))
    assert np.isclose(oriented.volume(), solid.volume())
    assert np.isclose(np.ptp(vertices[:, 0]), 80)


def test_toolpath_reader_handles_leading_decimal_extrusion_and_arcs(tmp_path):
    path = tmp_path / "arc.gcode"
    path.write_text("M83\nG1 X180 Y180 Z1\n;TYPE:Bridge infill\nG1 X181 E.1\nG3 X180 Y181 I-1 J0 E.2\nG1 E.8\n")
    paths = list(extrusion_paths(path))
    assert len(paths) == 2  # In-place unretraction is not deposited path material.
    assert np.isclose(paths[0][2], .1)
    assert np.isclose(paths[1][3], math.pi / 2)
    assert np.allclose(paths[1][1][-1], [0, 1, 1])


def test_analytic_toolpath_model_matches_material_probes(solid):
    points = np.array([[0, -16.7, 38], [13.6, -16.7, 38],
                       [13.8, -16.7, 36.4], [14.2, -16.7, 36.4],
                       [0, 0, 0], [39, 0, 0]])
    expected = [False, True, False, True, False, True]
    assert analytic_material(points).tolist() == expected
    for point, filled in zip(points, expected):
        volume = (solid ^ cube.box((.01, .01, .01), point)).volume()
        assert volume > .0000009 if filled else volume < 1e-8

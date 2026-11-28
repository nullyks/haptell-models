import math

import numpy as np
import pytest

import generate_pneumatic_cube_stl as cube
from tools.check_pneumatic_print import analytic_material, extrusion_paths


@pytest.fixture(scope="module")
def solid():
    return cube.build_model()


def test_rounded_cube_cavity_and_fourteen_openings(solid):
    report = cube.validate(solid)
    assert report["body_bounds_mm"] == [85, 85, 85]
    assert report["connected_solids"] == 1
    assert report["euler_characteristic"] == -24
    assert report["cavity_shape"] == "inward-offset rounded cube"
    assert np.allclose(report["cavity_bounds_mm"], [85 - 2 * cube.WALL_THICKNESS] * 3)
    assert np.isclose(report["cavity_corner_radius_mm"], 15 - cube.WALL_THICKNESS)
    assert np.allclose(list(report["measured_flat_wall_samples_mm"].values()), cube.WALL_THICKNESS, atol=.015)
    assert report["minimum_sampled_exterior_web_mm"] >= 2.6
    assert report["faces"]["front"]["openings"][0]["width_mm"] == 64
    assert report["faces"]["front"]["openings"][0]["height_mm"] == 28
    assert report["faces"]["right"]["openings"][0]["width_mm"] == 38
    assert report["faces"]["top"]["openings"][0]["width_mm"] == 34
    assert report["faces"]["bottom"]["openings"][0]["width_mm"] == 12


def test_bottom_opening_has_rounded_outer_rim_and_nominal_throat(solid):
    # The outer lip flares beyond the 6 mm radius. Farther in, the
    # same radial position must be in material.
    for point, filled in (((6.12, 0, -42.42), False),
                          ((6.34, 0, -42.42), True),
                          ((6.12, 0, -42), True)):
        probe = cube.box((.01, .01, .01), point)
        volume = (solid ^ probe).volume()
        assert volume > .0000009 if filled else volume < 1e-8


def test_selected_corner_orientation_preserves_geometry(solid):
    oriented, matrix = cube.print_transform(solid)
    vertices, _ = cube.mesh_arrays(oriented)
    assert abs(vertices[:, 2].min()) < 1e-8
    assert np.allclose(matrix[:, :3] @ matrix[:, :3].T, np.eye(3))
    assert np.isclose(oriented.volume(), solid.volume())
    assert np.isclose(np.ptp(vertices[:, 0]), 2 * (cube.FLAT_HALF * math.sqrt(2) + cube.OUTER_RADIUS),
                      atol=.01)


def test_toolpath_reader_handles_leading_decimal_extrusion_and_arcs(tmp_path):
    path = tmp_path / "arc.gcode"
    path.write_text("M83\nG1 X180 Y180 Z1\n;TYPE:Bridge infill\nG1 X181 E.1\nG3 X180 Y181 I-1 J0 E.2\nG1 E.8\n")
    paths = list(extrusion_paths(path))
    assert len(paths) == 2  # In-place unretraction is not deposited path material.
    assert np.isclose(paths[0][2], .1)
    assert np.isclose(paths[1][3], math.pi / 2)
    assert np.allclose(paths[1][1][-1], [0, 1, 1])


def test_analytic_toolpath_model_matches_material_probes(solid):
    points = np.array([[0, 0, 0], [0, 0, -41], [6.12, 0, -42.42],
                       [6.12, 0, -42], [0, 0, 42], [0, 42, 0], [39, 24, 24]])
    expected = [False, False, False, True, True, True, False]
    assert analytic_material(points).tolist() == expected
    for point, filled in zip(points, expected):
        volume = (solid ^ cube.box((.01, .01, .01), point)).volume()
        assert volume > .0000009 if filled else volume < 1e-8

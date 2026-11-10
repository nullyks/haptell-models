import itertools

import numpy as np
import pytest

import generate_rounded_cube_box_stl as cube


@pytest.fixture(scope="module")
def parts():
    return cube.build_parts()


def test_requested_envelope_and_internal_clearances(parts):
    lid, bottom = parts
    report = cube.validate(lid, bottom)
    assert report["assembly_bounds_mm"] == [80, 80, 80]
    assert report["outer_edge_radius_mm"] == 8
    assert report["snap_count"] == 8
    assert report["socket_remaining_wall_mm"] >= 2
    assert report["thermal_pad_thickness_mm"] == 1.2
    assert not any(report["component_collisions_mm3"].values())


def test_empty_electronics_regions(parts):
    lid, bottom = parts
    # The previous battery/UNO/charger shelves occupied these probes.
    for solid, size, center in (
        (bottom, (30, 6, 1), (0, 27, -18)),
        (bottom, (30, 6, 1), (0, -27, -28)),
        (lid, (20, 10, 1), (0, 25, 22)),
    ):
        assert (solid ^ cube.box(size, center)).volume() < 1e-6


def test_both_halves_remain_single_closed_bodies(parts):
    for solid in parts:
        assert len(solid.decompose()) == 1
        assert cube.boundary_edge_count(cube.to_mesh(solid)) == 0
    assert (parts[0] ^ parts[1]).volume() < 1e-5


def test_hooks_and_sockets_are_present_on_all_four_walls(parts):
    lid, bottom = parts
    for angle, along in itertools.product((0, 90, 180, 270), cube.SNAP_POSITIONS):
        hook_probe = cube.box((0.1, 0.1, 0.1),
            (cube.INNER_HALF + 0.25, along, cube.SNAP_HOOK_PEAK_Z)).rotate((0, 0, angle))
        assert (hook_probe ^ bottom).volume() > 0.0008
        assert (hook_probe ^ lid).volume() < 1e-7


def test_removed_usb_hole_is_closed(parts):
    # Probe between the two retained vent rows, inside the former USB opening.
    probe = cube.box((1, 1, 0.8), (0, 39, 28.0))
    assert np.isclose((probe ^ parts[0]).volume(), 0.8)


def test_fan_screw_ear_supports_follow_print_rotation():
    from tools.prepare_cube_prints import support_regions

    supports = cube.union([solid for _, solid in support_regions("bottom")])
    fan = cube.fan_bracket().rotate((180, 0, 0)).translate((0, 0, cube.LIP_HEIGHT))
    # Probe the first printed face of each screw ear. The X rotation reverses
    # Y as well as Z; support on the assembly's positive-Y side misses the ear.
    z = cube.LIP_HEIGHT + cube.FAN_MOUNT_PITCH / 2 - 10.4 / 2
    y = -(cube.FAN_BACKING_Y + cube.FAN_BRACKET_WALL / 2)
    for sign in (-1, 1):
        probe = cube.box((1, 1, .2), (sign * cube.FAN_MOUNT_PITCH / 2, y, z))
        assert (probe ^ fan).volume() > .09
        assert (probe ^ supports).volume() > .19

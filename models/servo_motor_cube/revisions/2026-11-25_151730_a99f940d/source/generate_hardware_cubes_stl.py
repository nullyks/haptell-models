"""Generate the three hardware-specific enclosures from the customer drawings."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import manifold3d as m3d
import numpy as np

import generate_lra_actuator_cube_stl as lra
import generate_rounded_cube_box_stl as rounded
from model_archive import preserve_models

VERSION = "v01-fit-trial"
SERVO_VERSION = "v02-loading-clearance-fit-trial"
BOX = rounded.box
HALF = lra.HALF
SIZE = lra.SIZE
RADIUS = lra.RADIUS
STANDARD_WALL = lra.WALL
SERVO_WALL = 5.0
SERVO_BODY_CENTER_Y = 9.5
SERVO_SHAFT_Y = -0.7
SERVO_EAR_Z = -8.5
SERVO_EAR_PITCH = 49.5
SERVO_CROSS_PITCH = 10.0
SERVO_PILOT = 2.7
VOICE_Z = -19.5
VOICE_INNER_X = 5.8
VOICE_OUTER_X = 35.8
VOICE_CLAMP_Y = 13.8
VOICE_CLAMP_X = 9.0
PELTIER_WIDTH = 20.0
PELTIER_DEPTH = 4.0
PELTIER_PAD = 1.2
PELTIER_FACE = HALF - PELTIER_PAD
PELTIER_TRAVEL = 11.5


def cylinder(height, radius, center):
    return m3d.Manifold.cylinder(height, radius, circular_segments=64, center=True).translate(center)


def shells(wall, lid_features=(), base_features=(), extra_cuts=()):
    outer = lra.cube(RADIUS)
    hollow = outer - lra.cube(RADIUS - wall)
    inner_half = HALF - wall
    lid = rounded.union([hollow ^ rounded.half_space(top=True), *lid_features])
    lid = rounded.subtract(lid, [*rounded.snap_sockets(inner_half), *extra_cuts])
    base = rounded.union([hollow ^ rounded.half_space(top=False),
                          rounded.registration(inner_half, rail_width=53), *base_features])
    base = rounded.subtract(base, [lra.cable_notch(), *extra_cuts])
    return lid, base


def check_clear(component, solid, label):
    interference = abs((component ^ solid).volume())
    if interference > 1e-5:
        raise ValueError(f"{label} interferes by {interference:.5f} mm³")


def servo_parts():
    bars = []
    screw_y = [SERVO_BODY_CENTER_Y + side * SERVO_EAR_PITCH / 2 for side in (-1, 1)]
    keepout = BOX((20.8, 40.8, 44), (0, SERVO_BODY_CENTER_Y, -15.5))
    lead_channel = BOX((6.2, 6.0, 7), (0, -13.1, SERVO_EAR_Z - 3))
    for index, (span, y) in enumerate(zip((70, 40), screw_y)):
        bar = BOX((span, 13, 6), (0, y, SERVO_EAR_Z - 3))
        if index == 0:
            braces = []
            for side in (-1, 1):
                points = [(side * u, z) for u, z in
                          ((33.5, -12), (38.4, -12), (38.4, -20.5), (33.5, -14.5))]
                braces.append(rounded.prism_xz(points, y - 6.5, y + 6.5))
            bar = rounded.union([bar, *braces])
            bar -= lead_channel
        bars.append(bar - keepout)
    screws = [cylinder(4.5, SERVO_PILOT / 2, (x, y, SERVO_EAR_Z - 2))
              for x, y in itertools.product((-SERVO_CROSS_PITCH / 2, SERVO_CROSS_PITCH / 2), screw_y)]
    lid, base = shells(SERVO_WALL, base_features=bars, extra_cuts=screws)
    # Omit the middle of the rear alignment rail so the 54.5 mm mounting
    # flange can pass between the two rear snap tongues.
    base -= BOX((21, 4.7, 14), (0, 34.9, 0))
    body = BOX((20, 40, 40.5), (0, SERVO_BODY_CENTER_Y, SERVO_EAR_Z - 27.7 + 40.5 / 2))
    flange = BOX((20, 54.5, 3.8), (0, SERVO_BODY_CENTER_Y, SERVO_EAR_Z + 1.9))
    lead = BOX((4.8, 4.8, 3.2), (0, -12.4, -27.7))
    servo = rounded.union([body, flange, lead])
    for offset in (0, 0.5, 2, 8, 25, 45, 70):
        check_clear(servo.translate((0, 0, offset)), base, f"DS3218 insertion at {offset:g} mm")
    check_clear(servo, lid, "Seated DS3218 and mounting flange envelope")
    # This full-circle envelope is centered on the estimated shaft at the
    # first clear plane above the servo and the closure.
    sweep_radius = 35.5
    sweep = cylinder(24, sweep_radius, (0, SERVO_SHAFT_Y, 19.5))
    check_clear(sweep, lid + base, "Reserved servo weight envelope")
    return {"lid": lid, "bottom": base}, {
        "wall_mm": SERVO_WALL,
        "nominal_internal_width_mm": SIZE - 2 * SERVO_WALL,
        "servo_body_mm": [40, 20, 40.5],
        "servo_flange_span_mm": 54.5,
        "pilot_pattern_mm": [SERVO_CROSS_PITCH, SERVO_EAR_PITCH],
        "pilot_diameter_mm": SERVO_PILOT,
        "nominal_full_circle_envelope_mm": [2 * sweep_radius, 24],
        "weight_envelope_z_from_seam_mm": [7.5, 31.5],
        "weight_notes": "Empty reserved envelope. Check actual horn height, hardware, and moving weight.",
    }


def axial_cylinder(radius, x0, x1):
    return cylinder(x1 - x0, radius, (0, 0, 0)).rotate((0, 90, 0)).translate(((x0 + x1) / 2, 0, VOICE_Z))


def voice_parts():
    cradle = axial_cylinder(13.45, VOICE_INNER_X, 39.7)
    cradle ^= BOX((40, 33, 14), (22, 0, VOICE_Z - 7))
    ears = [BOX((9.4, 6.3, 5.8), (VOICE_CLAMP_X, s * 12.35, VOICE_Z - 2.9))
            for s in (-1, 1)]
    cradle = rounded.subtract(rounded.union([cradle, *ears]), [
        axial_cylinder(11.25, VOICE_INNER_X - 1, VOICE_OUTER_X + .1),
        axial_cylinder(8.5, VOICE_OUTER_X - .2, 43),
    ])
    lid, base = shells(STANDARD_WALL, base_features=[cradle], extra_cuts=[
        cylinder(4.8, 1.35, (VOICE_CLAMP_X, y, VOICE_Z - 2.1))
        for y in (-VOICE_CLAMP_Y, VOICE_CLAMP_Y)])

    top_band = BOX((8.8, 34, 14), (VOICE_CLAMP_X, 0, VOICE_Z + 7))
    top_band -= axial_cylinder(11.25, VOICE_INNER_X, 14.5)
    # The inward stop bears on the end perimeter and leaves the center clear.
    top_band -= axial_cylinder(9.7, 3.8, VOICE_INNER_X + .1)
    top_band -= BOX((2.3, 34, 3.8), (4.65, 0, VOICE_Z + 1.9))
    fasteners = [cylinder(18, 1.65, (VOICE_CLAMP_X, y, VOICE_Z + 7))
                 for y in (-VOICE_CLAMP_Y, VOICE_CLAMP_Y)]
    # Counterbores bring the screw heads down to the mounting ears.
    counterbores = [cylinder(11.5, 2.95, (VOICE_CLAMP_X, y, VOICE_Z + 8.75))
                    for y in (-VOICE_CLAMP_Y, VOICE_CLAMP_Y)]
    clamp = rounded.subtract(top_band, fasteners + counterbores)
    actuator = axial_cylinder(11, VOICE_INNER_X + .08, VOICE_OUTER_X + .08)
    for offset in (0, .5, 2, 8, 15, 25, 50):
        check_clear(actuator.translate((0, 0, offset)), base, f"Voice-coil loading at {offset:g} mm")
    check_clear(actuator, base + lid + clamp, "Seated voice-coil body envelope")
    check_clear(clamp, base + lid, "Seated removable clamp")
    return {"lid": lid, "bottom": base, "clamp": clamp}, {
        "wall_mm": STANDARD_WALL, "actuator_mm": [22, 30],
        "clamp_pilot_diameter_mm": 2.7, "clamp_clearance_hole_mm": 3.3,
        "axial_seat": "The wall-side saddle shoulder and screw-down clamp capture the cylinder.",
    }


def thermal_parts():
    # The flat runway lets a plate begin clear of the two rails and slide
    # flush along the inner face to the fixed rear stop.
    runway = BOX((21.1, 34.2, 3.5), (0, -6.05, PELTIER_FACE - 1.75))
    rail = rounded.union([
        BOX((3.5, 12, 4.95), (side * 12.1, 5.8, PELTIER_FACE - 2.55))
        + BOX((2.0, 12, 1.6), (side * 10.45, 5.8, PELTIER_FACE - 5.15))
        for side in (-1, 1)
    ])
    rail += BOX((20.65, 2.5, 4.8), (0, 12.4, PELTIER_FACE - 2.4))
    vents = []
    for sign, level, x, wall in itertools.product((-1, 1), (23.5, 28.5),
                                                  (-19.5, -6.5, 6.5, 19.5), range(4)):
        slot = rounded.capsule(8, 2, 9).rotate((90, 0, 0))
        vents.append(slot.translate((x, HALF - 1.4, sign * level)).rotate((0, 0, 90 * wall)))
    flip = (0, 180, 0)
    lid, base = shells(STANDARD_WALL, [rail], [rail.rotate(flip)],
                       [runway, runway.rotate(flip), *vents])
    plate = BOX((PELTIER_WIDTH, PELTIER_WIDTH, PELTIER_DEPTH), (0, 0, PELTIER_FACE - PELTIER_DEPTH / 2))
    for offset in np.linspace(-PELTIER_TRAVEL, 0, 12):
        loading = plate.translate((0, float(offset), 0))
        check_clear(loading, lid, "Upper plate slide")
        check_clear(loading.rotate(flip), base, "Lower plate slide")
    for part in (lid, base):
        sign = 1 if part is lid else -1
        probe = BOX((0.2, 0.2, 4), (0, 0, sign * (HALF - 1)))
        thickness = (part ^ probe).volume() / .04
        if not np.isclose(thickness, PELTIER_PAD, atol=1e-5):
            raise ValueError(f"Thermal contact face thickness is {thickness:.3f} mm")
    return {"lid": lid, "bottom": base}, {
        "wall_mm": STANDARD_WALL, "peltier_mount_nominal_mm": [PELTIER_WIDTH, PELTIER_WIDTH, PELTIER_DEPTH],
        "peltier_contact_wall_mm": PELTIER_PAD, "vent_count_per_half": len(vents) // 2,
        "fan": False, "scope": "Passive housing fit only. Verify the received modules and heat rejection.",
    }


def generate(family, builder, version=VERSION):
    parts, report = builder()
    lid, base = parts["lid"], parts["bottom"]
    check_clear(lid, base, "Seated halves")
    measured = rounded.mesh_bounds(rounded.to_mesh(lid + base))[2]
    if not np.allclose(measured, [SIZE] * 3, atol=1e-5):
        raise ValueError(f"Assembly dimensions do not match specification: {measured}")
    output = Path("output") / family
    meshes = {}
    for name, part in parts.items():
        if part.status() != m3d.Error.NoError or len(part.decompose()) != 1:
            raise ValueError(f"{family}/{name} must be a connected solid")
        # Exterior ends face up. The removable clamp prints flat face down.
        pose = part if name == "lid" else part.rotate((180, 0, 0))
        mesh = rounded.to_mesh(pose.translate((0, 0, -pose.bounding_box()[2])))
        if rounded.boundary_edge_count(mesh) or rounded.signed_volume(mesh) <= 0:
            raise ValueError(f"Invalid print mesh for {family}/{name}")
        meshes[name] = mesh
    output.mkdir(parents=True, exist_ok=True)
    for name, mesh in meshes.items():
        path = output / f"{family}_{name}.stl"
        rounded.write_binary_stl(mesh, str(path), f"{family}-{version}-{name}")
        print(f"{path}: {len(mesh.faces)} triangles, boundary_edges=0", flush=True)
    report.update(model_version=version, assembly_bounds_mm=measured.tolist(), outer_radius_mm=RADIUS,
                  cable_notch_mm=[12, 6], shell_snaps=8, seated_halves_overlap_mm3=0)
    (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


@preserve_models("servo_motor_cube")
def servo():
    generate("servo_motor_cube", servo_parts, SERVO_VERSION)


@preserve_models("voice_coil_cube")
def voice():
    generate("voice_coil_cube", voice_parts)


@preserve_models("thermal_cube")
def thermal():
    generate("thermal_cube", thermal_parts)


if __name__ == "__main__":
    builders = {"servo": servo, "voice": voice, "thermal": thermal}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", choices=builders)
    builders[parser.parse_args().family]()

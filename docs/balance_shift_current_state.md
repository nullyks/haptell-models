# Balance-Shift Haptic Enclosure Current State

Date: 2026-06-17

Branch: `codex/balance-shift-development`
Generator: `generate_balance_shift_stl.py`
Output directory: `output/balance_shift/`

## Summary

This is a separate printable enclosure variant for a handheld balance-shift haptic prototype. It keeps the existing egg silhouette and two-piece closure as close to the current `90 mm` diameter / `130 mm` length shell as practical, but replaces the small motor holders with:

- one standard-servo-class body envelope,
- one rotating arm envelope around a vertical servo shaft aligned to the egg long axis,
- one compact dense end-weight envelope,
- one lower-half servo mount with only simple screw bars at the servo ear locations.

The current `output/egg_box_*.stl` files are not overwritten by this variant.

## Generated Files

- `output/balance_shift/balance_shift_lid.stl`
- `output/balance_shift/balance_shift_bottom.stl`

## Placement Logic

The servo body is placed in the rounded lower half. The output shaft is on the main shell centerline and is placed on the shell seam/equator plane:

```text
SERVO_SHAFT_Z = 0.0
```

The servo cradle keeps the narrow-long MS24 footprint visible from above. The output shaft axis is aligned with the egg's longitudinal `z` axis, so the arm rotates in a horizontal `xy` plane around the shell centerline.

`MS24-UF.stl` measurement showed that the shaft is not centered in the servo body. The measured body-center offset from the shaft is about `10.2 mm` along the servo's long axis. The generator therefore keeps the shaft at `x=0, y=0` and shifts the servo body/cradle:

Current simplified servo envelope:

```text
SERVO_BODY_X = 20.0
SERVO_BODY_Y = 40.0
SERVO_BODY_Z = 40.0
SERVO_BODY_CENTER_X = 0.0
SERVO_BODY_CENTER_Y = 10.2
SERVO_BODY_TOP_Z = 0.0
SERVO_BODY_BOTTOM_Z = -40.0
```

The previous centered-body assumption was wrong for this servo class. With the measured offset, keeping the old `-10 mm` shaft height would push the servo body into the narrowing lower shell. Moving the shaft plane to the seam/equator gives enough fit while keeping the shaft on the egg centerline.

## Moving-Mass Clearance Logic

The requested first-pass nominal arm length was roughly `35 mm` to the weight center. With the current `90 mm` outer shell, `2.8 mm` wall, a `12 mm` diameter end weight, and a `3-4 mm` shell clearance target, `35 mm` is not physically available near the seam/lower-half sweep plane.

Current moving-mass envelope:

```text
ARM_PLANE_Z = 0.0
ARM_WEIGHT_CENTER_RADIUS = 29.4
END_WEIGHT_DIAMETER = 12.0
END_WEIGHT_HEIGHT = 4.0
MOVING_MASS_CLEARANCE = 3.5
```

The generator checks the end weight's vertical thickness band around the horizontal sweep plane and computes:

```text
computed safe arm radius=29.48 mm
achieved weight-center arm radius=29.40 mm
moving weight shell clearance=3.58 mm
```

The design therefore uses the largest conservative radius that keeps the moving weight at least about `3.5 mm` from the shell.

## Servo Cradle

The previous complex holder failed the print-fit test: the internal rails blocked the servo body, the cable guide blocked insertion from one end, and support removal was too difficult. The cradle was therefore rebuilt from scratch as a minimal screw mount.

The lower half now includes only two shell-attached crossbars:

- one front/lower screw bar at `y=-15.8 mm`,
- one rear/upper screw bar at `y=36.2 mm`,
- four vertical pilot-hole bosses at the measured MS24 mounting-ear positions `x=+/-6.0 mm`,
- no body saddle pads,
- no side guide rails,
- no radial ribs,
- no support posts,
- no internal cable guide.

The servo body envelope remains clear between the two bars. With the current assumptions, the body occupies `y=-9.8...30.2 mm`; the bars occupy `y=-19.0...-12.6 mm` and `y=33.0...39.4 mm`, leaving about `2.8 mm` nominal end clearance on both sides of the servo body. The bars intentionally overlap the shell envelope at their outer ends so slicers merge them into the bottom shell instead of treating the screw features as loose floating islands.

This is deliberately less guided than the earlier holder. The design priority is now installation clearance and easy support cleanup; the servo should be positioned by its own mounting ears and screws rather than by side rails or a molded body pocket.

## Closure And Sweep Tradeoff

No local seam/lip relief was needed for the moving-weight sweep at the current `29.4 mm` arm radius. The registration lip and detent closure are preserved everywhere.

Tradeoff:

- Keeping the closure intact preserves the proven two-piece fit.
- The moving weight radius is reduced from the requested nominal `35 mm` to `29.4 mm`.
- A larger balance-shift effect would require at least one of: smaller end weight diameter, lower clearance target, local shell enlargement, local seam/lip relief, or a larger outer shell.

## Validation Output

The generator was run after creating the variant:

```text
balance_shift_lid.stl:
  vertices=35170 faces=70336 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 68.0] size=[90.0, 90.0, 68.0]
balance_shift_bottom.stl:
  vertices=36882 faces=73720 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 68.4] size=[90.0, 90.0, 68.4]
```

Parameter checks:

```text
model version=balance-shift-v03-simple-ms24-mount
shaft center relative to seam=0.0 mm
servo body center offset from shaft=0.0 x 10.2 mm
servo body envelope=20.0 x 40.0 x 40.0 mm
moving weight envelope diameter=12.0 mm height=4.0 mm
achieved weight-center arm radius=29.40 mm
computed safe arm radius=29.48 mm
moving weight shell clearance=3.58 mm
servo body corner clearance=0.06 mm
bottom exterior overrun=0.0000 mm
```

## Next Print Feedback To Capture

- Does the MS24-class servo body now pass cleanly between the two screw bars?
- Do the four screw holes align well enough with the real servo mounting ears?
- Are the two shell-attached bars strong enough without the removed ribs/posts?
- Is the `29.4 mm` moving weight radius sufficient for the perceived balance shift?
- Does the removed cable guide leave enough practical room for servo wire routing, or is a later local seam notch needed?

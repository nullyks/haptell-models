# Balance-Shift Haptic Enclosure Current State

Date: 2026-06-16

Branch: `codex/balance-shift-development`
Generator: `generate_balance_shift_stl.py`
Output directory: `output/balance_shift/`

## Summary

This is a separate printable enclosure variant for a handheld balance-shift haptic prototype. It keeps the existing egg silhouette and two-piece closure as close to the current `90 mm` diameter / `130 mm` length shell as practical, but replaces the small motor holders with:

- one standard-servo-class body envelope,
- one rotating arm envelope around a vertical servo shaft aligned to the egg long axis,
- one compact dense end-weight envelope,
- one lower-half servo cradle with clamp bosses and an internal cable guide.

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

The lower half includes:

- four lower saddle pads under the servo body, leaving the shaft centerline open,
- two side guide rails kept below the horizontal arm sweep volume,
- vertical webs tying the lower saddle pads into the side rails,
- broad buttresses tying the rails into the shell wall,
- six radial anchor ribs extending from the cradle into the inner shell wall, so the holder is not a floating slicer island,
- four vertical clamp bosses with pilot holes for a future printed clamp strap, also lowered below the arm sweep volume,
- an internal cable guide and strain-relief posts routing the servo wire below the moving-mass sweep plane toward the seam.

The radial anchor ribs run to radius `40.8 mm` at `z=-24.0...-18.0`. Four ribs start at `18.0 mm`; the two upper diagonal ribs start at `25.6 mm` so they do not intrude into the MS24 body pocket. The ribs intentionally overlap the inner shell wall while staying inside the exterior surface.

The cable guide intentionally does not cut an exterior hole through the shell in this first pass. That preserves the closure and shell strength; if an external cable pass-through is required for the test, add a local seam notch after confirming cable routing.

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
  vertices=37094 faces=74080 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 68.4] size=[90.0, 90.0, 68.4]
```

Parameter checks:

```text
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

- Does the MS24-class servo body fit into the lower half with enough practical installation clearance?
- Does the clamp boss position leave enough room for a printed clamp strap?
- Is the `29.4 mm` moving weight radius sufficient for the perceived balance shift?
- Is the internal cable guide enough, or is an exterior cable exit notch required?

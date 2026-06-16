# Balance-Shift Haptic Enclosure Current State

Date: 2026-06-16

Branch: `codex/balance-shift-development`
Generator: `generate_balance_shift_stl.py`
Output directory: `output/balance_shift/`

## Summary

This is a separate printable enclosure variant for a handheld balance-shift haptic prototype. It keeps the existing egg silhouette and two-piece closure as close to the current `90 mm` diameter / `130 mm` length shell as practical, but replaces the small motor holders with:

- one standard-servo-class body envelope,
- one rotating arm envelope around a horizontal servo shaft,
- one compact dense end-weight envelope,
- one lower-half servo cradle with clamp bosses and an internal cable guide.

The current `output/egg_box_*.stl` files are not overwritten by this variant.

## Generated Files

- `output/balance_shift/balance_shift_lid.stl`
- `output/balance_shift/balance_shift_bottom.stl`
- `output/balance_shift/balance_shift_assembly_preview.stl`
- `output/balance_shift/balance_shift_mechanism_preview.stl`

`balance_shift_mechanism_preview.stl` is preview-only. It includes the shell plus the assumed servo body, arm, end-weight, and sweep envelope.

## Placement Logic

The servo body is placed in the rounded lower half. The output shaft is on the main shell centerline and is placed `10.0 mm` below the shell seam/equator:

```text
SERVO_SHAFT_Z = -10.0
```

The servo is mounted on its side so the output shaft is horizontal. The arm therefore rotates in an `xz` plane relative to the egg long axis, instead of spinning in a flat horizontal disk. The top half remains clear. The lower half contains the servo cradle and the moving-mass sweep envelope.

Current simplified servo envelope:

```text
SERVO_BODY_X = 20.0
SERVO_BODY_Y = 40.5
SERVO_BODY_Z = 40.0
SERVO_BODY_TOP_Z = -10.0
SERVO_BODY_BOTTOM_Z = -50.0
```

Important assumption: this first pass still treats the installed servo body envelope as centered under the output shaft for fit budgeting. That is better than the earlier upright interpretation, but it is still not a fully detailed OEM servo CAD model. If the actual MS24/DS3218 shaft offset must be represented, the lower-half fit should be rechecked before printing.

## Moving-Mass Clearance Logic

The requested first-pass nominal arm length was roughly `35 mm` to the weight center. With the current `90 mm` outer shell, `2.8 mm` wall, a `12 mm` diameter end weight, and a `3-4 mm` shell clearance target, `35 mm` is not physically available near the seam/lower-half sweep plane.

Current moving-mass envelope:

```text
ARM_PLANE_Z = -10.0
ARM_WEIGHT_CENTER_RADIUS = 29.5
END_WEIGHT_DIAMETER = 12.0
END_WEIGHT_HEIGHT = 4.0
MOVING_MASS_CLEARANCE = 3.5
```

The generator samples the moving weight's vertical sweep band and computes:

```text
computed safe arm radius=29.62 mm
achieved weight-center arm radius=29.50 mm
moving weight shell clearance=3.62 mm
```

The design therefore uses the largest conservative radius that keeps the moving weight at least about `3.5 mm` from the shell.

## Servo Cradle

The lower half includes:

- a lower saddle under the servo body,
- two side guide rails,
- broad buttresses tying the rails into the shell wall,
- four vertical clamp bosses with pilot holes for a future printed clamp strap,
- an internal cable guide and strain-relief posts routing the servo wire below the moving-mass sweep plane toward the seam.

The cable guide intentionally does not cut an exterior hole through the shell in this first pass. That preserves the closure and shell strength; if an external cable pass-through is required for the test, add a local seam notch after confirming cable routing.

## Closure And Sweep Tradeoff

No local seam/lip relief was needed for the moving-weight sweep at the current `29.5 mm` arm radius. The registration lip and detent closure are preserved everywhere.

Tradeoff:

- Keeping the closure intact preserves the proven two-piece fit.
- The moving weight radius is reduced from the requested nominal `35 mm` to `29.5 mm`.
- A larger balance-shift effect would require at least one of: smaller end weight diameter, lower clearance target, local shell enlargement, local seam/lip relief, or a larger outer shell.

## Validation Output

The generator was run after creating the variant:

```text
balance_shift_lid.stl:
  vertices=35170 faces=70336 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 68.0] size=[90.0, 90.0, 68.0]
balance_shift_bottom.stl:
  vertices=36990 faces=73924 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 68.4] size=[90.0, 90.0, 68.4]
balance_shift_assembly_preview.stl:
  vertices=72160 faces=144260 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 130.0] size=[90.0, 90.0, 130.0]
balance_shift_mechanism_preview.stl:
  vertices=73838 faces=147476 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 130.0] size=[90.0, 90.0, 130.0]
```

Parameter checks:

```text
shaft center relative to seam=-10.0 mm
servo body envelope=20.0 x 40.5 x 40.0 mm
moving weight envelope diameter=12.0 mm height=4.0 mm
achieved weight-center arm radius=29.50 mm
computed safe arm radius=29.62 mm
moving weight shell clearance=3.62 mm
servo body corner clearance=1.18 mm
bottom exterior overrun=0.0000 mm
```

## Next Print Feedback To Capture

- Does the MS24-class servo body fit into the lower half with enough practical installation clearance?
- Is the side-mounted but still simplified shaft/body assumption acceptable, or does the actual servo shaft offset need to be modelled?
- Does the clamp boss position leave enough room for a printed clamp strap?
- Is the `29.5 mm` moving weight radius sufficient for the perceived balance shift?
- Is the internal cable guide enough, or is an exterior cable exit notch required?

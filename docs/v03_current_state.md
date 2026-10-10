# v03 Current State

Date: 2026-06-15

Branch: `codex/v03-development`
Base: latest `codex/v02-development` at `f9064a3 Reinforce smaller haptic holders`
Related device project: `https://github.com/nullyks/haptell-devices`

## Summary

`v03` is a client test variant of the egg enclosure. It keeps the same external egg shape, mating lip, detent, shell thickness, and STL output names as `v02`, but removes the large haptic holder and replaces the v02 holder set with five identical small holders.

Client request:

- `5 holders in total`
- `3` holders distributed equally along the circumference in the middle or slightly closer to the top of the egg
- `1` holder in the very top center
- `1` holder in the very bottom center

## Generated Files

- `output/egg_box_lid.stl`
- `output/egg_box_bottom.stl`
- `output/egg_box_assembly_preview.stl`

Both the lid and bottom STL files are generated for `v03`, because the bottom half now contains the bottom-center holder.

## Overall Dimensions

All dimensions are millimetres.

- Maximum diameter: `90.0`
- Assembled length: `130.0`
- Lid print height: `68.0`
- Bottom print height: `68.4`
- Nominal wall thickness: `2.8`
- Fit clearance: `0.1`
- Lip height: `6.4`
- Registration lip thickness: `2.8`
- Detent bead: `0.24`
- Detent socket groove: `0.22`
- Detent ramp: `0.9`

## v03 Holder Geometry

All five holders use the reinforced small-holder geometry:

- Holder diameter: `10.0`
- Pocket depth: `4.05`
- Clip count: `3`
- `clip_wall = 1.8`
- `clip_arc_degrees = 46.0`
- `seat_margin = 1.4`
- `clip_head = 0.9`

Current actuator placement:

| Mount | Part | Placement | Center | Angle | Notes |
| --- | --- | --- | ---: | ---: | --- |
| `top_ring_10x4_holder_90` | top | side | `[0.00, 30.45, 42.00]` | `90.0` | ring holder 1 of 3 |
| `top_ring_10x4_holder_210` | top | side | `[-26.37, -15.22, 42.00]` | `210.0` | ring holder 2 of 3 |
| `top_ring_10x4_holder_330` | top | side | `[26.37, -15.22, 42.00]` | `330.0` | ring holder 3 of 3 |
| `top_center_10x4_holder` | top | center | `[0.00, 0.00, 65.24]` | `0.0` | top inner pole holder |
| `bottom_center_10x4_holder` | bottom | center | `[0.00, 0.00, -59.21]` | `0.0` | bottom inner pole holder; local bottom coordinates |

The three ring holders are spaced `120` degrees apart. The center holders use axial frames: top-center points into the lid cavity, and bottom-center points into the bottom cavity.

## Validation Output

The generator was run after the v03 changes. Expected checks passed:

```text
egg_box_lid.stl:
  vertices=36362 faces=72608 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 68.0] size=[90.0, 90.0, 68.0]
egg_box_bottom.stl:
  vertices=36588 faces=73144 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 68.4] size=[90.0, 90.0, 68.4]
egg_box_assembly_preview.stl:
  vertices=72950 faces=145752 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 130.0] size=[90.0, 90.0, 130.0]
```

Sampled holder-to-exterior clearances:

```text
top_ring_10x4_holder_*: min_outer_surface_clearance=1.6943 mm
top_center_10x4_holder: min_outer_surface_clearance=1.6490 mm
bottom_center_10x4_holder: min_outer_surface_clearance=6.2239 mm
```

## Known Risks For Print Feedback

- The top-center and bottom-center holder orientations are new in `v03` and need print validation.
- The bottom-center holder is now inside the bottom half, so confirm it does not interfere with assembly, wiring, or support removal.
- The three ring holders are placed slightly above the lid mid-height at `z=42.0`; adjust `TOP_RING_MOUNT_Z` if the client wants them closer to the seam or closer to the top.
- The haptic mounts are modelled as watertight positive internal solids that overlap into the shell. The slicer preview should confirm the pads fuse into the shell instead of being treated as separate shells.

## Next Print Feedback To Capture

- Do all five small actuators snap in by hand without damaging clips?
- Are the three ring holders high enough toward the top for the intended test?
- Does the top-center holder sit correctly at the inner top pole?
- Does the bottom-center holder sit correctly at the inner bottom pole?
- Does each actuator transfer vibration into the shell strongly enough?
- Do any clips interfere with wires or routing?

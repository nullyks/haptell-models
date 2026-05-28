# v02 Current State

Date: 2026-05-28

Branch: `codex/v02-development`
Tag: `v02`
Commit: `d17b19c Add v02 haptic actuator mounts`
Related device project: `https://github.com/nullyks/haptell-devices`

## Summary

`v02` is based on the frozen `v01` enclosure prototype and adds three internal snap-in haptic actuator mounts to the lid. The external egg shape, mating lip, detent, and overall dimensions are kept from `v01`.

The `v01` tag remains the backup/reference model. Continue new geometry work from `v02` unless the print feedback says to return to the `v01` baseline.

## Product Status

- `v01`: first suitable egg-shaped prototype for the device enclosure; preserved as backup.
- `v02`: current print-test version with internal haptic actuator mounts.
- Current physical status: `v02` has been sent to print; haptic mount fit and vibration transfer are awaiting print feedback.

## Generated Files

- `output/egg_box_lid.stl`
- `output/egg_box_bottom.stl`
- `output/egg_box_assembly_preview.stl`

The bottom half is unchanged from `v01`. The lid and assembly preview were regenerated for `v02`.

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

## Haptic Actuator Sources

- Vybronics `VG2230001H`: official product page lists `22.0 mm` diameter and `30.0 mm` thickness.
- Vybronics `VG1040003D`: official product page lists `10.0 mm` diameter and `4.0 mm` thickness; the current generator uses `4.05 mm` to leave a small allowance.
- Generic sourcing map / Amazon coin motor: currently modelled from the user-provided product dimension `8 mm x 3 mm`.

Relevant source links:

- https://www.vybronics.com/coin-vibration-motors/lra/v-g2230001h
- https://www.vybronics.com/coin-vibration-motors/lra/v-g1040003d
- https://www.vybronics.com/wp-content/uploads/2024/07/VG1040003D_Assembly_Guide_260724.pdf
- https://www.amazon.de/-/en/sourcing-map-Vibration-Motors-Brushless/dp/B085G6WB64

Note: the Amazon page returned a temporary fetch error during documentation, so the 8 x 3 mm motor dimensions should be treated as user-supplied until rechecked manually.

## v02 Mount Geometry

The haptic mounts are generated parametrically in `generate_egg_box_stl.py`; do not hand-edit STL files.

Each mount is built around:

- a raised flat contact pad tied into the lid shell,
- side guide clips around the actuator circumference,
- an open wire/FPC exit sector,
- an over-lip that gives slight preload so the actuator stays pressed against the contact pad.

This follows the mechanical intent from the Vybronics guidance: the actuator should be held in a molded pocket and pressurized enough that it does not disengage during use, while avoiding excessive force.

Current actuator placement:

| Mount | Diameter | Thickness | Lid z | Angle | Clips |
| --- | ---: | ---: | ---: | ---: | ---: |
| `VG2230001H` | `22.0` | `30.0` | `36.0` | `90.0` | `4` |
| `VG1040003D` | `10.0` | `4.05` | `38.0` | `225.0` | `3` |
| `8x3_coin_motor` | `8.0` | `3.0` | `42.0` | `315.0` | `3` |

Current shared mount parameters:

- `MOUNT_RADIAL_CLEARANCE = 0.2`
- `MOUNT_CLIP_WALL = 1.2`
- `MOUNT_SEAT_MARGIN = 1.0`
- `MOUNT_SEAT_EMBED = 0.8`
- `MOUNT_MIN_SEAT_STANDOFF = 0.6`
- `MOUNT_CLIP_HEAD = 0.7`
- `MOUNT_LIP_OVERLAP = 0.35`
- `MOUNT_PRELOAD = 0.15`
- `MOUNT_WIRE_SLOT_DEGREES = 70.0`
- `MOUNT_CLIP_ARC_DEGREES = 34.0`

## Validation Output

The generator was run after the v02 changes. Expected checks passed:

```text
egg_box_lid.stl:
  vertices=36120 faces=72144 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 68.0] size=[90.0, 90.0, 68.0]
egg_box_bottom.stl:
  vertices=36290 faces=72576 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 68.4] size=[90.0, 90.0, 68.4]
egg_box_assembly_preview.stl:
  vertices=72410 faces=144720 boundary_edges=0
  bounds min=[-45.0, -45.0, 0.0] max=[45.0, 45.0, 130.0] size=[90.0, 90.0, 130.0]
```

Fit relationship check remains unchanged from `v01`:

```text
assembly_interference_outside_groove=0.1400
seated_bead_clearance_in_groove=0.0800
```

## Known Risks For Print Feedback

- Snap-in clips are not yet print-validated.
- The haptic mounts are modelled as watertight positive internal solids that overlap into the lid shell. This is common enough for FDM slicers, but the slicer preview should confirm the pads fuse into the lid instead of being treated as separate shells.
- The `VG2230001H` mount is large and tall. It was moved upward to avoid the socket/lip region, but it should still be checked for hand assembly clearance.
- The current preload is intentionally mild. If the actuator fit is loose, increase `MOUNT_PRELOAD` first. If it is too tight, reduce `MOUNT_PRELOAD` or increase `MOUNT_RADIAL_CLEARANCE`.
- For maximum vibration transfer, the actuator must sit firmly against the contact pad; any foam/tape layer will reduce or tune the transfer depending on material stiffness.

## Next Print Feedback To Capture

- Do all three actuators snap in by hand without damaging the clips?
- Does each actuator stay seated after tapping/shaking the lid?
- Is the contact strong enough to transfer vibration into the egg shell?
- Do any clips interfere with wires or FPC routing?
- Does the slicer and printed part visibly fuse the mount pads to the lid?
- Does the added internal geometry make support removal or assembly difficult?

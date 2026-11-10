# Rounded Cube Box — v07, 80 mm / R8

Current generator: `generate_rounded_cube_box_stl.py`, version
`v07-80mm-r8-fan-only-eight-snaps`.

The user's 2026-11-10 reference requests an **80 x 80 x 80 mm exterior, R8 mm
on all edges, without decorative dots or indents**. The enclosure remains two
halves. The user also reports weak closure in the previous print, requests only
fan-related internal holders, slightly taller vents, and printing that protects
the exterior finish. The reference's suggested materials are not a print test.

- [Current v07, selected opening-down STLs](revisions/2026-11-10_185836_23d24978/)
- [Initial v07, floor-down orientation trial](revisions/2026-11-10_182653_f80190dd/)
- [Previous v06](revisions/2026-10-13_073006_f7a8bc2d/)
- [Previous v05](revisions/2026-10-10_113343_3748715a/)
- [Previous v04](revisions/2026-10-10_111644_c2a314f8/)
- [Previous v03](revisions/2026-10-10_110233_cc65c905/)
- [Previous 91 mm threaded v02](revisions/2026-10-10_103358_24bd9aba/)

## Geometry

- Exterior 80 mm on each axis; seam at assembly Z=0. Circular R8 edge rounding
  with spherical corner patches, and matching R4.8 inner rounding.
- Shell wall 3.2 mm. Centered top/bottom 45 x 45 mm R4 thermal contact areas
  retain **1.2 mm thickness**. Nominal Peltier bodies remain 40 x 40 x 3.4 mm,
  with 0.2 mm interface allowance. No separate heatsinks.
- **Eight snap tongues**, two per wall, 10 mm wide and 2.2 mm thick, with tapered
  roots. Previous model: four tongues, 7.2 x 1.6 mm. Nominal insertion interference
  increases from 0.50 to 0.70 mm; seated radial clearance remains 0.45 mm.
  Socket depth 1.15 mm leaves 2.05 mm exterior wall. Lip height 6.8 mm.
  These changes target firmer retention; opening force and fatigue need a print test.
- Retained inside: fan cradle, closure and alignment features. Removed: UNO,
  battery and charger shelves/guides and the associated USB-C opening.
- Each half has 24 rounded slots, **10 x 2 mm**, two rows on each wall.
  Rows are 26.0 and 30.2 mm from the seam; centers along each wall are -20, 0,
  20 mm. This keeps the slots out of the R8 end rounding. No decorative dimples.

## Fan

JZK nominal 50 x 50 x 10 mm fan, vertical in XZ, axis along Y. Cradle envelope
accepts 50 x 12 x 50 mm. It uses two seats, side cheeks and two lower M3 screw
slots. Reinforced v06 construction remains: backing 4.4 mm, seats 2.8 mm,
cheeks 3.2 mm, with load paths to the thick end perimeter outside the thermal pad.

Mounting pitch **40 mm is provisional**. Horizontal 7.4 x 3.4 mm slots nominally
accept 38–42 mm pitch. Measure actual hole spacing, screw diameter and body
depth. Use washers that cover the slots and suitable spacers for the actual fan.
The nominal fan insertion path from the seam is clear; wires, screws, plugs and
real hardware have not been physically fitted.

## Selected printing setup

**Both halves print opening-down, exterior end face up. The STLs are already
oriented.** Bottom height 46.8 mm; lid height 40 mm. This supersedes v06's
floor-down bottom in response to the user's new exterior-finish requirement.

Floor-down avoids a large interior roof but places the R8 outside rounding over
the bed, where its underside overhangs need support or risk poor finish.
Opening-down moves support contact to internal faces and concealed mating
edges. The selected projects enforce supports only in reviewed regions.

PrusaSlicer 2.9.7, Prusa XL IS standard 0.4 mm, Generic PLA, 0.20 mm STRUCTURAL,
4 perimeters, 6/6 solid layers, 15% Grid, 5 mm brim:

| Part | Support | Enforcer volumes | Estimated time | Total PLA | Supports included |
| --- | --- | --- | --- | --- | --- |
| Bottom | Snug, allowed everywhere | 15 | 5h 28m 26s | 95.62 g | 22.21 g |
| Lid | Organic, bed only | 8 | 4h 34m 55s | 70.46 g | 13.90 g |

Combined supports: **36.11 g**, about **39.7% less** than automatic Snug supports
on the same geometry and orientation (59.90 g). This compares support extrusion,
not total filament. Total selected print estimate: 166.08 g / 10h 03m 21s.
Neither estimate proves removal force, surface quality or retention strength.

Both profiles use 0.25 mm top/bottom support gaps, 0.50 mm XY gap, 0.30 mm
interface spacing, 5 mm support pattern spacing, 90-degree bridge direction,
25 mm/s bridges and 100% bridge fan. Bottom has 2/2 interface layers; lid 3/2,
Organic branch distance 2 mm and tip density 30%.

**Open the 3MF as a project with settings.** It contains the support enforcer
volumes and its complete print profile. The manual-support INI alone plus a
plain STL does not recreate these supports. Do not combine the two profiles.
`python tools/slice_models.py` creates fresh, self-contained projects with the
correct enforcers after regeneration. Re-slice whenever geometry changes.

See the [Estonian print and assembly guide](PRUSA_XL_PLA_JUHEND.md).

Latest files are in `output/rounded_cube_box/`:

- `rounded_cube_bottom.stl`, `rounded_cube_lid.stl` — printable geometry
- `rounded_cube_bottom_xl_pla.3mf`, `rounded_cube_lid_xl_pla.3mf` — preferred projects
- matching G-code and separate INIs — Prusa XL IS 0.4 mm / PLA only
- `rounded_cube_assembly_preview.stl` — inspection, not a printable combined part
- `rounded_cube_overview.png`, `rounded_cube_v07_closed.png`, `prusa_v07_supports.png`
- `validation.json`, `prusa_slicer_validation.json`

The current revision's `review/` preserves all 32 comparison jobs and subsequent
final-file attempts, including rejected ones. Their G-code is compressed
losslessly. Those trials are evidence, not alternative ready-to-print jobs;
use `review/selected_prints/` or the latest output projects.

## Validation and limits

Both serialized printable meshes are closed, consistently wound, one solid each,
with zero open/non-manifold edges and zero degenerate triangles. The assembled
envelope is 80 mm on every axis, seated halves do not intersect, fan/Peltier
nominal envelopes are clear, and thermal membranes are 1.2 mm at nine probes each.

The final self-contained 3MFs were sliced with their embedded settings. Each
contains one printable model plus support enforcers; vertex positions agree
with the corresponding STL within 0.000001 mm. Actual toolpaths include support
under all six fan-holder first-overhang regions. A sampled roof-support check
estimates longest free spans of 16.55 mm bottom / 12.79 mm lid; long G-code bridge
commands may cross several support strips. This is an analytical screen, not
a physical bridge-quality test. No sampled support-interface paths lie on the
broad visible exterior faces. Concealed mating edges still need careful cleanup.

Physical fan fit, snap force, repeated opening, PLA creep, exterior finish and
cooling performance remain untested. The reference's PLA/PETG/ABS suggestions do
not validate these PLA settings for other materials. No cooling capacity is claimed.

## References

- [Client reference, received 2026-11-10](references/2026-11-10_client_80mm_R8.png)
- [Prusa: modeling with printing in mind](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)
- [Prusa: support settings](https://help.prusa3d.com/article/support-material_1698)
- [Prusa: Organic supports](https://help.prusa3d.com/article/organic-supports_480131)

Earlier component-source notes remain in Git history; prior print settings remain in the v06 review.

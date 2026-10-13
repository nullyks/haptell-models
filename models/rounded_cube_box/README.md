# Rounded Cube Box — v04, 76 mm snap enclosure

Current generator: `generate_rounded_cube_box_stl.py`.
Client dimensions received 2026-10-10 supersede the previous 91 mm v02.
The image's thread annotation is superseded by the user's explicit snap request.
The previous threaded model and every intermediate trial remain archived.

- [Current v06 trial](revisions/2026-10-13_073006_f7a8bc2d/)
- [Previous v05 trial](revisions/2026-10-10_113343_3748715a/)
- [Previous v04 trial](revisions/2026-10-10_111644_c2a314f8/)
- [Previous v03 trial, R1 and three vent rows](revisions/2026-10-10_110233_cc65c905/)
- [Previous 91 mm threaded v02](revisions/2026-10-10_103358_24bd9aba/)

## Geometry and output

- Exterior: **76 x 76 x 76 mm**, centered seam at Z=0.
- All twelve exterior edges are circularly rounded R2.5 mm, with spherical corner
  patches. The previous 45-degree end bevels and circular screw tubes are removed.
- Side walls/end perimeter: 2.8 mm. Top/bottom centered thermal contact pads
  retain their 45 x 45 mm outline, R4 corners, and **1.2 mm wall thickness**.
- Four independent internal snap tongues: 7.2 mm wide, 1.6 mm thick,
  approximately 12 mm free length to the hook. Nominal 0.50 mm insertion
  interference and 0.45 mm seated radial clearance in the sockets.
- Hook insertion ramp: 1.8 mm; short extraction ramp: 0.3 mm. This favors firm
  retention over easy opening. Opening force has not been physically measured.
- Socket depth: 0.95 mm; remaining local exterior wall: 1.85 mm.
- Side/front registration strips align the halves; back is clear for UNO.
- Each half has **24 rounded horizontal slots**, 10 x 1.4 mm, two rows
  on all four sides. Rows are 31.5 and 34.5 mm away from the center seam, i.e. 6.5 and
  3.5 mm from the outer top/bottom. Slot centers along each wall are -20, 0, 20 mm.
  The middle of the cube is closed. Reduced vent area follows aesthetic intent;
  airflow and cooling performance remain untested.
- Lid has a 12 x 6 mm USB-C access aperture for the charging board, now with
  R2 mm corners. It permits charging without opening the firm snap closure.

Latest files:

- `output/rounded_cube_box/rounded_cube_bottom.stl`
- `output/rounded_cube_box/rounded_cube_lid.stl`
- `output/rounded_cube_box/rounded_cube_assembly_preview.stl` — inspection only
- `output/rounded_cube_box/validation.json`
- `output/rounded_cube_box/rounded_cube_overview.png` — current bottom print/support preview

## Components and arrangement

Coordinates below describe the assembly: Z is top/bottom, +Y is front.
Both Peltier pads are left unobstructed. No separate heatsinks are modeled,
as explicitly confirmed by the user.

| Item | Body envelope X x Y x Z (mm) | Center X, Y, Z (mm) | Basis |
| --- | --- | --- | --- |
| JZK fan | 50 x 12 x 50 | 0, 0, 0 | Seller nominal 50 x 50 x 10; extra depth allowance |
| Arduino Uno | 68.6 x 14 x 53.4 | 0, -27.5, 0 | Official R3 outline; 14 mm component depth assumed |
| LiPo 3000 mAh | 65 x 10 x 35 | 0, 26.5, 0.5 | Seller 65 x 35 x 10, oriented vertically |
| TP4056 | 26 x 17 x 5 | 0, 24.5, 25.5 | Seller PCB 26 x 17; 5 mm height assumed |
| Bottom Peltier | 40 x 40 x 3.4 | 0, 0, -34.9 | Seller detailed dimensions, 0.2 mm interface allowance |
| Top Peltier | 40 x 40 x 3.4 | 0, 0, 34.9 | Same as bottom |

Fan mounts vertically in XZ, with its axis along Y. Two bottom seats and side
cheeks position it; two lower screws retain it against the mounting ears.
Use M3 through screws, nuts, and washers large enough to cover the 7.4 x 3.4 mm
slots. Fan hole pitch is provisionally 40 mm; slots accept horizontal pitches
38–42 mm. **The seller does not give hole pitch or hole diameter. Measure both
axes on the actual fan before printing a final fitting sample.** Backing plane
allows 12 mm fan depth plus 0.6 mm padding/spacer clearance; choose spacers to
match the actual fan thickness. Keep the central rotor opening free.

Battery rests on a front shelf with loose lateral guides. Retain with soft
insulating foam and a removable adhesive strap; no squeeze clip is applied to
the pouch. UNO rests on a rear edge shelf, components toward the rear wall;
its exact mount-hole pattern is not guessed. Secure on component-free PCB
areas with insulating tape/strap. Charger rests on the upper-front tray with
USB-C directed toward +Y. Check socket alignment and cable access physically.

There is an additional empty 16 x 20 x 6 mm reserve centered at (25, 23, 26)
for a small power board. This is only a space reservation, not a selected
converter or driver. TP4056 is a battery charger/protection module; it does
not produce the regulated 5 V needed by UNO/fan or drive a Peltier element.
Final converter/driver boards and wiring must be checked when selected.

## Printing and assembly

The **bottom prints floor-down, open-side-up** from v06 onward. Its STL is
already oriented; do not apply the old 180-degree rotation. Height is 44.4 mm
(38 mm body + 6.4 mm lip). The unchanged lid still prints open-side-down,
height 38 mm.

See the full [Estonian Prusa XL / PLA setup guide](PRUSA_XL_PLA_JUHEND.md).

v06 addresses 2026-10-13 feedback: fragile holders broke while removing the
dense internal supports. Fan backing increased 3.2 -> 4.4 mm, seats 1.6 -> 2.8,
cheeks 2.0 -> 3.2. Battery/UNO shelves are 2.8 mm thick with sloping/floor-attached
ribs. Battery guide walls grow outward. Sloped braces support fixed registration
pads and snap roots; the flexible snap spans, hooks, seating clearances, fan
seating faces and holes, and nominal component locations are unchanged.

PrusaSlicer 2.9.6, XL Input Shaper standard 0.4 mm, Generic PLA, one active tool:

- Both parts: 0.20 mm STRUCTURAL, 4 perimeters, 6/6 solid layers, 15% Grid,
  5 mm outer brim, nozzle 230/220 C, bed 60 C in this Generic PLA profile.
- **Bottom** uses `prusa_xl_04_pla_bottom.ini`: automatic Snug supports
  **everywhere** (including from the interior floor), 0.25 mm top/bottom contact,
  0.50 mm XY spacing, 2/2 interface layers, 0.30 mm interface spacing,
  3 mm pattern spacing, 1 mm closing radius. Bed-only support is incorrect for
  this orientation because the solid floor blocks access to interior shelves.
- **Lid** retains `prusa_xl_04_pla.ini`: automatic Snug supports only from bed,
  0.20 mm top contact, 0 bottom contact (=same as top), 0.35 mm XY spacing,
  3/0 interface layers, 0.20 mm interface spacing, 2 mm pattern spacing,
  2 mm closing radius.
- Bottom: **3h 44m 53s, 73.13 g**, including approximately **4.96 g supports**.
  v05 bottom: 4h 6m 41s, 97.27 g, approximately 37.37 g supports. Support
  extrusion decreased about 87%; these are slicer estimates, not removal tests.
- Lid retains its prior job: 3h 11m 16s, 85.00 g. Actual material/temperature,
  tool-count variant and machine firmware must match the profile used to print.
- Final bottom G-code inspected in Prusa G-code Viewer, full view and lower-layer
  cutaway. Supports are localized under shelves/overhangs, with no broad roof
  support block. Both 3MF projects successfully re-sliced with embedded settings.
- All meshes are watertight after STL serialization. Lid geometry and all four
  flexible snap spans were compared against v05; symmetric-difference volume 0.

Open `rounded_cube_bottom_xl_pla.3mf` or `rounded_cube_lid_xl_pla.3mf` from
`output/rounded_cube_box/` **as a project with settings**. Select your actual
XL tool-count profile if different and re-slice, retaining the above overrides.
The assembly-preview STL is for inspection only. The guide explains manual
settings and support removal. Do not remove the permanent orange ribs shown
in the preview; only the green toolpath regions represent removable supports.

Remove internal supports through the open side before fitting electronics.
Install fan and rear UNO/front battery into the lower half from above. Attach
Peltier elements at the centered pads and the charger to its upper tray. Route
wires away from the fan rotor, hooks, and mating seam. Check charging access
before closing. Align all four snaps and press the halves straight together;
there is no twisting step. This revision intentionally favors retention.

## Validation and limits

The generator validates before replacing any latest STL output:

- No non-manifold/boundary edges and exactly one connected solid per half.
- Assembled bounds 76 x 76 x 76 mm; no interference between seated halves.
- Thermal pad thickness 1.2 mm at nine probe locations per pad.
- No intersections among nominal component bodies or between them and shell,
  mounts, or shelves; clear fan/UNO/battery insertion paths from the open seam.
- Positive snap insertion interference and seated pocket clearance.

These are geometric checks of nominal envelopes, not measured hardware fit.
UNO connector overhang, attached plugs, lead bends, pouch expansion/foam/straps,
charger component height, and any future power hardware need physical checking.
UNO has only 0.9 mm nominal clearance at either board-length end; programming
with an internal USB cable is not included in the current envelope.
Vent area and a fan do not establish a cooling capacity: no thermal test/CFD
has been performed, and heatsinks were explicitly excluded by the user.

## Sources checked 2026-10-10

- [Client drawing](references/2026-10-10_client_dimensions.png): 76 mm exterior,
  approximately R1 corners. AI-generated reference; only requested dimensions
  and rounding intent were adopted.
- [JZK fan, B0CTMDY7F1](https://www.amazon.de/dp/B0CTMDY7F1): 50 x 50 x 10 mm.
  Title/bullets label it 5 V; one description section says 12 V. Voltage/current
  fields are inconsistent, so verify the delivered fan label for electrical work.
- [songyea battery, B0F99KLK2Y](https://www.amazon.de/dp/B0F99KLK2Y): 65 x 35 x
  10 mm, 3.7 V, 3000 mAh. Selected variant is the four-pack of 3000 mAh cells;
  this enclosure holds **one** cell.
- [StarMaker TP4056, B0D9TSG6VB](https://www.amazon.de/dp/B0D9TSG6VB): detailed
  PCB size 26 x 17 mm. The generic product-dimensions field is inconsistent
  and was not used for the PCB footprint.
- [Hailege SP1848, B0CJY49P6X](https://www.amazon.de/dp/B0CJY49P6X): detailed
  description 40 x 40 x 3.4 mm (summary rounds thickness to 3 mm). Sold primarily
  as a thermoelectric generator; active-cooling suitability is not established.
- [Arduino Uno R3 official specification](https://store.arduino.cc/products/arduino-uno-rev3):
  68.6 x 53.4 mm outline; R3 assumed because user specified Uno without revision.

# Rounded Cube Box â€” v04, 76 mm snap enclosure

Current generator: `generate_rounded_cube_box_stl.py`.
Client dimensions received 2026-10-10 supersede the previous 91 mm v02.
The image's thread annotation is superseded by the user's explicit snap request.
The previous threaded model and every intermediate trial remain archived.

- [Current v04 trial](revisions/2026-10-10_111644_c2a314f8/)
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
- Each half has **24 rounded horizontal slots**, 18 x 2.4 mm, two rows
  on all four sides. Rows are 15 and 29 mm away from the center seam.
- Lid has a 12 x 6 mm USB-C access aperture for the charging board.

Latest files:

- `output/rounded_cube_box/rounded_cube_bottom.stl`
- `output/rounded_cube_box/rounded_cube_lid.stl`
- `output/rounded_cube_box/rounded_cube_assembly_preview.stl` â€” inspection only
- `output/rounded_cube_box/validation.json`
- `output/rounded_cube_box/rounded_cube_overview.png` â€” current PrusaSlicer review overview

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
38â€“42 mm. **The seller does not give hole pitch or hole diameter. Measure both
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

Both print STL files already have their **open side facing the build plate**.
The lid is 38.0 mm high. The bottom is 44.4 mm high because its 6.4 mm
registration lip projects past the seam and touches the bed.

Validated slicing setup on 2026-10-10, PrusaSlicer 2.9.6:

- Printer: Original Prusa XL Input Shaper, standard 0.4 mm nozzle, one active tool.
- Filament: Generic PLA @XLIS; print preset: 0.20mm STRUCTURAL @XLIS 0.4.
- 0.20 mm layers, 4 perimeters, 6 top/bottom solid layers, 15% infill, 5 mm brim.
- Automatic snug supports from the build plate, 0.20 mm Z contact gap,
  0.35 mm XY separation, 3 interface layers. Automatic support generation is
  explicitly enabled; the vendor preset otherwise uses support enforcers only.
- Both final G-codes were inspected in Prusa G-code Viewer, including interior
  cutaways. Supports reach the roof/trays and elevated bottom rim. Side vents
  remain open in the preview; their narrow roofs use bridging.
- Both imported STLs report manifold=yes and one connected part; slicing
  completed without a mesh repair/error message.
- Bottom: **4h 2m 32s, 94.66 g**. Lid: **3h 7m 3s, 82.72 g**.
  Combined separate jobs: **7h 9m 35s, 177.38 g**, including supports/brim.
  These are slicer estimates, not measured print results.
- Remove internal supports carefully around the cantilevers; verify that all
  four tongues move before closing. PLA latch strength and actual opening force
  still require a physical print test.

Open `output/rounded_cube_box/rounded_cube_bottom_xl_pla.3mf` or
`rounded_cube_lid_xl_pla.3mf` in PrusaSlicer for editable model/settings projects.
Matching `.gcode` files, `prusa_xl_04_pla.ini`, screenshots, and
`prusa_slicer_validation.json` are stored beside them. Re-slice using the actual
XL tool-count/filament variant if it differs from this single-tool setup.
The assembly-preview STL is for inspection, not a print job.

For reproduction, load the saved INI when slicing each print STL. The installed
CLI preset selector returned an unrelated printer during the initial attempt;
the final INI resolves the installed official PrusaResearch vendor profile's
inheritance explicitly. Final G-code and 3MF metadata were checked for XLIS and
0.4 mm; no MINI configuration is used in the delivered files.

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

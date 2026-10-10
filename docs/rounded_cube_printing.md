# 91 mm rounded cube enclosure

The generator `generate_rounded_cube_box_stl.py` creates a two-piece enclosure
based on the supplied concept image. The exterior is 91 x 91 x 91 mm with a
nominal 15 mm corner radius. A circular screw joint is hidden inside the square
shell so that the parts can physically rotate during assembly.

The side walls and the perimeter of each end face are 2.8 mm thick. A recessed
45 x 45 mm central thermal pad in the top and bottom is 1.2 mm thick to transfer
heat from an internally mounted Peltier element more effectively. Each thin pad
still corresponds to three nominal 0.4 mm extrusion widths and six 0.20 mm
layers.

Version v02 replaces the support-sensitive spherical end edges with 45-degree
printable bevels. The 15 mm rounding around the vertical corners is retained.
The hidden thread has 8.0 mm engagement (about 2.5 turns) and 0.30 mm radial
clearance.

## Generated files

- `output/rounded_cube_box/rounded_cube_bottom.stl`
- `output/rounded_cube_box/rounded_cube_lid.stl`
- `output/rounded_cube_box/rounded_cube_assembly_preview.stl` (inspection only)

The printable lid is already inverted, with its exterior top face on the build
plate. The printable bottom is already upright on its exterior bottom face.

## PrusaSlicer baseline: Prusa XL, 0.4 mm nozzle, PLA

- Printer profile: Original Prusa XL, 0.4 mm nozzle
- Filament profile: the profile matching the actual PLA brand; use Generic PLA
  if no measured profile exists
- Layer height: 0.20 mm (0.15 mm for a smoother exterior)
- First layer: 0.20 mm
- Perimeters: 4
- Top solid layers: 6
- Bottom solid layers: 6
- Infill: 15% gyroid
- Seam position: Rear or Aligned; rotate both parts so the seam is on the least
  visible side
- External perimeter speed: 30-35 mm/s
- Small perimeter speed: 20-25 mm/s
- First-layer speed: 20 mm/s
- Avoid crossing perimeters: enabled
- Detect thin walls / Arachne perimeter generator: enabled
- Elephant foot compensation: 0.15-0.20 mm
- Brim: 4 mm if the selected PLA tends to lift; otherwise none

Enable supports only for the internal connector webs:

- Support material: For support enforcers only
- On build plate only: disabled (the supports must start on the inner cavity
  floor)
- Style: Organic
- Overhang threshold: 50 degrees
- Top contact Z distance: 0.20 mm
- XY separation: 0.30 mm
- Interface layers: 2
- Paint/enforce support only below the annular connector ledges. Block support
  on the thread flanks so the grooves are not filled. Do not paint support on
  the exterior 45-degree bevels.

Use 100% cooling after layer 3. Start with the PLA profile's normal nozzle and
bed temperatures (typically about 210 C / 60 C) and follow the spool maker's
range when it differs.

## Peltier temperature limit

PLA is not intended for sustained high-temperature use and may soften or deform
above about 50-60 C. Use a temperature sensor at the plastic/Peltier interface,
closed-loop control, and an independent thermal cutoff. Do not run a Peltier
module without the heat sinking required for its opposite face.

## Fit and finishing

The modeled radial thread clearance is 0.30 mm (0.60 mm diametrically). Remove
all support residue and any seam blob from the thread before the first assembly.
Start the lid square to the bottom and turn without forcing it. A trace of dry
PTFE lubricant can be used after cleaning; do not use oil that may attack or
stain the contents.

If the fit is too tight, first increase `THREAD_RADIAL_CLEARANCE` by 0.10 mm. If
it is too loose, reduce it by 0.05-0.10 mm. Regenerate both mating parts after
any fit change.

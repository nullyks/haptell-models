# 91 mm rounded cube enclosure

The generator `generate_rounded_cube_box_stl.py` creates a two-piece enclosure
based on the supplied concept image. The exterior is 91 x 91 x 91 mm with a
nominal 15 mm corner radius. A circular screw joint is hidden inside the square
shell so that the parts can physically rotate during assembly.

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
- Top solid layers: 5
- Bottom solid layers: 5
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

Enable supports for the internal connector webs:

- Support material: enabled, everywhere (the supports must start on the inner
  cavity floor, not on the build plate)
- Style: Organic
- Overhang threshold: 50 degrees
- Top contact Z distance: 0.20 mm
- XY separation: 0.30 mm
- Interface layers: 2
- Paint/enforce support only below the annular connector ledges. Block support
  on the thread flanks so the grooves are not filled.

Use 100% cooling after layer 3. Start with the PLA profile's normal nozzle and
bed temperatures (typically about 210 C / 60 C) and follow the spool maker's
range when it differs.

## Fit and finishing

The modeled radial thread clearance is 0.35 mm (0.70 mm diametrically). Remove
all support residue and any seam blob from the thread before the first assembly.
Start the lid square to the bottom and turn without forcing it. A trace of dry
PTFE lubricant can be used after cleaning; do not use oil that may attack or
stain the contents.

If the fit is too tight, first increase `THREAD_RADIAL_CLEARANCE` by 0.10 mm. If
it is too loose, reduce it by 0.05-0.10 mm. Regenerate both mating parts after
any fit change.

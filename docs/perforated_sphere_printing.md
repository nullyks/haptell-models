# 91 mm perforated sphere enclosure

`generate_perforated_sphere_stl.py` creates a separate two-piece spherical
enclosure based on the supplied reference image. It does not overwrite the egg
or rounded-cube outputs.

## Geometry

- Exterior: 91 mm diameter and 91 mm assembled height
- Wall: 2.8 mm
- Top hemisphere: two 45 mm holes and one central 35 mm hole
- Bottom hemisphere: one central 45 mm hole and two 35 mm side holes
- Hidden thread: 8.0 mm engagement, 3.2 mm pitch, about 2.5 turns
- Thread radial clearance: 0.30 mm
- No holes at either polar print pad

Each outer pole has a 37.69 mm flat print pad followed by a tangent 45-degree
transition into the spherical middle. This avoids the rough support scars found
under the first rounded-cube prototype while keeping the assembled dimensions.

## Generated files

- `output/perforated_sphere/perforated_sphere_lid.stl`
- `output/perforated_sphere/perforated_sphere_bottom.stl`
- `output/perforated_sphere/perforated_sphere_assembly_preview.stl` (inspection only)

Both printable parts are already oriented with their polar flat on the build
plate. Do not rotate or scale them.

## PrusaSlicer: Prusa XL, 0.4 mm nozzle, PLA

- Layer height: 0.20 mm
- First layer: 0.20 mm
- Perimeters: 4
- Top solid layers: 5
- Bottom solid layers: 5
- Infill: 15% gyroid
- External perimeter speed: 30-35 mm/s
- Small perimeter speed: 20-25 mm/s
- Elephant-foot compensation: 0.15-0.20 mm
- Avoid crossing perimeters: enabled
- Seam position: Rear or Aligned
- Brim: normally unnecessary on the 37.69 mm flat; add 4 mm only if the PLA
  lifts from the selected sheet

Use painted supports rather than automatic supports over the whole model:

- Support material: For support enforcers only
- On build plate only: disabled
- Style: Organic
- Top contact Z distance: 0.20 mm
- XY separation: 0.30 mm
- Interface layers: 2
- Paint support below the internal connector webs and under only the upper arcs
  of the horizontal 35/45 mm openings
- Block support on the outer polar pads, their 45-degree transitions, the
  thread flanks, and the lower portions of the openings

Inspect the sliced preview layer-by-layer. No support should touch the visible
polar transitions. Remove all support residue and seam blobs from the thread
before assembly, then start the lid square and turn it without forcing it.

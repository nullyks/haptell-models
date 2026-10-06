# 91 mm perforated sphere enclosure

`generate_perforated_sphere_stl.py` creates a separate two-piece spherical
enclosure based on the supplied reference image. It does not overwrite the egg
or rounded-cube outputs.

## Geometry

- Exterior: 91 mm diameter and 91 mm assembled height
- Wall: 2.8 mm
- Top hemisphere: two 31.5 mm holes and one 24.5 mm hole
- Bottom hemisphere: one 31.5 mm hole and two 24.5 mm holes
- Hidden thread: 8.0 mm engagement, 3.2 mm pitch, about 2.5 turns
- Thread radial clearance: 0.30 mm
- Exact spherical exterior without flattened poles or exterior bevels
- Three holes per hemisphere at 120-degree intervals
- Bottom pattern rotated 60 degrees relative to the top pattern
- No holes at either pole

The six holes are distributed around the full circumference rather than grouped
on one viewing side. The top uses small/large/large holes; the bottom uses
small/large/small holes in the alternating 60-degree positions. Version v03
reduces both hole classes by 30% from the reference image dimensions.

## Generated files

- `output/perforated_sphere/perforated_sphere_lid.stl`
- `output/perforated_sphere/perforated_sphere_bottom.stl`
- `output/perforated_sphere/perforated_sphere_assembly_preview.stl` (inspection only)

Both printable parts are already oriented with the threaded opening toward the
build plate. Do not rotate or scale them. Supports are intentionally required
for the inner spherical ceilings and the upper arcs of the side openings.

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
- Brim: 4-6 mm, with a 0.10-0.15 mm separation if needed to protect the male
  thread's smooth lead-in

Supports are required:

- Support material: On build plate only
- Style: Organic
- Top contact Z distance: 0.20 mm
- XY separation: 0.30 mm
- Interface layers: 2
- Ensure support reaches the inner spherical ceiling and the upper arcs of all
  horizontal 24.5/31.5 mm openings
- Add a support enforcer below the bottom half's outer seam shoulder if the
  automatic preview leaves it unsupported
- Block support on both thread flanks and keep support-interface material out of
  the female groove

Inspect the sliced preview layer-by-layer. The bottom part rests on the male
thread's smooth lead-in; the active ridge starts above the first layers. Use
0.15-0.20 mm elephant-foot compensation and remove every brim/support remnant
from the thread before assembly. Start the lid square and turn it without
forcing it.

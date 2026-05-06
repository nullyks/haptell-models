# Egg Box STL

Parametric STL model for a hollow, two-piece egg-shaped box.

## Files

- `output/egg_box_bottom.stl` - printable bottom half with male registration lip
- `output/egg_box_lid.stl` - printable lid
- `output/egg_box_assembly_preview.stl` - assembled preview, useful for checking fit in a slicer
- `generate_egg_box_stl.py` - generator script for adjusting dimensions and rebuilding the STL files

## Current Parameters

- Longest dimension: 130 mm
- Maximum width: 90 mm
- Assembled height: 52 mm
- Wall thickness: 2.4 mm
- Fit clearance: 0.2 mm
- Lip height: 7.2 mm
- Material target: STL for 0.4 mm nozzle printing

## Regenerate

Run the script with Python and it will overwrite the STL files in `output/`.

```powershell
python generate_egg_box_stl.py
```

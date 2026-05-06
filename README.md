# Egg Box STL

Parametric STL model for a hollow, two-piece egg-shaped box.

## Files

- `output/egg_box_bottom.stl` - printable bottom half with male registration lip
- `output/egg_box_lid.stl` - printable lid
- `output/egg_box_assembly_preview.stl` - assembled preview, useful for checking fit in a slicer
- `generate_egg_box_stl.py` - generator script for adjusting dimensions and rebuilding the STL files

## Current Parameters

- Maximum diameter: 90 mm
- Assembled length: 90 mm
- Shell wall thickness: 0.8 mm
- Registration lip thickness: 1.2 mm
- Fit clearance: 0.2 mm
- Lip height: 5.2 mm
- Material target: STL for 0.4 mm nozzle printing

## Regenerate

Run the script with Python and it will overwrite the STL files in `output/`.

```powershell
python generate_egg_box_stl.py
```

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
- Nominal shell wall thickness: 2.8 mm
- Minimum shell wall target: at least 2.6 mm
- Registration lip thickness: 2.8 mm
- Fit clearance: 0.2 mm
- Lip height: 6.4 mm
- Material target: STL for 0.4 mm nozzle printing

## Regenerate

Run the script with Python and it will overwrite the STL files in `output/`.

```powershell
python generate_egg_box_stl.py
```

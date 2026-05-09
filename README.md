# Egg Box STL

Parametric STL model for a hollow, two-piece egg-shaped box.

## Files

- `output/egg_box_bottom.stl` - printable bottom half with male registration lip
- `output/egg_box_lid.stl` - printable lid
- `output/egg_box_assembly_preview.stl` - assembled preview, useful for checking fit in a slicer
- `generate_egg_box_stl.py` - generator script for adjusting dimensions and rebuilding the STL files

## Current Parameters

- Maximum diameter: 90 mm
- Assembled length: 130 mm
- Sharp-tip half print height: 68 mm
- Rounded half print height: 68.4 mm
- Nominal shell wall thickness: 2.8 mm
- Minimum shell wall target: at least 2.6 mm
- Registration lip thickness: 2.8 mm
- Fit clearance: 0.1 mm
- Lip height: 6.4 mm
- Retention feature: 0.32 mm annular detent bead with matching 0.27 mm socket groove
- Material target: STL for 0.4 mm nozzle printing

## Regenerate

Run the script with Python and it will overwrite the STL files in `output/`.

```powershell
python generate_egg_box_stl.py
```

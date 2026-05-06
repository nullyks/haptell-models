# Heart Box STL

Parametric STL model for a hollow, two-piece, slightly heart-shaped box.

## Files

- `output/heart_box_bottom.stl` - printable bottom half with male registration lip
- `output/heart_box_lid.stl` - printable lid
- `output/heart_box_assembly_preview.stl` - assembled preview, useful for checking fit in a slicer
- `generate_heart_box_stl.py` - generator script for adjusting dimensions and rebuilding the STL files

## Current Parameters

- Longest dimension: 150 mm
- Width: 104 mm
- Assembled height: 60 mm
- Wall thickness: 2.4 mm
- Fit clearance: 0.2 mm
- Lip height: 7.2 mm
- Material target: STL for 0.4 mm nozzle printing

## Regenerate

Run the script with Python and it will overwrite the STL files in `output/`.

```powershell
python generate_heart_box_stl.py
```


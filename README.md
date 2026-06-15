# Egg Box STL

Parametric STL model for a hollow, two-piece egg-shaped device enclosure prototype.

Related device project: `https://github.com/nullyks/haptell-devices`

## Files

- `output/egg_box_bottom.stl` - printable bottom half with male registration lip
- `output/egg_box_lid.stl` - printable lid
- `output/egg_box_assembly_preview.stl` - assembled preview, useful for checking fit in a slicer
- `generate_egg_box_stl.py` - generator script for adjusting dimensions and rebuilding the STL files
- `docs/v03_current_state.md` - current v03 handoff and print-test notes

## Current Parameters

- Product status: `v01` is the first suitable prototype for a device enclosure and should be kept as the backup/reference model.
- Current development version: `v03`, based on the latest `v02-development`, removes the large motor holder and provides five identical small `10.0 x 4.05 mm` holders for client testing.
- Maximum diameter: 90 mm
- Assembled length: 130 mm
- Sharp-tip half print height: 68 mm
- Rounded half print height: 68.4 mm
- Nominal shell wall thickness: 2.8 mm
- Minimum shell wall target: at least 2.6 mm
- Registration lip thickness: 2.8 mm
- Fit clearance: 0.1 mm
- Lip height: 6.4 mm
- Retention feature: 0.24 mm annular detent bead with matching 0.22 mm socket groove and gentler 0.9 mm ramps
- Material target: STL for 0.4 mm nozzle printing

## v03 Haptic Mounts

The model includes five small internal actuator pockets. Each pocket uses a raised flat contact pad tied into the egg shell, side guide clips, a wire/FPC exit gap, and a small over-lip preload to hold the actuator against the shell for better vibration transfer.

- Three holders are distributed equally around the top half circumference at `z=42.0 mm`, angles `90`, `210`, and `330` degrees.
- One holder is centered at the top inner pole.
- One holder is centered at the bottom inner pole.
- All five holders use `10.0 mm` diameter x `4.05 mm` pocket depth, with the reinforced small-holder clip geometry from late `v02`.

The v03 mounts are generated parametrically in `generate_egg_box_stl.py`; do not hand-edit the STL files.

For the current v03 handoff, validation output, and print-test risks, see `docs/v03_current_state.md`.

## Regenerate

Run the script with Python and it will overwrite the STL files in `output/`.

```powershell
python generate_egg_box_stl.py
```

## Continue With Codex On Another Computer

Clone the repository, install the Python dependency, then regenerate the STL files.

```powershell
git clone https://github.com/nullyks/haptell-models.git
cd haptell-models
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python generate_egg_box_stl.py
```

For Codex or another coding agent, see `AGENTS.md`. It records the current print feedback, model constraints, validation checks, and the safest parameters to adjust for future fit or shape changes.

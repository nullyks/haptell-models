# Egg Box STL

Parametric STL model for a hollow, two-piece egg-shaped device enclosure prototype.

Related device project: `https://github.com/nullyks/haptell-devices`

## Files

- `output/egg_box_bottom.stl` - printable bottom half with male registration lip
- `output/egg_box_lid.stl` - printable lid
- `output/egg_box_assembly_preview.stl` - assembled preview, useful for checking fit in a slicer
- `generate_egg_box_stl.py` - generator script for adjusting dimensions and rebuilding the STL files
- `generate_balance_shift_stl.py` - separate generator for the balance-shift haptic enclosure variant
- `output/balance_shift/` - generated STL files for the balance-shift variant; this path is separate so the current egg-box outputs are not overwritten
- `docs/balance_shift_current_state.md` - current balance-shift handoff and design notes
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

## Balance-Shift Haptic Variant

`generate_balance_shift_stl.py` creates a separate two-piece shell variant for a handheld balance-shift haptic prototype. It keeps the current outer 90 mm x 130 mm egg silhouette and closure geometry, but replaces the small motor holders with a lower-half servo cradle and a moving-mass clearance envelope.

Generated files:

- `output/balance_shift/balance_shift_lid.stl`
- `output/balance_shift/balance_shift_bottom.stl`
- `output/balance_shift/balance_shift_assembly_preview.stl`
- `output/balance_shift/balance_shift_mechanism_preview.stl` - preview-only STL that includes the assumed servo body, arm, end-weight, and sweep envelope

Current first-pass balance-shift assumptions:

- Servo body envelope: `40.0 x 20.0 x 40.5 mm`
- Shaft center: `10.0 mm` below the shell seam, on the main shell centerline
- Moving weight envelope: `12.0 mm` diameter x `4.0 mm` height
- Achieved safe arm radius to weight center: `31.8 mm`
- Moving weight to shell clearance: about `3.59 mm`
- The seam lip is left intact for closure strength; no sweep relief is needed at the current radius.

For placement logic, clearance math, and tradeoffs, see `docs/balance_shift_current_state.md`.

## Regenerate

Run the script with Python and it will overwrite the STL files in `output/`.

```powershell
python generate_egg_box_stl.py
```

To regenerate only the balance-shift variant:

```powershell
python generate_balance_shift_stl.py
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

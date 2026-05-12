# Codex Handoff Notes

This repository contains a parametric STL generator for a two-piece, 3D-printable egg-shaped box.

## Current Product State

- Public repository: `https://github.com/nullyks/haptell-models`
- Main generator: `generate_egg_box_stl.py`
- Generated STL files:
  - `output/egg_box_lid.stl`
  - `output/egg_box_bottom.stl`
  - `output/egg_box_assembly_preview.stl`
- Target printer/material assumption: FDM printing with a 0.4 mm nozzle.

## Current Model Parameters

All dimensions are millimetres.

- Maximum diameter: `90.0`
- Assembled length: `130.0`
- Sharp-tip half print height: `68.0`
- Rounded half print height: `68.4`
- Nominal wall thickness: `2.8`
- Minimum wall target: at least `2.6`
- Fit clearance: `0.1`
- Lip height: `6.4`
- Registration lip thickness: `2.8`
- Retention feature: `0.24` annular detent bead, `0.22` matching socket groove, `0.9` ramps

Recent print feedback:

- The halves fit and hold very tightly.
- The current detent was softened from the previous version to make opening easier.
- Tip and rounded end were acceptable after the last print.
- Wall strength is sufficient.
- No printer artifacts were reported.

## Setup On A New Machine

Use Python 3.10+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then regenerate the STLs:

```powershell
python generate_egg_box_stl.py
```

The script overwrites the STL files in `output/`.

## Validation Workflow

After changing geometry, always regenerate STL files and check the script output. Expected output includes:

- `boundary_edges=0` for all STL files
- assembly preview bounds: `90.0 x 90.0 x 130.0`
- lid bounds height: `68.0`
- bottom bounds height: `68.4`

For fit-related changes, verify these derived relationships in the script or with a small Python check:

- lip normal radius = `lid_socket_radius() - CLEARANCE`
- bead peak radius = lip normal radius + `DETENT_PROTRUSION`
- groove radius = socket radius + `DETENT_GROOVE_DEPTH`
- assembly interference outside groove should stay small; current target is about `0.14 mm`
- seated bead clearance in groove should stay positive; current target is about `0.08 mm`

For wall thickness, use the existing profile-distance sanity checks from prior work if making major profile changes. The last checked approximate minima were:

- top shell: about `2.718 mm`
- bottom shell: about `2.775 mm`

## Design Intent

Keep the model parametric and generated from `generate_egg_box_stl.py`. Do not hand-edit STL files.

Preferred minimal changes:

- Fit too tight: reduce `DETENT_PROTRUSION`, increase `DETENT_RAMP`, or slightly increase `CLEARANCE`.
- Fit too loose: increase `DETENT_PROTRUSION` first, then consider reducing `CLEARANCE`.
- Tip too sharp: reduce `TOP_POWER` slightly.
- Tip too round: increase `TOP_POWER` slightly.
- Wall too thin: increase `WALL_THICKNESS` and re-check lip/socket radii.

Avoid large redesigns such as hinges, threads, separate clips, or non-parametric mesh edits unless the user explicitly asks for that.

## Git Notes

The repository may contain local documentation drafts under `docs/`. Treat them as optional project documentation; do not include them in geometry commits unless the user asks.

When changing the model, commit the generator and regenerated STL outputs together.

# Codex Handoff Notes

This repository contains a parametric STL generator for a two-piece, 3D-printable egg-shaped device enclosure prototype.

## Current Product State

- Public repository: `https://github.com/nullyks/haptell-models`
- Related device project: `https://github.com/nullyks/haptell-devices`
- Main generator: `generate_egg_box_stl.py`
- Balance-shift variant generator: `generate_balance_shift_stl.py`
- Version `v01`: first suitable prototype for a device enclosure; keep as backup/reference.
- Version `v02`: previous development iteration with three haptic actuator mounts, including the large holder.
- Version `v03`: current development iteration, based on latest `v02-development`, with five identical small haptic actuator holders for client testing.
- Current v03 handoff: `docs/v03_current_state.md`
- Current balance-shift handoff: `docs/balance_shift_current_state.md`
- Generated STL files:
  - `output/egg_box_lid.stl`
  - `output/egg_box_bottom.stl`
  - `output/egg_box_assembly_preview.stl`
- Balance-shift STL files are generated separately under `output/balance_shift/` and must not overwrite the current `output/egg_box_*.stl` files.
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
- v03 haptic mounts:
  - all holders use `10.0` diameter x `4.05` pocket depth with 3 reinforced snap clips;
  - three `top_ring_10x4_holder_*` mounts are equally distributed around the top half circumference at `z=42.0`, angles `90`, `210`, and `330` degrees;
  - `top_center_10x4_holder` is centered at the top inner pole;
  - `bottom_center_10x4_holder` is centered at the bottom inner pole.

Recent print feedback:

- The halves fit and hold very tightly.
- The current detent was softened from the previous version to make opening easier.
- Tip and rounded end were acceptable after the last print.
- Wall strength is sufficient.
- No printer artifacts were reported.
- v02 haptic mount print feedback from 2026-05-30:
  - largest `VG2230001H` holder dimensions were correct but the holder was too weak and broke/bent easily;
  - smallest `8x3_coin_motor` holder needed to be `0.5 mm` deeper;
  - first reinforced `VG2230001H` revision pushed part of the holder pad through the outer egg surface;
  - all other geometry was acceptable.
  - Latest generator revision applies this feedback and reduces the largest holder `seat_embed` so the reinforcement stays internal.
- v02 haptic mount print feedback from 2026-05-31:
  - largest `VG2230001H` holder is now acceptable;
  - smallest-position holder should have exactly the same internal dimensions as the medium `VG1040003D` holder;
  - medium and smallest-position holder constructions broke too easily and have been reinforced.
- v03 client request from 2026-06-15:
  - create a test egg with only small motor holders;
  - 5 holders total;
  - 3 holders distributed equally along the circumference in the middle or slightly closer to the top of the egg;
  - 1 holder in the very top center;
  - 1 holder in the very bottom center.

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

For the balance-shift variant, run:

```powershell
python generate_balance_shift_stl.py
```

This writes only to `output/balance_shift/`.

## Validation Workflow

After changing geometry, always regenerate STL files and check the script output. Expected output includes:

- `boundary_edges=0` for all STL files
- assembly preview bounds: `90.0 x 90.0 x 130.0`
- lid bounds height: `68.0`
- bottom bounds height: `68.4`

For the balance-shift variant, expected output includes:

- `boundary_edges=0` for all files under `output/balance_shift/`
- printable lid bounds: `90.0 x 90.0 x 68.0`
- printable bottom bounds: `90.0 x 90.0 x 68.4`
- shaft center relative to seam: current target `0.0`
- servo body center offset from shaft: current target `0.0 x 10.2`
- achieved weight-center arm radius: current target `29.4`
- moving weight shell clearance: current target about `3.58`
- bottom exterior overrun: `0.0000`

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
- Haptic actuator too tight: slightly increase `MOUNT_RADIAL_CLEARANCE` or reduce `MOUNT_PRELOAD`.
- Haptic actuator too loose: increase `MOUNT_PRELOAD` first, then consider `MOUNT_LIP_OVERLAP`.
- Largest actuator holder weak: keep motor-facing dimensions unchanged and reinforce outward by increasing its per-mount `clip_wall`, `clip_arc_degrees`, `seat_margin`, or `clip_head`. Be careful with `seat_embed`; too much embed can push the holder pad through the outer egg surface.
- Medium or smallest-position holder weak: keep their shared `10.0 x 4.05` internal dimensions unchanged and reinforce outward through per-mount `clip_wall`, `clip_arc_degrees`, `seat_margin`, or `clip_head`.
- v03 holder size: keep all five holders at `10.0 x 4.05` unless the user explicitly changes that requirement.
- v03 holder count/placement: keep three top ring holders, one top center holder, and one bottom center holder unless the user explicitly changes the layout.
- Balance-shift variant: keep it in `generate_balance_shift_stl.py` and `output/balance_shift/` so the egg-box STL outputs are not overwritten.
- Balance-shift shell: preserve the current outer egg silhouette and closure unless a measured servo/weight conflict requires a local relief.
- Balance-shift moving mass: the requested nominal `35 mm` arm radius does not fit with a `12 mm` end weight and 3-4 mm shell clearance inside the current 90 mm shell; current safe radius is about `29.5 mm`, and the current design uses `29.4 mm`.
- Balance-shift servo: current first pass uses the `MS24-UF.stl` measured shaft offset. The shaft axis is vertical / parallel to the egg long axis and stays on the shell centerline; the servo body center is offset `10.2 mm` along the long body axis.
- Balance-shift bottom cradle: current print feedback rejected the complex holder. Keep the holder as two simple shell-attached screw bars only. Do not reintroduce body saddle pads, side rails, support posts, radial ribs, or an internal cable guide unless the user explicitly asks for them.
- Balance-shift outputs: generate only `balance_shift_lid.stl` and `balance_shift_bottom.stl`; do not reintroduce balance-shift assembly/mechanism preview STL files unless the user asks for them.

Avoid large redesigns such as hinges, threads, separate clips, or non-parametric mesh edits unless the user explicitly asks for that.

## Git Notes

The repository may contain local documentation drafts under `docs/`. Treat them as optional project documentation; do not include them in geometry commits unless the user asks.

Keep the `v01` git tag as the frozen reference for the first suitable enclosure prototype. Keep `codex/v02-development` as the previous three-holder reference, `codex/v03-development` as the five-holder reference, and do new balance-shift geometry work on `codex/balance-shift-development`.

When changing the model, commit the generator and regenerated STL outputs together.

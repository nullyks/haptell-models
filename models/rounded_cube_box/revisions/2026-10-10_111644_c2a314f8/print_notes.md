# v04: R2.5 corners and two vent rows

User requested rounder edges/corners, two vent rows per half, and Prusa XL / 0.4 mm / PLA slicing review.

- Exterior R1 -> R2.5 mm. Vent levels now 15 and 29 mm from seam; 24 slots per half.
- Exterior 76 mm, Peltier pads, component arrangement and snap geometry retained.
- Generator geometric checks passed; both STLs report manifold and one connected part in PrusaSlicer 2.9.6.
- Official XL Input Shaper 0.4 mm / Generic PLA / 0.20mm STRUCTURAL profiles resolved from installed PrusaResearch vendor INI.
- Overrides: 4 perimeters, 6 top/bottom layers, 15% infill, 5 mm brim; automatic snug build-plate supports with 0.2 mm Z and 0.35 mm XY separation.
- Final toolpaths reviewed in Prusa G-code Viewer. Roof/tray/rim supports present; two vent rows visible. Straight support-path sampling found no centerlines in the narrow bottom tongue-to-wall gaps (see review JSON for scope).
- Bottom 4h 2m 32s / 94.66 g; lid 3h 7m 3s / 82.72 g, including supports and brim. Estimates only.
- Editable 3MF, exact G-code, INI and screenshots preserved under review/.
- No physical print test. Remove supports carefully and verify four latches flex freely before assembly. PLA latch strength/retention must be confirmed on a print.

# v06: stronger bottom with reduced removable supports

2026-10-13 user print feedback on v05: internal holders are fragile and break during difficult support removal. User requested necessary changes and precise Prusa XL / 0.4 mm / PLA setup instructions.

- Bottom exported floor-down/open-up; unchanged outside dimensions and component layout.
- Fan backing 4.4 mm, seats 2.8 mm, cheeks 3.2 mm. Sloped feet anchor on thick perimeter outside thermal pads. Battery/UNO shelves 2.8 mm with ribs; battery guides thicken outward. Fixed registration pads and snap roots have sloped underside braces. Flexible snap spans and hooks unchanged.
- All generator checks pass; serialized STL welded-edge checks pass. Lid geometry and snap free spans compared against frozen v05: zero symmetric-difference volume.
- Final XLIS / Generic PLA / 0.20 STRUCTURAL: 4 perimeters, 6/6 solids, 15% Grid, 5 mm brim. Bottom uses automatic Snug supports everywhere (floor blocks bed-only), Z 0.25 top/bottom, XY 0.5, interface 2/2 at 0.3 spacing, body spacing 3, closing radius 1. Final bottom preview/cutaway reviewed in Prusa G-code Viewer. Both 3MF projects re-sliced successfully.
- Final bottom: 73.13 g, 3h 44m 53s, approximately 4.96 g supports vs v05 97.27 g, 4h 6m 41s, 37.37 g supports. Support reduction approximately 87%. Estimates only; no physical force/strength/removal test.
- Earlier first v06 trial is archived at 2026-10-13_072734_80cc292c. It lacked the final registration-pad braces and sliced at 75.15 g / 3h 52m 14s with Snug. Organic comparison of that trial was 76.46 g / 4h 39m 22s. Final uses lighter Snug settings.
- Full Estonian instructions and exact sliced projects, configs, JSON, screenshots preserved in review/. Lid retains previous slicing settings and geometry.

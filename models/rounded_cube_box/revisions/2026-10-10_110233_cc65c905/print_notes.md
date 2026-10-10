# v03 — 76 mm snap closure and component layout

Status: geometrically validated prototype; not yet physically printed.

Client requirements: 76 mm cube, R1 exterior edges/corners, firm snaps instead
of threads, same centered top/bottom Peltier contact pads, central 50 mm fan,
side slots, and space for Uno, one 3000 mAh LiPo and TP4056. User confirmed no
separate heatsinks. See the current family README for sources and assumptions.

Validated: three closed STL files, one connected solid per printable half,
76 mm assembly, zero seated-half interference, 1.2 mm pads, nominal component
fit and loading paths. Verified exported STL topology after coordinate welding.

Review artifacts in `review/` include the generated validation report and a
preview derived from the same geometry. They do not establish physical fit,
snap force, slicer support coverage, or cooling performance.

Before the first fitting print, confirm fan hole pitch/vertical hole position,
Uno component depth/connector overhang and TP4056 height. Nominal fan pitch
40 mm; UNO depth 14 mm and charger height 5 mm are provisional assumptions.

## Print feedback

- Printer/material/layer height: pending
- Support removal and surface finish: pending
- Snap closing force and retention: pending
- Fan, Uno, battery and charging-board fit: pending
- Wiring and charging socket access: pending
- Next measured change: pending

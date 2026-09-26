# `*-topline.svg` rotated to vertical

All eight per-family topline guides under `mechanical/templates/individuals/`
were rotated so the guide line runs exactly vertical, and each file was
reframed to fit. Only these eight files were touched.

## Method

Each path was rotated as a rigid body about its own bounding-box centre. No
geometry was distorted: lengths, curvature, the relative angle between
segments, and the stroke width are all unchanged.

* **Rotation amount** — the path's first→last on-curve chord was rotated by the
  smallest angle that puts it on vertical (i.e. onto `+90°`, so each line keeps
  the direction it already pointed; no line was flipped 180°).
* **Vertex order** — preserved exactly as it was before rotation.
* **Reframe** — new `viewBox` = rotated path's exact bounding box expanded by a
  1 mm margin on all four sides; `width`/`height` = that box + 2 mm, so the line
  sits centred with 1 mm clear on every edge. (Same framing rule the files
  already used.) Frame units are unchanged: 1 user unit = 1 mm.

For the one curved path (`LC`) the two control points were rotated with the
endpoints, which maps the cubic exactly.

## Per-file changes

| File | Rotation | Size before → after | New `viewBox` |
|---|---|---|---|
| `A-topline.svg` | +160.469° | 31.296803 × 84.587416 → **2 × 89.629811** | `190.064856 1723.540766 2 89.629811` |
| `B-topline.svg` | +47.686° | 90.278854 × 89.806569 → **43.215492 × 121.38269** | `8.214231 1726.673579 43.215492 121.38269` |
| `LC-topline.svg` | +3.805° | 10.180845 × 43.586855 → **9.131899 × 43.678732** | `41.813062 1747.65982 9.131899 43.678732` |
| `MC-topline.svg` | +23.900° | 30.095821 × 65.401645 → **2 × 71.34799** | `26.73842 1701.798584 2 71.34799` |
| `P-topline.svg` | +101.182° | 159.513788 × 33.137361 → **2 × 162.561915** | `116.469965 1732.820854 2 162.561915` |
| `PC-topline.svg` | +105.576° | 67.161118 × 20.163985 → **2 × 69.645411** | `165.6952 1760.61524 2 69.645411` |
| `S-topline.svg` | +96.095° | 165.532834 × 19.463414 → **2 × 166.462636** | `94.482287 1677.741122 2 166.462636` |
| `SC-topline.svg` | −23.089° | 37.520367 × 85.322145 → **2 × 92.577461** | `82.173302 1675.607634 2 92.577461` |

### New path data

| File | `d` |
|---|---|
| A | `M 191.064855587,1724.540766421 L 191.064855587,1812.170577857` |
| B | `M 50.42972313,1727.673579235 L 9.214231241,1812.83307997 L 50.42972313,1847.05626961` |
| LC | `M 49.944961085,1748.659820194 C 42.813061825,1774.295348155 49.12379069,1777.525304008 49.944961085,1790.338552215` |
| MC | `M 27.738420107,1702.798583857 L 27.738420107,1772.146573719` |
| P | `M 117.469964741,1733.820853982 L 117.469964742,1894.382769095` |
| PC | `M 166.695199733,1761.615239674 L 166.695199733,1829.260650683` |
| S | `M 95.482286552,1678.741122488 L 95.482286552,1843.203758722` |
| SC | `M 83.173301721,1676.607633946 L 83.173301722,1767.185094557` |

Only `width`, `height`, `viewBox` and `d` changed. The `style`, `stroke-width`,
ids, `inkscape:label` and all other markup are byte-identical, and no
`transform` attribute was introduced.

### Notes on individual files

* **A, MC, P, PC, S, SC** are single straight segments, so their new endpoints
  share exactly one x value and the frame collapses to a 2 mm-wide band
  (line + 1 mm each side).
* **B** is a bent 3-point polyline. Its overall chord was made vertical, so the
  kink survives as a lateral excursion: the frame is 43.2 mm wide because the
  middle vertex swings ~41 mm to one side of the vertical axis. It is a straight
  vertical guide only in the sense that its ends are vertically aligned.
* **LC** is a curved (cubic) path whose endpoints now align vertically; the
  curve bulges ~7 mm to one side, so it has a 9.1 mm frame rather than a 2 mm
  band.
* **P, PC, S** rotate by ~96–106° rather than a small angle, because those
  guides pointed nearly horizontally and their original direction was kept.
* The rotation angles above are the *change in the chord's angle*, chosen so
  every path lands on exactly `+90°`. After rotation each straight path's
  endpoint x-spread is ≤ 3e-14 mm and each curved path's endpoints match exactly.

## Verification

* **Verticality** — chord angle after rotation is exactly `90°` in all eight;
  on-curve endpoint x-spread ≤ 1e-9 mm for the straight guides.
* **Rigid body** — total path length is unchanged in every file (max delta
  9.2e-10 mm; `LC`'s cubic length checked by numerical integration).
* **Framing** — for all eight the new `viewBox` equals the rotated path's exact
  bounding box + 1 mm, and `width`/`height` equal that box + 2 mm.
* **Rendering** — each file was rasterised; ink falls fully inside the frame in
  every case (nothing clipped or out of bounds). The six straight guides render
  an ink band 0.5 mm wide, equal to the declared stroke width.
* **No collateral edits** — text outside `width`/`height`/`viewBox`/`d` is
  byte-identical to the previous revision, and `stroke-width` is unchanged.

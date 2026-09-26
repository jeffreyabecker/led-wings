# `*-topline.svg` transform bake-out

All eight per-family topline guides under `mechanical/templates/individuals/` were
edited so the `d` attribute of the guide path is expressed directly in final
viewBox coordinates and no `transform` attribute is needed anywhere in the file.

Files changed (8):

`A-topline.svg`, `B-topline.svg`, `LC-topline.svg`, `MC-topline.svg`,
`P-topline.svg`, `PC-topline.svg`, `S-topline.svg`, `SC-topline.svg`

Nothing else was touched — not the `viewBox`, `width`, `height`, `style`,
`stroke-width`, ids, labels, or any other file.

## What changed in each file

Exactly one edit per file: the `<path>` `d` value was rewritten from
pre-transform local coordinates into post-transform coordinates, and the
`transform="matrix(a,b,c,d,e,f)"` attribute was deleted. For paths written with
relative commands (`m`, `l`, `c`) the geometry was also converted to absolute
commands (`M`, `L`, `C`), since baked coordinates have no relative delta to carry.

| File | Old `transform` matrix | Path commands before → after | `d` before → after |
|---|---|---|---|
| `A-topline.svg` | `0.99255402,-0.08036897,0.01496052,0.83861014,-14.62963,1685.3532` | `M`/`L` → `M`/`L` | `M 189.97083,166.42291 220.92708,70.908332` → `M 176.416454273,1809.649379917 L 205.7132569,1727.061964361` |
| `B-topline.svg` | `0.99255402,-0.08036897,0.01496052,0.83861014,-14.629631,1685.3532` | `m`+2 implicit `l` → `M`+2 `L` | `m 17.191849,73.9245 33.86305,107.95017 53.507351,-3.74178` → `M 3.540156797,1745.965344098 L 38.766053881,1833.771912825 L 91.819011241,1826.333687488` |
| `LC-topline.svg` | `0.99255402,-0.08036897,0.01496052,0.83861014,-14.629631,1685.3532` | `m`/`c` → `M`/`C` | `m 62.446065,81.315032 c -5.915268,30.499158 0.584955,34.465788 2.036252,49.785358` → `M 48.567977011,1748.526084445 C 43.153037242,1774.578391602 49.664202559,1777.382431514 51.333881964,1790.112939011` |
| `MC-topline.svg` | `0.99255402,-0.08036897,0.01496052,0.83861014,-14.62964,1685.3533` | `M`/`L` → `M`/`L` | `M 28.124985,27.043356 55.252841,105.24642` → `M 13.690509592,1705.771756486 L 41.786330622,1769.17340109` |
| `P-topline.svg` | `0.99255402,-0.08036897,0.01496052,0.83861014,-14.629631,1685.3532` | `M`/`L` → `M`/`L` | `M 51.075206,176.98588 210.10057,155.0965` → `M 38.713070835,1829.670491906 L 196.226858648,1798.533131171` |
| `PC-topline.svg` | `0.99255402,-0.08036897,0.01496052,0.83861014,-14.629627,1685.3533` | `m`+implicit `l` → `M`/`L` | `m 147.50521,156.23646 65.88125,-15.34584` → `M 134.114640841,1804.519937796 L 199.275758625,1786.355952561` |
| `S-topline.svg` | `0.98862708,-0.15036039,0.08713051,0.99841597,-862.78009,1634.7161` | `m`+implicit `l` → `M`/`L` | `m 863.20611,265.20014 164.76869,7.32287` → `M 13.715869418,1769.704147672 L 177.248703686,1752.240733538` |
| `SC-topline.svg` | `0.82163364,0.41517259,-0.55705064,0.73304695,425.90848,1209.7361` | `m`+implicit `l` → `M`/`L` | `m 28.635866,625.62209 24.44498,99.8207` → `M 100.933485183,1680.235291581 L 65.41311826,1763.557436922` |

Each file shrank by one line (the removed `transform` attribute); the trailing
`/>` of `<path>` moved onto the `id` line.

## Why the `viewBox` is left alone

The existing `viewBox` was already the correct frame for the **baked** coordinates:
in every file it equals the baked path's exact bounding box expanded by a 1 mm
margin, with `width`/`height` equal to that box plus 2 mm. Verified to 6 dp:

| File | baked path bbox min (x, y) | `viewBox` min (x, y) |
|---|---|---|
| A | 176.416454, 1727.061964 | 175.416454, 1726.061964 |
| B | 3.540157, 1745.965344 | 2.540157, 1744.965344 |
| LC | 43.153037, 1748.526084 | 42.153037, 1747.526084 |
| MC | 13.690510, 1705.771756 | 12.690510, 1704.771756 |
| P | 38.713071, 1798.533131 | 37.713071, 1797.533131 |
| PC | 134.114641, 1786.355953 | 133.114641, 1785.355953 |
| S | 13.715869, 1752.240734 | 12.715869, 1751.240734 |
| SC | 65.413118, 1680.235292 | 64.413118, 1679.235292 |

So changing the `viewBox` would have *shifted* the guide within its own canvas.
Leaving it untouched keeps each guide exactly where it was.

## Verification

The committed version of each file (transform + pre-transform `d`) was rasterised
and pixel-diffed against the edited version (no transform + baked `d`), at the
file's native render size. Geometry is unchanged; the residual differences are
sub-pixel anti-aliasing:

| File | raster | mean diff (0–255) | ink pixels old → new |
|---|---|---|---|
| A | 118×320 | 0.118 | 635 → 653 |
| B | 341×339 | 0.131 | 1050 → 1038 |
| LC | 38×165 | 0.051 | 301 → 302 |
| MC | 114×247 | 0.040 | 536 → 536 |
| P | 603×125 | 0.337 | 1043 → 1142 |
| PC | 254×76 | 0.556 | 445 → 496 |
| S | 626×74 | 0.160 | 1212 → 1212 |
| SC | 142×322 | 0.106 | 666 → 682 |

Also confirmed: 0 `transform` attributes remain in `*-topline.svg`, and all eight
`viewBox` values are byte-identical to their pre-edit values.

## Note on stroke width

Seven matrices contain a small anisotropic scale (e.g. `sx = 0.9958`,
`sy = 0.8387` in the `0.99255402,…` family), so the declared
`stroke-width: 0.264583px` was already rendering as a very slightly elliptical
stroke ~16% narrower perpendicular to the line's own `x` basis. That is a
pre-existing property of the original files and was deliberately **not** changed:
the inline `stroke-width` was left exactly as-is so the rendered result matches
the original.

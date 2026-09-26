# `outline-toplines.svg` — inverse rotations on the `<use>` tags

The eight per-family guides were rotated to vertical in the individual files
(see `topline-vertical-rotation.md`). This change puts the **inverse of those
same rotations** onto the `<use>` elements in `outline-toplines.svg`, so the
aggregate sheet draws each guide exactly where it drew it before. Only this one
file changed; the individual toplines and everything else are untouched.

## What changed

A `transform` attribute was added to each of the eight topline `<use>` elements
in the `<g id="top-lines">` group. Nothing else was modified — same `href`,
`width`, `height`, ids and group matrix; the `total-outline` group is untouched.

The transform is a plain rotation:

```
rotate(-θ cx cy)
```

* `-θ` is the inverse of the rotation recorded in `topline-vertical-rotation.md`.
* `(cx, cy)` is the path's own bounding-box centre, in the file's coordinate
  space — the fixed point the rotation in the individual file was taken about.

### Why no translation

The `<use>` elements reference a `<g>` (`…#-topline-def`), **not** an `<svg>` or
`<symbol>`. For a `<g>` reference the `width`/`height` attributes are ignored and
no `viewBox` mapping is applied: the referenced path's raw coordinates are used
directly in the sheet. The individual-file rotation was performed about that
path's own centre in those same raw coordinates, so the exact inverse is the
matching rotation about the same centre. Nothing else shifts.

An earlier attempt added `translate(…)` terms and treated the rotation centre as
a `viewBox`-relative "local" point; that was wrong for a `<g>` reference and
placed every guide far outside the sheet.

## Per-file values

| `<use>` id | Inverse rotation | Centre `(cx, cy)` |
|---|---|---|
| `A-topline` | `-160.468527°` | `191.064856, 1768.355672` |
| `B-topline` | `-47.685529°` | `47.679584, 1789.868628` |
| `LC-topline` | `-3.805088°` | `47.24346, 1769.319512` |
| `MC-topline` | `-23.90006°` | `27.73842, 1737.472579` |
| `P-topline` | `-101.182074°` | `117.469965, 1814.101812` |
| `PC-topline` | `-105.576076°` | `166.6952, 1795.437945` |
| `S-topline` | `-96.095426°` | `95.482287, 1760.972441` |
| `SC-topline` | `23.088631°` | `83.173302, 1721.896364` |

Verbatim attributes as written:

```
B-topline    transform="rotate(-47.685529 47.679584 1789.868628)"
P-topline    transform="rotate(-101.182074 117.469965 1814.101812)"
LC-topline   transform="rotate(-3.805088 47.24346 1769.319512)"
A-topline    transform="rotate(-160.468527 191.064856 1768.355672)"
SC-topline   transform="rotate(23.088631 83.173302 1721.896364)"
MC-topline   transform="rotate(-23.90006 27.73842 1737.472579)"
PC-topline   transform="rotate(-105.576076 166.6952 1795.437945)"
S-topline    transform="rotate(-96.095426 95.482287 1760.972441)"
```

## Verification

* **Pointwise** — rotating each new path back by `-θ` about `(cx, cy)` reproduces
  the pre-rotation path to ≤ 7e-10 mm in every one of the eight guides (the B and
  LC control points included).
* **Rendering** — the aggregate was rasterised with the referenced content
  inlined (resvg does not follow external `href`s), both for the committed
  pre-change file and the current file. The two render identically:

  | | ink bbox in sheet units (viewBox `0 0 300 300`) |
  |---|---|
  | committed (pre-change) | `[50.3, 31.8, 254.3, 209.0]` |
  | current (after fix) | `[50.3, 31.8, 254.3, 209.0]` |

  Both lie fully inside the 300×300 viewBox.

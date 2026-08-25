# Mechanical — Wing Structure

Physical design of the wing structure — the frame the electronics mount into. Kept separate
from `boards/` (electrical build), `feather/` (physical feather templating), and `docs/`
(shared electrical pinouts).

| Area | Status | Scope |
|------|--------|-------|
| [Structural](structural/) | ideation | Wing frame/skeleton — spars, ribs, mounts, harness routing, body attachment |

## Conventions

- One folder per area, each with a `README.md` (scope + open questions).
- Mechanical parts reference the electrical build — e.g. frame mounts match the power-hub and
  controller layout in [boards/README.md](../boards/README.md).
- Status mirrors the [boards doc](../boards/README.md): `ideation` · `design` · `ready` ·
  `blocked`.
- CAD/geometry artifacts (STEP, FreeCAD, DXF, STL) live in their area folder alongside
  the notes.

## Adding an area

Create `mechanical/<area>/` with a `README.md` and link it in the table above.

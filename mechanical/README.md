# Mechanical

Physical design of the wings — the structure the PCBs mount into and the feather geometry
that carries and diffuses the light. Kept separate from `boards/` (electrical) and `docs/`
(shared electrical pinouts).

| Area | Status | Scope |
|------|--------|-------|
| [Structural](structural/) | ideation | Wing frame/skeleton — spars, ribs, mounts, harness routing, body attachment |
| [Feather](feather/) | ideation | Physical feather shapes — geometry, diffuser, LED-board mounting |

## Conventions

- One folder per area, each with a `README.md` (scope + open questions).
- Mechanical parts reference the boards they host — e.g. the ~70 physical feather shapes
  match the `boards/led-segment/` parameterization (length + bend points).
- "Feather" here means the *physical* feather geometry, distinct from the electrical
  `boards/led-segment/` feather *board*.
- Status mirrors `boards/`: `ideation` · `design` · `ready` · `blocked`.
- CAD/geometry artifacts (STEP, FreeCAD, DXF, STL) live in their area folder alongside
  the notes.

## Adding an area

Create `mechanical/<area>/` with a `README.md` and link it in the table above.

# Plan — replace the `PAGES` manifest with section classes

**Scope:** `make_logical_pages.py` only. Script 2 and the SVG sources are
untouched, and the generated logical pages must come out **byte-identical**.
This is a pure restructuring of how a page is declared and laid out.

---

## 0. Terminology

A manifest entry is **not** a page: some entries emit several pages
(`MirroredWholePage` emits two — right, then left). So neither the entry nor
the manifest is called a "page".

| name | means |
|---|---|
| `Section` | one manifest entry; owns a layout; emits **one or more** logical pages |
| `Page` | one *built* logical page (title, content, w, h) — one `page-NNN.svg` |
| `SECTIONS` | the ordered manifest |
| `Context` | the built fragments + source items a section lays out |

Pages emitted per kind, stated on the class and asserted in tests:

| section kind | pages emitted |
|---|---|
| `Cover` | 1 |
| `MirroredPairs` | 1 |
| `MirroredPairsRot90` | 1 |
| `AlignmentGuides` | 1 |
| `MirroredWholePage` | **2** — right, then left |

(A kind's *name* describes the drawing and its layout. How many pages it
emits is a property of the section, not something to infer from the name.)

---

## 1. The smells

`PAGES` is a list of lists of item specs. Both the spec format *and* the page
behaviour are encoded in positional tuples and literal names:

| # | where | smell |
|---|---|---|
| 1 | `PAGES` (64–85), `normalize_item` (430–438) | `("S1", 90)` / `("S3", 0, 10, 20)` — positional; arity inferred by `len(spec) >= 4`; the meaning is discoverable only from a comment |
| 2 | `main()` line 542 | `if len(specs) == 1 and specs[0][0] == "outline-toplines":` — the "expand into right + left pages" rule lives in the loop, keyed on a literal name |
| 2b | line 527, `placement_halves` (393–394), line 531 | the same name hard-coded three more times: the precomputed `halves`, the page titles, and the `expected` set |
| 3 | `layout_group` line 455 | `pad = TOP_LINE_PAD if name.endswith("-topline") else PAD` — a hidden name-suffix rule |

The consequence: to know what a `PAGES` entry *does*, you have to read the
loop in `main()`, `normalize_item`, `layout_group`, and a comment — four
places, none of which is the config.

---

## 2. Design

Each manifest entry becomes an object that **owns its layout** and returns the
pages it contributes. One interface, one shared layout base, then one class per
domain concept.

```python
@dataclass(frozen=True)
class Page:
    """One built logical page."""
    title: str
    content: str
    w: float
    h: float


@dataclass(frozen=True)
class Context:
    """What a section needs in order to lay itself out."""
    frags: dict     # name -> (built fragment, w, h)
    raw: dict       # name -> source Item (needed by MirroredWholePage)


class Section(ABC):
    """One entry in SECTIONS: owns a layout, emits one or more logical pages."""

    @abstractmethod
    def pages(self, ctx: Context) -> list[Page]: ...


class Shelf(Section):
    """Items placed left-to-right, wrapping at MAX_WIDTH. The one shared layout."""
    rotate = 0.0     # subclass knob
    pad    = PAD     # subclass knob

    def __init__(self, *items):
        self.items = tuple(items)

    def pages(self, ctx):
        content, w, h = shelf(self.items, ctx.frags, self.rotate, self.pad)
        return [Page("/".join(self.items), content, w, h)]


class MirroredPairs(Shelf):
    """Feather pairs, side by side. Emits 1 page."""


class MirroredPairsRot90(Shelf):
    """Feather pairs rotated 90 deg, so an oversized pair fits one sheet.
    Emits 1 page."""
    rotate = 90.0


class AlignmentGuides(Shelf):
    """The *-topline strip: wider spacing between the guides. Emits 1 page."""
    pad = TOP_LINE_PAD


class MirroredWholePage(Section):
    """A whole-wing drawing. Emits 2 pages: right, then left."""
    def __init__(self, item):
        self.item = item

    def pages(self, ctx):
        return placement_halves(ctx.raw[self.item])


class Cover(Section):
    """The calibration cover. Emits 1 page."""
    def pages(self, ctx):
        return [cover_page()]
```

### The manifest

```python
SECTIONS = [
    Cover(),
    MirroredPairs("P1"), MirroredPairs("P2"), MirroredPairs("P3"),
    MirroredPairs("P4"), MirroredPairs("P5"),
    MirroredPairsRot90("S1"), MirroredPairsRot90("S2"),
    MirroredPairs("S3"), MirroredPairs("S4"), MirroredPairs("B1"),
    MirroredPairsRot90("B2"), MirroredPairsRot90("B3"),
    MirroredPairs("A1", "A2", "A3"),
    MirroredPairs("PC1", "PC2"),
    MirroredPairs("SC1", "SC2"), MirroredPairs("SC3"), MirroredPairs("SC4"),
    MirroredPairs("MC1", "MC2"), MirroredPairs("MC3", "MC4"),
    MirroredPairs("LC1", "LC2", "LC3"),
    MirroredWholePage("outline-toplines"),
    # Print order for the guides strip (deliberately not TOPLINES' read order).
    AlignmentGuides("A-topline", "PC-topline", "SC-topline", "LC-topline",
                    "MC-topline", "B-topline", "P-topline", "S-topline"),
]
```

Two ordering traps, both caught by the byte-identical test:

- **Section order.** `MirroredWholePage("outline-toplines")` comes *before*
  `AlignmentGuides(...)`, matching the current output (its two pages are
  22–23, the guides strip is 24).
- **`TOPLINES` is not the print order.** The read list is
  `A, B, LC, MC, P, PC, S, SC`; the strip prints
  `A, PC, SC, LC, MC, B, P, S`. The manifest therefore names the guides
  explicitly rather than splatting `TOPLINES`.

`main()` collapses to one homogeneous loop — no name sniffing anywhere:

```python
ctx = Context(frags=..., raw=...)
pages = [page for section in SECTIONS for page in section.pages(ctx)]
```

### Where the manifest lives

`SECTIONS` is built by instantiating classes, so the classes must be defined
before it. The manifest therefore moves from the top of the file to just below
the class definitions, and the top-of-file config comment points at it.

### Why classes rather than a string→function registry

| | string registry | classes |
|---|---|---|
| typo in a kind | runtime lookup failure | `NameError` at import |
| adding a kind | edit the registry **and** the config | add a class |
| toplines special case | a dict entry plus a suffix rule | `AlignmentGuides.pad = TOP_LINE_PAD` |
| parameters | none — the name is the whole API | real constructor args (`MirroredPairs("A1", "A2", "A3")`) |
| layout logic | five free functions | co-located with the kind it serves |
| pages emitted | invisible | on the class, in its docstring |

`rotate` / `pad` are class attributes, not parameters, because a rotation *is*
a kind here (`MirroredPairsRot90`) rather than an option on a generic layout.

---

## 3. What moves

| current | becomes |
|---|---|
| `normalize_item` (430–438) + the tuple docs (64–72) | **deleted** — items are plain names |
| `layout_group` (441–467) | `shelf(names, frags, rotate, pad)` — the shared layout body |
| `pad = TOP_LINE_PAD if name.endswith("-topline")` (455) | `AlignmentGuides.pad` |
| `if len(specs) == 1 and specs[0][0] == "outline-toplines"` (542) | **deleted** — `MirroredWholePage("outline-toplines")` |
| `halves = placement_halves(t)` precomputed in `main()` (527) | built on demand by `MirroredWholePage.pages` |
| literal titles `"outline-toplines-right"` / `"-left"` (393–394) | derived: `f"{item.name}-right"` / `"-left"` |
| `expected = set(FEATHERS) | set(TOPLINES) | {"outline-toplines"}` (531) | `expected = set(frags)` — the items actually read |
| `pages = [cover_page()] + …` (539) | `Cover()` is the first manifest entry |
| `(title, content, w, h)` tuples through `page_svg` / the print loop | the `Page` dataclass |

Two small types carry data instead of bare tuples: `Page` (built output) and
`Context` (section input).

`raw` exists because `MirroredWholePage` rebuilds its left/right halves from
the source `Item.body`, not from the built pair fragment.

Explicit x/y placement is **dropped** — nothing in the manifest currently uses
it, and `shelf()` keeps the internal `x`/`y` it needs.

---

## 4. Validation

Kept, and tightened:

- Every item appears exactly once, and the manifest covers exactly the items read.
- `MirroredWholePage` asserts it was given exactly one item.
- `Section.pages` is abstract, so a new kind cannot silently do nothing.
- Unchanged: mirror check, `verify_body`, cover-first ordering.

---

## 5. Acceptance test

The refactor must not change a single byte of output.

1. Before touching code: run `make_logical_pages.py` and hash
   `logical-pages/page-*.svg` → baseline.
2. After: re-run and hash again; the two hash sets must be **identical**.
3. `pages_to_pdf.py` → still **29 sheets**, tiling structural check OK,
   scale check OK.

Then commit the implementation separately from the plan.

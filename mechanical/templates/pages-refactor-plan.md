# Plan — give `PAGES` page-kind classes

**Scope:** `make_logical_pages.py` only. Script 2 and the SVG sources are
untouched, and the generated logical pages must come out **byte-identical**.
This is a pure restructuring of how a page is declared and laid out.

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

Each entry in `PAGES` becomes an object that **owns its layout**. One
interface, one shared layout base, then one class per domain concept.

```python
class PageSpec(ABC):
    """One entry in PAGES: a logical page, or a set of logical pages."""
    @abstractmethod
    def build(self, ctx: BuildContext) -> list[Built]: ...


class ShelfPage(PageSpec):
    """Items placed left-to-right, wrapping at MAX_WIDTH. The one shared layout."""
    rotate = 0.0     # subclass knob
    pad    = PAD     # subclass knob

    def __init__(self, *items):
        self.items = tuple(items)

    def build(self, ctx):
        content, w, h = shelf(self.items, ctx.frags, self.rotate, self.pad)
        return [Built("/".join(self.items), content, w, h)]


class MirroredPairs(ShelfPage):
    """Feather pairs, side by side."""


class MirroredPairsRot90(ShelfPage):
    """Feather pairs rotated 90 deg, so an oversized pair fits one sheet."""
    rotate = 90.0


class AlignmentGuides(ShelfPage):
    """The *-topline strip: wider spacing between the guides."""
    pad = TOP_LINE_PAD


class MirroredWholePage(PageSpec):
    """A whole-wing drawing: one item -> a right page plus a left page."""
    def __init__(self, item):
        self.item = item

    def build(self, ctx):
        return placement_halves(ctx.raw[self.item])     # two pages


class CoverPage(PageSpec):
    def build(self, ctx):
        return [cover_page()]
```

### The new `PAGES`

```python
PAGES = [
    CoverPage(),
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
    AlignmentGuides(*TOPLINES),
    MirroredWholePage("outline-toplines"),
]
```

`main()` collapses to one homogeneous loop — no name sniffing anywhere:

```python
ctx = BuildContext(frags=..., raw=...)
pages = [p for spec in PAGES for p in spec.build(ctx)]
```

### Why classes rather than a string→function registry

| | string registry | classes |
|---|---|---|
| typo in a kind | runtime lookup failure | `NameError` at import |
| adding a kind | edit the registry **and** the config | add a class |
| toplines special case | a dict entry plus a suffix rule | `AlignmentGuides.pad = TOP_LINE_PAD` |
| parameters | none — the name is the whole API | real constructor args (`MirroredPairs("A1", "A2", "A3")`) |
| layout logic | five free functions | co-located with the kind it serves |

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
| `halves = placement_halves(t)` precomputed in `main()` (527) | built on demand by `MirroredWholePage.build` |
| literal titles `"outline-toplines-right"` / `"-left"` (393–394) | derived: `f"{item.name}-right"` / `"-left"` |
| `expected = set(FEATHERS) | set(TOPLINES) | {"outline-toplines"}` (531) | `expected = set(frags)` — the items actually read |
| `pages = [cover_page()] + …` (539) | `CoverPage()` is the first manifest entry |
| `(title, content, w, h)` tuples through `page_svg` / the print loop | a `Built` dataclass |

Two small types are introduced to carry data instead of bare tuples:

```python
@dataclass(frozen=True)
class Built:
    title: str
    content: str
    w: float
    h: float

@dataclass(frozen=True)
class BuildContext:
    frags: dict[str, tuple[str, float, float]]   # name -> (built fragment, w, h)
    raw:   dict[str, Item]                       # name -> source Item
```

`raw` exists because `MirroredWholePage` rebuilds its left/right halves from
the source `Item.body`, not from the built pair fragment.

Explicit x/y placement is **dropped** — nothing in `PAGES` currently uses it,
and `shelf()` keeps the internal `x`/`y` it needs.

---

## 4. Validation

Kept, and tightened:

- Every item appears exactly once, and `PAGES` covers exactly the items read.
- `MirroredWholePage` asserts it was given exactly one item.
- `PageSpec.build` is abstract, so a new kind cannot silently do nothing.
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

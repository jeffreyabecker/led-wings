# Plan: `tile_sheets.py` changes beyond the move

**Status:** proposed, not executed.
**Scope:** the behaviour changes the tiler needs for the new `templates/` layout, plus the fixes
required to re-tile safely. Moving the script to `templates/tile_sheets.py` is covered by
[`plans/templates-reorg.md`](templates-reorg.md) and is not repeated here.

Line numbers are deliberately avoided: the working copy was being edited while this was written
(1130 → 992 lines within minutes) and the facts below were re-verified against the later state.
Identifiers (`run`, `emit_multipage_svg`, `parse_args`, `_URI_SAFE`) are stable.

## 1. Sheet references must become relative (blocking)

`run()` builds the reference to the source document as:

```python
href = quote(os.path.basename(in_path), safe=_URI_SAFE)
```

with the comment "Sheets are referenced relative to the output file (assumed co-located)". Under the
new layout that assumption is false — the print document lives three levels below its master. Change
it to a relative path computed from the output directory:

```python
rel = os.path.relpath(in_path, start=os.path.dirname(out_path)).replace(os.sep, '/')
href = quote(rel, safe=_URI_SAFE)
```

Two details that matter:
- `os.sep` must be normalised to `/`; on Windows `relpath` returns backslashes and the href would be
  malformed.
- `_URI_SAFE` already contains `/` and `.`, so `../../../feathers/sheets.svg` survives quoting intact.

Internal references (`#clip`, `#crop-ticks`) are unaffected — only the sheet href changes.

## 2. Output location and naming

`run()` currently defaults the output to `<input>-multipage.svg` beside the input, and the usage text
documents that default. The name is retired and the location can no longer be inferred (the master
and its print documents live in different trees), so:

- **Require `--out`** and fail with a clear message when it is missing. (Alternative: keep an
  optional default of `<input stem>-print.svg` beside the input, accepting that callers must pass
  `--out` anyway for the real tree.)
- **Create the output directory** if needed (`os.makedirs(os.path.dirname(out_path), exist_ok=True)`),
  or fail explicitly — today a missing directory surfaces as a bare `FileNotFoundError`.
- `--whatif` should print the path it would write, as it already does, and additionally the resolved
  href (see §6).

## 3. `sodipodi:docname` lies

`emit_multipage_svg(..., doc_name: str | None = None, ...)` falls back to a hardcoded
`'sheets-multipage.svg'`, and `run()` never passes the argument — so every generated document claims
to be that file. Pass the real name:

```python
svg = emit_multipage_svg(pages, style_css, doc_name=os.path.basename(out_path), gap=gap)
```

## 4. Stamp the tiling parameters into the output

A print document currently records nothing about how it was produced: `print-8_5x11.svg` pins the
paper, but not the safe area, overlap, gap, source revision or page count — and those change the
output. Emit a provenance comment next to the Inkscape header comment:

```
<!-- tiled by tile_sheets.py: source=../../../feathers/sheets.svg paper=letter trim=215.9x279.4mm
     safe=205.9x269.4mm overlap=12mm gap=10mm pages=28 orientation=per-sheet -->
```

Recording the `--paper` token as well as the resolved millimetres keeps the stamp readable and lets a
later check confirm the table entry has not drifted.

Keep it before `<svg>` so it cannot interfere with the `<defs>` marker rewrite in §5. This is what
makes `targets/home/AGENTS.md`'s commands checkable against a shipped file.

## 5. The defs insertion fails silently

`run()` appends the shared clip paths and crop-ticks to the emitted document with a literal
replacement:

```python
svg = svg.replace('<defs\n     id="defs1" />', '<defs\n     id="defs1">\n' + '\n'.join(defs) + '\n    </defs>')
```

If that exact text ever changes in the emitter (indentation, attribute order, a self-closing form),
the replacement is a no-op and the document silently loses its clip paths and crop ticks while still
being written. Assert that the marker was found:

```python
marker = '<defs\n     id="defs1" />'
if defs and marker not in svg:
    raise RuntimeError('defs marker not found; shared clip/crop defs were not inserted')
```

Better still, have `emit_multipage_svg` accept the defs and render them itself, removing the
string surgery.

## 6. CLI: paper names instead of millimetres

The interface should speak paper names, not dimensions. Replace the leading size positionals
(`<trimWxH> <safeWxH>`) with a required `--paper <name>`, and turn the remaining positionals into
flags:

```
python tile_sheets.py <sheets.svg> --paper letter [--margin 5] [--overlap 12] [--gap 10] --out <path> [--whatif]
```

| `--paper` | trim (mm) | safe area at the default margin |
|---|---|---|
| `letter` | 215.9 × 279.4 | 205.9 × 269.4 |
| `legal` | 215.9 × 355.6 | 205.9 × 345.6 |
| `tabloid` | 279.4 × 431.8 | 269.4 × 421.8 |
| `a3` | 297 × 420 | 287 × 410 |
| `a4` | 210 × 297 | 200 × 287 |
| `a5` | 148 × 210 | 138 × 200 |

- **Only trim is tabulated.** `--margin MM` (default 5, i.e. 5 mm per edge) derives the safe area, which
  reproduces today's letter numbers exactly (215.9 → 205.9, 279.4 → 269.4). `--safe WxH` overrides the
  derivation for stock whose printable area is not symmetric.
- `--paper` is required, and an unknown name is a usage error that prints the table. An optional
  `--list-papers` prints the table and exits 0.
- `--overlap` and `--gap` carry today's defaults (12 mm, 10 mm) and keep the existing `dist()` forms
  (`12`, `0.5in`).
- **Escape hatch**: keep the explicit sizes available as `--size WxH` (with `--safe WxH`) so unusual
  stock still works. `size()` and `dist()` already exist; this is argument routing, not new parsing.
- The chosen token is the paper's public name: it belongs in the provenance stamp (§4), in the
  `--whatif` echo, and in the filename the caller composes.

> **Naming coupling to settle.** `plans/templates-reorg.md` currently names the outputs
> `print-8_5x11.svg` / `print-a4.svg`. With named papers the flag value and the filename should agree,
> so those become `print-letter.svg` / `print-a4.svg` — or the token table uses dimension names. Pick
> one and both documents follow it.

## 7. Docstring and usage refresh

Still describing the old world: the module docstring and `USAGE` say `<sheets.svg>`,
"`--out` … (default: `<input>-multipage.svg` beside the input)", the size positionals
`[trimWxH] [safeWxH]`, and pages laid out "side by side in a single Inkscape multipage document".
Update to the new layout, the required `--out`, and the `--paper` grammar from §6; the `sheets.svg`
fragment in the usage line should read `<content>/sheets.svg`.

## 8. Optional robustness: sheet discovery

`has_sheet_class()` matches the substring `"sheet"` anywhere in the class attribute, and its own
docstring warns that `class="worksheet"` or `class="sheets"` would match. The sheets documents now
carry more generated groups (`sheet-<name>-half`, `-labels`, `-mirror`, `-reg`, and the
`sheet-bounds` rect), all of which happen to be safe today because they are either not `<g>`
elements or carry no class containing "sheet". Tighten to a token test anyway:

```python
return 'sheet' in (el.get('class') or '').split()
```

## 9. Verification

- `--whatif` for both masters, both papers. At `--paper letter` the page counts must match the
  committed documents: **28** for feathers, **19** for alignment.
- An unknown `--paper` value exits non-zero and prints the table; `--paper letter` and
  `--margin 5` resolve to the same trim/safe as today's hardcoded 215.9×279.4 / 205.9×269.4.
- Inspect one generated page and confirm the sheet href is `../../../feathers/sheets.svg#sheet-P1`
  and resolves from `templates/targets/home/feathers/`.
- Open a generated document in Inkscape: content renders (the earlier blank-page incident was a
  missing sibling file, and this change makes the reference path deeper).
- Confirm each shared def appears exactly once per geometry and that no id repeats. A mid-edit
  working copy briefly had the `shared_ticks` loop duplicated four times, which would have emitted
  each crop-ticks def four times; that is already fixed in the current copy, and this check keeps it
  fixed.
- Confirm the provenance comment matches the parameters in `targets/home/AGENTS.md`.

## 10. Out of scope

- Inlining sheet content instead of `<use>` (decided against: print documents stay thin references).
- The page-orientation policy in `choose_layout`, overlap/gap defaults, and paper sizes beyond the
  table in §6 (add entries as needed; no other code path should hardcode a size).
- Any change to what the sheets documents contain — the tiler reads them, it does not author them.

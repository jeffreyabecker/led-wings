# Investigations

Non-board design investigations — architecture, part-selection, and cost questions that
don't yet have their own board folder. Each investigation keeps a `README.md` (scope +
decision context) plus one or more analysis notes.

| Investigation | Status | Question |
|---------------|--------|----------|
| [Battery](battery/) | investigation | Which 12 V battery (chemistry + size) powers 8 h @ 20 % for mobility? |
| [Power delivery](power-delivery/) | investigation | How is 12 V stepped to 5 V and delivered to ~140 SK9822-EC20 feathers? |

## Conventions

- Status: `investigation` (in progress) · `recommended` · `rejected` · `superseded`.
- Cite the source for every spec or price; mark estimates `⚠️` vs confirmed `✅`.
- A recommendation here is an *input* to a board's `design-readiness.md`, not a locked
  decision. Locking decisions still happens in the board folders.

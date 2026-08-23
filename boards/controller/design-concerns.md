# Controller Board — Design Concerns

External, one per strand. Drives DATA + CLK into the first segment's `J_IN`.

- **Level shift:** controller logic (3.3 V) → 5 V; SK9822 expects 5 V logic.
- **Series R (33–100 Ω)** on DATA + CLK output — damp the controller→first-board cable.
- **Fuse:** size for one strand (≈ N segments × current); one per strand / injection feed.
- **ESD/TVS** on DATA, CLK, VCC at the output.
- **Outputs:** how many strands per controller?

See [connector pinout](../../docs/connector-pinout.md) · [parts](selected-parts.md).

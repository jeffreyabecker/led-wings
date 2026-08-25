# Wings — Project Plan

## Phase 1 — Mechanical mockup *(this round)*
Knock out all templates and fabricate a first wearable mockup.

**Deliver:**
- Rigid structure + attachment mechanism fully designed
- All feather templates finalized, labeled, scanned in
- A complete wearable mockup

**Understand:**
- How thick feathers are allowed to be
- How much space is available for wiring and power

## Phase 2 — EVA foam trials
**Understand:**
- How to texture the feathers
- How stacking affects lighting
- How much of each feather needs to be lighted
- How to assemble a feather; which feathers are doubled vs one-sided
- Whether front and back both need lighting

**Deliver:** model feathers in varying sizes —
- Untextured packing foam with lighting
- Non-diffusion EVA foam with texturing
- Diffusion EVA foam with texturing

## Phase 3 — Electronics
**Decisions locked (per `boards/`):**
- Off-the-shelf build — **no custom PCBs** (custom boards deferred to "if we build more than one")
- Split power/data: 12 V bus → MP1584EN buck hubs (≤ ~2 A per cluster) → 5 V per-feather strip chunks; data daisy-chains, one per wing, from a Pixelblaze V3 + level shifter
- Feathers = cut SK9822 96 LED/m chunks with JST-PNI pigtails; settled COTS BOM in `boards/parts-list.md`

**Understand/confirm:**
- Signal + power wiring harness requirements and topology
- Overall power requirements for the system
- Battery sizing needs (12 V chemistry; see `investigations/battery`) — grounded by **measuring the system's actual power draw** during this phase

**Deliver:**
- Hand-assembled preliminary wiring harness for at least one full wing, run off a power supply or battery
- An off-the-shelf battery specced for ≥6 hours runtime at full brightness

*Software phase dropped — the LED control software already manages power correctly (in-strip power management).*

## Phase 4 — Preliminary build
Build the first complete version — structure, feathers, harness, and electronics all together.

**By this phase we have enough info to decide where the battery goes** (placement/mounting on the frame).

## Phase 5 — Final assembly
Full assembly of the finished piece — everything mounted, wired, and tested as a wearable.

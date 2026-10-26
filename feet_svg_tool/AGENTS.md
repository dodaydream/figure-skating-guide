# AGENTS.md — Figure Skating Quick References (handover)

You are picking up an ongoing project for **Sophie**, the project owner. Read this whole file before touching anything — most of it is her explicit decisions, and she notices drift immediately. When her instructions in conversation conflict with this file, her latest word wins; update this file to match.

## What the project is

Sophie is learning figure skating from *The Complete Book of Figure Skating* by Carole Shulman. The project turns the book, chapter by chapter, into **rink-ready quick-reference web pages** — one page per topic, designed to be skimmed on a phone at the rink. Each page organizes every skill the same way: **body posture, foot posture, blades used, tips**.

The four finished pages (hosted web artifacts, one page each):

| Page | Artifact slug | Book source |
|---|---|---|
| Stops | `figure-skating-stops-quick-reference` | Ch. 4, pp. 42–45 |
| Stroking | `figure-skating-stroking-quick-reference` | Ch. 4, pp. 44–48 |
| Edges & Crossovers | `figure-skating-edges-crossovers-quick-reference` | Ch. 4, pp. 49–56 |
| Turns & Footwork | `figure-skating-turns-footwork-quick-reference` | Ch. 6, pp. 69–94 |

**One page per artifact is a hard decision.** A combined multi-page version was built once and rejected (24.3 MB, too heavy). Do not merge the pages.

Sophie hosts the pages herself in her GitHub repo **`dodaydream/figure-skating-guide`**. Deliveries to her are a zip (`figure-skating-guide.zip`: root folder `figure-skating-guide/` with `README.md` and one folder per page — `stops/`, `stroking/`, `edges-crossovers/`, `turns-footwork/` — each holding `index.html` + `assets/`). You have no GitHub sign-in; she pushes the zip contents herself.

**Not yet built** (do not start unprompted): Ch. 5 "Freestyle Moves" and Ch. 7 "Spins" pages.

## Sources

- The book PDF (owner-provided). If she shares it with you: **PDF page = book page + 16** (book p. 42 = PDF p. 58). `pdftotext` / `pdftoppm` / Python PIL are available; PyMuPDF is not. 250-dpi renders are slow (~10–30 s/page).
- Diagram style model: https://skating.tw/start/basics — clean, text-free, top-view feet diagrams. Terminology note: **sculling = swizzle** (same move; the book says "sculling", modern rinks say "swizzle"). Snowplow = 八字煞， swizzle = 葫蘆， backward wiggle/snake = 蛇行.
- Each page's **cheat sheet** (Markdown, see file map) is the content source the page was built from. Keep cheat sheet and page in sync: edit the cheat sheet first, then the page.

## File map (working files)

```
your_files/
  skating-stops/     feet_specs.json · stopping-techniques-cheat-sheet.md · feet_svg_tool.py · fig*.png (book crops)
  skating-stroking/  stroking_specs.json · stroking-skills-cheat-sheet.md
  skating-edges/     edges_specs.json · edges_keyframes_specs.json · edges-crossovers-cheat-sheet.md · fig*.png
  skating-turns/     turns_specs.json (retired flat singles) · turns_keyframes_specs.json · turns-footwork-cheat-sheet.md · fig*.png
  figure-skating-guide.zip   latest GitHub delivery
```

- `skating-stops/` and `skating-stroking/` diagrams are **inlined** in their pages (no SVG asset files).
- `skating-edges/` single edge diagrams are inlined; its keyframe panels are **asset files**. `skating-turns/` keyframe panels are **asset files**.
- Artifact page sources live under `workspace/ts-spaces/<slug>/` (`index.html` + `assets/`). Never hand-edit them — pages change only through the artifact build/edit flow. They are read (copied) only when packing the zip, after the artifacts are final.

## The feet-diagram generator

`skating-stops/feet_svg_tool.py` (v2, Python 3, stdlib only; `cairosvg` needed only for `--preview`). All diagrams are generated from JSON specs — **never hand-draw or hand-edit an SVG**; edit the spec and regenerate.

```bash
python3 feet_svg_tool.py --specs <specs.json> --all            # regenerate everything in a specs file
python3 feet_svg_tool.py --specs <specs.json> <name>           # one flat spec / one move (panels + strip)
python3 feet_svg_tool.py --specs <specs.json> <move>-k2       # just one stage panel
python3 feet_svg_tool.py --specs <specs.json> --all --preview  # + PNG strips into previews/ next to the specs
python3 feet_svg_tool.py --specs <specs.json> --check          # validate only
```

Run `python3 feet_svg_tool.py --help` for the full spec reference. Essentials:

- **Panel**: 300 wide, y grows downward, "up" on the page = direction of travel. Coordinates are panel-local.
- **Boot**: `{x, y, angle, len, ghost}` — centre position; `angle` 0 = toe straight up, positive = clockwise (toe swings right); the blade line extends 6 units past each end of the boot. `ghost: true` draws a dashed boot.
- **Flat spec** (one panel): `boots`, `dots` (red pressure points), `arrows`, `paths` (e.g. spray), `tracks` (ice-print curves), `travel` (direction arrow), `bare: true` = no title block, `height` (300 for page diagrams).
- **Move spec** (keyframed, `"move": true`): the ice-print `track` is written **once, in full**; shared fields (`len`, `travel`, `arrows`) are defined once; each entry in `stages` sets `track_until` (fraction of the total print length skated so far, 0–1) and the tool cuts the path at that arc length automatically. A stage may override with explicit `tracks`; `travel: null` on a stage suppresses the shared arrow; stage `arrows` add to shared ones.
- **Outputs**: `<name>-feet.svg` per panel, plus `<move>-strip.svg` (panels side by side, stage labels underneath) per move — written next to the specs file.
- **Validation** runs on every generation: off-panel boots, boot pairs overlapping >~20% of the smaller boot, off-panel dots, non-monotonic `track_until`. Warnings are heuristics — feet legitimately crowd at steps and crosses; judge visually.

## Diagram rules (Sophie's, non-negotiable)

1. **Feet-and-blades, top view only.** No legend, no front/side body diagrams — the original book photo covers the body. (Style model: skating.tw.)
2. **Dashed boot = lifted free foot.** Solid boot = on the ice. State this in each page's diagram-reading note.
3. **Physics rule — the one Sophie checks first:** a gliding boot must **sit on its pale-blue ice-print trail with its blade parallel to the trail (tangent) at that point**, and the free foot is drawn **parallel to the skating foot**. Boots floating off the print or angled across it are the project's most-recurring error — a full audit in Oct 2026 found glide boots up to ~90° off their trails. Deliberate exceptions, which are *not* errors: mid-turn boots in stage 2 of the one-foot turns (the turn is happening), the crossing foot in a crossover's stage 2, pushing feet at ~45° in stroking, and braking poses in stops.
4. **QA method that works:** after regenerating, numerically check each on-ice glide boot against its trail (distance from boot centre to the curve; angle between boot axis and the curve's tangent at the nearest point — glide boots should be ~0 px / within a few degrees), then render the strips and **look at them**. Do both; each method has caught errors the other missed.
5. **Keyframed 3-stage strips** (entry / key moment / exit) for turns, change of edge, and crossovers. Sustained glides keep single diagrams.
6. **Arrows:** single diagrams keep their red travel arrows. Keyframed strips do **not** mark travel direction (stage order shows it) — **except Mohawks**, which carry a red direction arrow in each stage: a Mohawk reverses forward→backward on one smooth arc, so the print alone doesn't show the direction change.
7. **Red dot** = the pressure / working-edge point on the skating boot. On edge glides it sits on the side toward the curve's centre (that's the edge that bites and makes the curve).
8. **Snowplow is an upside-down V (∧)**: toes turned **in** toward each other at the front, heels pushed out, braking on inside edges. The one-foot snowplow is half of that wedge (braking foot toe-in ~45°, slightly ahead). The T-stop is an upside-down T: glide foot straight, drag foot perpendicular behind it.
9. **Trails are ground truth from the book's print figures** (e.g. Fig. 6.1 three-turn print = two lobes curving the same way with an inward cusp; Fig. 6.11 bracket = one arc with an outward hook; Figs. 6.13/6.14 counter/rocker = same-sense tangent circles differing only in cusp shape). For crossover-class moves, derive boot positions *and* angles from one circle so the geometry can't contradict itself.

## Video rules (Sophie's, non-negotiable)

- Videos are **embedded YouTube players** (responsive 16:9 iframe, `https://www.youtube-nocookie.com/embed/<ID>`, `loading="lazy"`), with a "▶ Watch: …" caption link under each player.
- **Single-technique breakdowns only**: a dedicated tutorial on ONE technique. No multi-skill lessons, class compilations, or test-pattern demos. (Two disclosed exceptions already on the pages: the one-foot snowplow has no dedicated figure-skating breakdown, so it uses a snowplow lesson that progresses to it; the back-outside-edges card uses a video covering both back edges.)
- **Channel preference**: Coach Mary Figure Skating first; then other high-quality single-technique channels already used: Coach Julia, Coach Michelle Hong, Style Skating, Ice Coach Online, Ice Edge Academy, Coach Ashleigh.
- **YouTube IDs must come from an actual lookup, never guessed.** If a video turns out to be embedding-disabled, flip that card back to a thumbnail link.
- Build-sandbox caveat: external network is blocked during page audits, so players render as black rectangles there — that's a pass if no error state shows. Playback can only be confirmed by opening the page live.

## Page design conventions

Ice palette (deep navy, pale ice blue, one warm accent), light/dark friendly, fully self-contained pages. Every page: a "golden rule"-style callout, a "Which skill when?" picker with anchor links, a diagram-reading note, skill cards with **Body / Feet / Blade** rows + **Tips**, the **original book photo** where the book has one (captioned with the figure number), a comparison table, and a source footer. Accepted quirk: on narrow phones the comparison table scrolls horizontally inside its own container — by design; *page-level* overflow is a defect.

## Change workflow — order matters

Sophie's standing rule: **always rebuild/sync the artifacts first, then pack the zip. Never pack the zip before the artifact sync is done.**

1. Edit the cheat sheet (text) and/or the specs (diagrams).
2. Regenerate the SVGs; run the numeric tangent audit (rule 4); render previews and visually inspect every changed strip/panel.
3. Sync the affected artifact(s) through the artifact edit flow — asset-file swaps for keyframe panels, inline-SVG swaps where diagrams are inlined. Wait for each build's audit to pass.
4. Spot-verify the artifact sources actually changed (byte-compare a swapped panel; grep the new inline geometry).
5. Only then rebuild `figure-skating-guide.zip` from the artifact sources (`index.html` + `assets/` per page, folder names as above, keep `README.md`), and verify every `assets/…` reference in each `index.html` resolves to a file in the zip.
6. Deliver the zip to Sophie.

## Status snapshot (2026-10-26)

- All four pages are current, including a full diagram-physics correction round (every glide boot re-aligned to its trail; crossovers rebuilt from single circles; backward sculling phase fixed; snake given two wiggle trails; Mohawk direction arrows added). The zip delivered 2026-10-25 matches the artifacts.
- Open item, only if Sophie raises it: the Stroking page's Power Stroking card uses an Ice Edge Academy Short (the only true single-technique tutorial found). Coach Mary's multi-drill power class is the stated fallback if she prefers it despite being multi-drill.
- Retired files you may ignore: `turns_specs.json` flat singles (superseded by keyframes), the flat `cross1`/`cross2`/`edge5` singles in the edges specs (superseded by keyframes).

#!/usr/bin/env python3
"""Feet-diagram SVG generator for the skating reference pages.

Generates "FEET & BLADES · FROM ABOVE" panels (300 wide) from a small
JSON spec, so foot positions can be tweaked by editing numbers instead
of hand-drawing SVG.

Usage:
    python3 feet_svg_tool.py --all               # regenerate everything
    python3 feet_svg_tool.py snowplow            # one flat spec
    python3 feet_svg_tool.py --specs turns_keyframes_specs.json --all
    python3 feet_svg_tool.py --specs turns_keyframes_specs.json turn1-three
                                                 # one move: panels + strip
    python3 feet_svg_tool.py --specs turns_keyframes_specs.json turn1-three-k2
                                                 # just one stage panel
    python3 feet_svg_tool.py --specs <file> --check    # validate only
    python3 feet_svg_tool.py --specs <file> --all --preview
                                                 # + PNG strips in previews/

FLAT SPEC (one panel; coordinates are panel-local, panel is 300 wide,
y grows downward, "up" on the page = direction of travel):
    {
      "snowplow": {
        "travel": {"x": 150, "label": "DIRECTION OF TRAVEL"},
        "boots":  [{"x": 108, "y": 272, "angle": 38, "len": 84},
                   {"x": 192, "y": 272, "angle": -38, "len": 84, "ghost": false}],
        "dots":   [{"x": 101, "y": 298}],                      # red pressure points
        "arrows": [{"x1": 72, "y1": 292, "x2": 32, "y2": 322, "dashed": false}],
        "paths":  [{"d": "M60,230 L28,212", "cls": "spray"}],  # raw extra paths
        "tracks": [{"d": "M...", "cls": "track"}],             # ice-print curves
        "texts":  [{"x": 150, "y": 402, "text": "...", "bold": true, "anchor": "middle"}],
        "bare":   true,          # no panel title (small diagram mode)
        "height": 300            # panel height (default 560)
      }
    }

Boot "angle" rotates the boot around its centre: 0 = pointing straight
ahead (toe up), positive = clockwise (toe swings right). "len" is the
boot length; the blade line extends 6 units past each end. A "ghost"
boot is drawn as a dashed outline (a lifted free foot).
Output file: <spec name>-feet.svg next to the specs file.

MOVE SPEC (a keyframed move: entry / key moment / exit). The ice print
("track") is written ONCE, in full; each stage says how much of it has
been skated via "track_until" (fraction of total print length, 0..1),
and the tool cuts the path at that length automatically -- no more
hand-splitting the curve into per-stage path strings.
    {
      "turn1-three": {
        "move": true,
        "bare": true, "height": 300, "len": 68,     # shared by all stages
        "travel": {"x": 52},                        # shared travel arrow
        "arrows": [],                               # shared extra arrows
        "track": "M74,272 C70,200 94,142 140,118 C164,106 182,116 177,140 ...",
        "stages": [
          {"label": "1 · Entry",    "track_until": 0.38,
           "boots": [...], "dots": [...]},
          {"label": "2 · The turn", "track_until": 0.55,
           "boots": [...], "dots": [...]},
          {"label": "3 · Exit",     "track_until": 1.0,
           "boots": [...], "dots": [...],
           "travel": null,                          # suppress shared arrow
           "arrows": [{"x1": 218, "y1": 232, "x2": 225, "y2": 262}]}
        ]
      }
    }
Stage fields inherit the move's "len" (per-boot default), "travel",
"arrows" (stage arrows are ADDED to shared ones) and "bare"/"height".
A stage may override "tracks" with its own explicit path list (for
moves whose print is re-drawn each stage, e.g. crossovers).
Outputs: <move>-k1-feet.svg ... <move>-kN-feet.svg, plus a combined
<move>-strip.svg (all panels side by side with the stage labels under
each panel) ready to embed as a single figure.

Validation runs on every generation: boots that fall off the panel,
boots overlapping each other by more than ~20% of the smaller boot,
dots outside the panel, and non-monotonic track_until values are
reported as warnings.
"""

import argparse
import json
import math
import os
import re
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL_W = 300

STYLE = """  <defs>
    <marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#d64541"/>
    </marker>
    <style>
      .panel{fill:#ffffff;stroke:#c9d6e4;stroke-width:1.5}
      .ptitle{font-family:'Segoe UI',Arial,sans-serif;font-size:14px;font-weight:700;letter-spacing:2px;fill:#5a718c}
      .lbl{font-family:'Segoe UI',Arial,sans-serif;font-size:13px;fill:#33506e}
      .lblb{font-family:'Segoe UI',Arial,sans-serif;font-size:13px;font-weight:700;fill:#16324f}
      .arr{stroke:#d64541;stroke-width:3;fill:none;marker-end:url(#ah)}
      .dash{stroke:#d64541;stroke-width:2.5;stroke-dasharray:6 5;fill:none;marker-end:url(#ah)}
      .spray{stroke:#7fb2dd;stroke-width:3;stroke-linecap:round}
      .track{stroke:#7fb2dd;stroke-width:3;fill:none;stroke-linecap:round;stroke-linejoin:round}
      .dot{fill:#d64541}
      .ghostboot{fill:none;stroke:#7d93a8;stroke-width:2.5;stroke-dasharray:6 4}
    </style>
  </defs>
"""


# ---------------------------------------------------------------- paths
# Minimal absolute M/L/C path engine: enough to measure arc length and
# cut a path at a fraction of its length.

_TOKEN = re.compile(r"([MLC])|(-?\d*\.?\d+)")


def _fmt(v):
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.1f}"


def _pair(x, y):
    return f"{_fmt(x)},{_fmt(y)}"


def parse_path(d):
    """Return (start_point, [segments]) where a segment is
    ('L', p0, p1) or ('C', p0, c1, c2, p1), points as (x, y) tuples."""
    tokens = []
    for m in _TOKEN.finditer(d):
        if m.group(1):
            tokens.append(m.group(1))
        else:
            tokens.append(float(m.group(2)))
    segs = []
    cur = None
    start = None
    i = 0
    cmd = None
    while i < len(tokens):
        if isinstance(tokens[i], str):
            cmd = tokens[i]
            i += 1
            if cmd == "M":
                cur = (tokens[i], tokens[i + 1])
                start = cur
                i += 2
                cmd = "L"  # implicit lineto after moveto
            continue
        if cmd == "L":
            nxt = (tokens[i], tokens[i + 1])
            segs.append(("L", cur, nxt))
            cur = nxt
            i += 2
        elif cmd == "C":
            c1 = (tokens[i], tokens[i + 1])
            c2 = (tokens[i + 2], tokens[i + 3])
            nxt = (tokens[i + 4], tokens[i + 5])
            segs.append(("C", cur, c1, c2, nxt))
            cur = nxt
            i += 6
        else:
            raise ValueError(f"unsupported path command near token {i} in {d!r}")
    return start, segs


def _cubic(p0, c1, c2, p1, t):
    mt = 1 - t
    x = (mt**3 * p0[0] + 3 * mt * mt * t * c1[0]
         + 3 * mt * t * t * c2[0] + t**3 * p1[0])
    y = (mt**3 * p0[1] + 3 * mt * mt * t * c1[1]
         + 3 * mt * t * t * c2[1] + t**3 * p1[1])
    return (x, y)


def _seg_points(seg, steps=120):
    if seg[0] == "L":
        _, p0, p1 = seg
        return [p0, p1]
    _, p0, c1, c2, p1 = seg
    return [_cubic(p0, c1, c2, p1, j / steps) for j in range(steps + 1)]


def _seg_length(seg):
    pts = _seg_points(seg)
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def _seg_text(seg):
    if seg[0] == "L":
        return f"L{_pair(*seg[2])}"
    return f"C{_pair(*seg[2])} {_pair(*seg[3])} {_pair(*seg[4])}"


def _split_cubic(seg, t):
    """Left part of a cubic segment cut at parameter t (de Casteljau)."""
    _, p0, c1, c2, p1 = seg

    def lerp(a, b):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    q0, q1, q2 = lerp(p0, c1), lerp(c1, c2), lerp(c2, p1)
    r0, r1 = lerp(q0, q1), lerp(q1, q2)
    s = lerp(r0, r1)
    return ("C", p0, q0, r0, s)


def _cut_segment(seg, target_len):
    """Sub-segment covering the first target_len units of seg."""
    pts = _seg_points(seg, steps=400)
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    total = cum[-1]
    if target_len >= total:
        return seg
    if seg[0] == "L":
        t = target_len / total if total else 0.0
        p0, p1 = seg[1], seg[2]
        mid = (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
        return ("L", p0, mid)
    # find t by walking the dense samples
    j = 0
    while j < len(cum) - 1 and cum[j + 1] < target_len:
        j += 1
    span = cum[j + 1] - cum[j] or 1.0
    t = (j + (target_len - cum[j]) / span) / 400.0
    return _split_cubic(seg, t)


def truncate_path(d, frac):
    """The first `frac` (0..1) of path d, by arc length. Cuts landing
    on a segment joint reproduce the original segments verbatim."""
    if frac >= 1.0:
        return d
    if frac <= 0.0:
        start, _ = parse_path(d)
        return f"M{_pair(*start)}"
    start, segs = parse_path(d)
    lengths = [_seg_length(s) for s in segs]
    target = frac * sum(lengths)
    out = [f"M{_pair(*start)}"]
    for seg, seg_len in zip(segs, lengths):
        if target >= seg_len - 0.75:  # whole segment (snap at joints)
            out.append(_seg_text(seg))
            target -= seg_len
            if target <= 0.75:
                break
        else:
            out.append(_seg_text(_cut_segment(seg, target)))
            break
    return " ".join(out)


def truncate_tracks(ds, frac):
    """Cut a list of paths at `frac` of their combined length."""
    if frac >= 1.0:
        return list(ds)
    parsed = [parse_path(d) for d in ds]
    totals = [sum(_seg_length(s) for _, segs in [p] for s in segs)
              for p in parsed]
    target = frac * sum(totals)
    out = []
    for d, tot in zip(ds, totals):
        if tot == 0:
            continue
        if target >= tot - 0.75:
            out.append(d)
            target -= tot
        elif target > 0:
            out.append(truncate_path(d, target / tot))
            target = 0
        else:
            break
    return out


# ---------------------------------------------------------------- panels

def header(height, title):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="{height}" '
        f'viewBox="0 0 300 {height}">',
        STYLE.rstrip(),
        f'  <rect x="0" y="0" width="300" height="{height}" class="panel"/>',
    ]
    if title:
        parts.append(
            '  <text x="150" y="32" text-anchor="middle" class="ptitle">'
            "FEET &amp; BLADES · FROM ABOVE</text>"
        )
    return "\n".join(parts)


def boot_svg(b):
    x, y = b["x"], b["y"]
    angle = b.get("angle", 0)
    length = b.get("len", 84)
    half = length / 2
    blade = half + 6
    transform = f"translate({x},{y})"
    if angle:
        transform += f" rotate({angle})"
    if b.get("ghost"):
        return (
            f'  <g transform="{transform}"><rect x="-13" y="{-half:g}" width="26" '
            f'height="{length}" rx="13" class="ghostboot"/>'
            f'<line x1="0" y1="{-blade:g}" x2="0" y2="{blade:g}" stroke="#7d93a8" '
            f'stroke-width="2.5" stroke-dasharray="5 4"/></g>'
        )
    return (
        f'  <g transform="{transform}"><rect x="-13" y="{-half:g}" width="26" '
        f'height="{length}" rx="13" fill="#2b3440"/>'
        f'<line x1="0" y1="{-blade:g}" x2="0" y2="{blade:g}" stroke="#aeb9c4" '
        f'stroke-width="3"/></g>'
    )


def elements(spec):
    """The drawing elements of one panel (everything except the svg
    wrapper and the panel background/title from header())."""
    bare = spec.get("bare", False)
    out = []
    travel = spec.get("travel")
    if travel:
        x = travel["x"]
        if bare:
            out.append(
                f'  <line x1="{x}" y1="88" x2="{x}" y2="52" class="arr"/>'
            )
        else:
            out.append(
                f'  <line x1="{x}" y1="108" x2="{x}" y2="70" class="arr"/>'
            )
            out.append(
                f'  <text x="{x}" y="60" text-anchor="middle" class="lblb">'
                f'{escape(travel["label"])}</text>'
            )
    for p in spec.get("tracks", []):
        out.append(f'  <path d="{p["d"]}" class="{p.get("cls", "track")}"/>')
    for b in spec.get("boots", []):
        out.append(boot_svg(b))
    for d in spec.get("dots", []):
        out.append(f'  <circle cx="{d["x"]}" cy="{d["y"]}" r="5" class="dot"/>')
    for a in spec.get("arrows", []):
        cls = "dash" if a.get("dashed") else "arr"
        out.append(
            f'  <path d="M{a["x1"]},{a["y1"]} L{a["x2"]},{a["y2"]}" class="{cls}"/>'
        )
    for p in spec.get("paths", []):
        out.append(f'  <path d="{p["d"]}" class="{p["cls"]}"/>')
    for t in spec.get("texts", []):
        cls = "lblb" if t.get("bold") else "lbl"
        anchor = t.get("anchor", "middle")
        anchor_attr = "" if anchor == "start" else f' text-anchor="{anchor}"'
        out.append(
            f'  <text x="{t["x"]}" y="{t["y"]}"{anchor_attr} class="{cls}">'
            f'{escape(t["text"])}</text>'
        )
    return out


def render(spec):
    bare = spec.get("bare", False)
    height = spec.get("height", 560)
    out = [header(height, title=not bare)]
    out.extend(elements(spec))
    out.append("</svg>")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- moves

def expand_stage(move, stage):
    """Materialize one stage of a move into a flat panel spec."""
    flat = {"bare": move.get("bare", True), "height": move.get("height", 300)}
    if "travel" in stage:
        if stage["travel"] is not None:
            flat["travel"] = stage["travel"]
    elif move.get("travel"):
        flat["travel"] = move["travel"]
    if "tracks" in stage:
        flat["tracks"] = stage["tracks"]
    else:
        ds = move.get("tracks") or ([move["track"]] if move.get("track") else [])
        frac = stage.get("track_until", 1.0)
        flat["tracks"] = [{"d": d} for d in truncate_tracks(ds, frac)]
    default_len = move.get("len")
    boots = []
    for b in stage.get("boots", []):
        b = dict(b)
        if default_len is not None:
            b.setdefault("len", default_len)
        boots.append(b)
    flat["boots"] = boots
    if stage.get("dots"):
        flat["dots"] = stage["dots"]
    arrows = list(move.get("arrows", [])) + list(stage.get("arrows", []))
    if arrows:
        flat["arrows"] = arrows
    if stage.get("paths"):
        flat["paths"] = stage["paths"]
    return flat


def render_strip(name, move):
    """All stage panels side by side, labels underneath, one SVG."""
    stages = move["stages"]
    height = move.get("height", 300)
    gap = 16
    label_h = 34
    width = len(stages) * PANEL_W + (len(stages) - 1) * gap
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height + label_h}" viewBox="0 0 {width} {height + label_h}">',
        STYLE.rstrip(),
        f'  <rect x="0" y="0" width="{width}" height="{height + label_h}" '
        'fill="#ffffff"/>',
    ]
    for i, stage in enumerate(stages):
        flat = expand_stage(move, stage)
        x = i * (PANEL_W + gap)
        parts.append(f'  <g transform="translate({x},0)">')
        parts.append(
            f'  <rect x="0" y="0" width="300" height="{height}" class="panel"/>'
        )
        parts.extend("  " + line for line in elements(flat))
        parts.append("  </g>")
        label = stage.get("label", f"{i + 1}")
        parts.append(
            f'  <text x="{x + PANEL_W / 2:g}" y="{height + 23}" '
            f'text-anchor="middle" class="lblb">{escape(label)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------- checks

def _boot_poly(b):
    x, y = b["x"], b["y"]
    half = b.get("len", 84) / 2
    rad = math.radians(b.get("angle", 0))
    cos, sin = math.cos(rad), math.sin(rad)
    pts = []
    for lx, ly in ((-13, -half), (13, -half), (13, half), (-13, half)):
        pts.append((x + lx * cos - ly * sin, y + lx * sin + ly * cos))
    return pts


def _poly_area(poly):
    return abs(sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1])
    )) / 2


def _clip(subject, clip):
    """Sutherland–Hodgman polygon clipping (both convex)."""
    def inside(p, a, b):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0

    def intersect(p1, p2, a, b):
        d1 = (p2[0] - p1[0], p2[1] - p1[1])
        d2 = (b[0] - a[0], b[1] - a[1])
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if den == 0:
            return p1
        t = ((a[0] - p1[0]) * d2[1] - (a[1] - p1[1]) * d2[0]) / den
        return (p1[0] + d1[0] * t, p1[1] + d1[1] * t)

    # ensure clip polygon is counter-clockwise in screen coords (y down):
    # signed area positive with y down means the "inside" test above works
    # when vertices wind clockwise visually; normalize by area sign.
    signed = sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(clip, clip[1:] + clip[:1])
    )
    if signed < 0:
        clip = clip[::-1]
    out = subject
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]
        if not out:
            break
        new = []
        prev = out[-1]
        for cur in out:
            if inside(cur, a, b):
                if not inside(prev, a, b):
                    new.append(intersect(prev, cur, a, b))
                new.append(cur)
            elif inside(prev, a, b):
                new.append(intersect(prev, cur, a, b))
            prev = cur
        out = new
    return out


def check_panel(name, spec):
    """Return a list of warning strings for one flat panel spec."""
    warns = []
    height = spec.get("height", 560)
    polys = []
    for idx, b in enumerate(spec.get("boots", [])):
        poly = _boot_poly(b)
        polys.append(poly)
        for px, py in poly:
            if px < -8 or px > PANEL_W + 8 or py < -8 or py > height + 8:
                warns.append(
                    f"{name}: boot {idx + 1} at ({b['x']},{b['y']}) "
                    f"angle {b.get('angle', 0)} reaches off-panel "
                    f"({px:.0f},{py:.0f})"
                )
                break
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            inter = _clip(polys[i], polys[j])
            if len(inter) >= 3:
                area = _poly_area(inter)
                smaller = min(_poly_area(polys[i]), _poly_area(polys[j]))
                if smaller and area > 0.20 * smaller:
                    warns.append(
                        f"{name}: boots {i + 1} and {j + 1} overlap by "
                        f"{area / smaller:.0%} of the smaller boot"
                    )
    for d in spec.get("dots", []):
        if not (0 <= d["x"] <= PANEL_W and 0 <= d["y"] <= height):
            warns.append(f"{name}: dot at ({d['x']},{d['y']}) is off-panel")
    return warns


def check_move(name, move):
    warns = []
    fracs = [s.get("track_until", 1.0) for s in move["stages"]]
    for f in fracs:
        if not 0.0 <= f <= 1.0:
            warns.append(f"{name}: track_until {f} is outside 0..1")
    if any(b < a for a, b in zip(fracs, fracs[1:])):
        warns.append(f"{name}: track_until goes backwards across stages {fracs}")
    if len(move["stages"]) < 2:
        warns.append(f"{name}: a move needs at least 2 stages")
    for i, stage in enumerate(move["stages"]):
        panel = f"{name}-k{i + 1}"
        warns.extend(check_panel(panel, expand_stage(move, stage)))
    return warns


# ---------------------------------------------------------------- main

def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {path}")


def generate(specs, out_dir, only=None, preview=False):
    """Generate outputs. `only` limits to one flat name, move name, or
    panel name (e.g. turn1-three-k2). Returns warning strings."""
    warns = []
    strips = []
    for name, spec in specs.items():
        if spec.get("move"):
            panels = [f"{name}-k{i + 1}" for i in range(len(spec["stages"]))]
            if only and only != name and only not in panels:
                continue
            warns.extend(check_move(name, spec))
            for i, stage in enumerate(spec["stages"]):
                panel = panels[i]
                if only and only not in (name, panel):
                    continue
                _write(os.path.join(out_dir, f"{panel}-feet.svg"),
                       render(expand_stage(spec, stage)))
            if only in (None, name):
                strip_path = os.path.join(out_dir, f"{name}-strip.svg")
                _write(strip_path, render_strip(name, spec))
                strips.append(strip_path)
        else:
            if only and only != name:
                continue
            warns.extend(check_panel(name, spec))
            _write(os.path.join(out_dir, f"{name}-feet.svg"), render(spec))
    if preview and strips:
        try:
            import cairosvg
        except ImportError:
            print("preview skipped: cairosvg is not installed")
        else:
            prev_dir = os.path.join(out_dir, "previews")
            os.makedirs(prev_dir, exist_ok=True)
            for strip_path in strips:
                png = os.path.join(
                    prev_dir,
                    os.path.basename(strip_path).replace(".svg", ".png"),
                )
                cairosvg.svg2png(url=strip_path, write_to=png)
                print(f"wrote {png}")
    return warns


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", nargs="?",
                        help="spec name, move name, or panel name")
    parser.add_argument("--all", action="store_true", help="generate every spec")
    parser.add_argument("--check", action="store_true",
                        help="validate only, write nothing")
    parser.add_argument("--preview", action="store_true",
                        help="also render PNG strips into previews/")
    parser.add_argument(
        "--specs",
        default=os.path.join(HERE, "feet_specs.json"),
        help="path to the specs JSON file",
    )
    args = parser.parse_args()

    with open(args.specs, encoding="utf-8") as f:
        specs = json.load(f)

    out_dir = os.path.dirname(os.path.abspath(args.specs))
    known = list(specs)
    for n, s in specs.items():
        if s.get("move"):
            known.extend(f"{n}-k{i + 1}" for i in range(len(s["stages"])))
    if args.name and args.name not in known:
        raise SystemExit(f"unknown spec: {args.name} (have: {', '.join(known)})")

    if args.check:
        warns = []
        for name, spec in specs.items():
            if spec.get("move"):
                warns.extend(check_move(name, spec))
            else:
                warns.extend(check_panel(name, spec))
    else:
        only = None if args.all else args.name
        warns = generate(specs, out_dir, only=only, preview=args.preview)
    for w in warns:
        print(f"WARNING: {w}")
    if not warns:
        print("checks: all clean")


if __name__ == "__main__":
    main()

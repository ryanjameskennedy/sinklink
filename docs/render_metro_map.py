#!/usr/bin/env python3
"""Render assets/metro_map.mmd with nf-metro and shade the QC and typing stations.

nf-metro gives every section box the same colour, and the map's fan-outs do not
lay out inside sections, so the coloured blocks are drawn here instead: a
rounded rectangle behind each group of stations, sized from the stations and
their labels in the rendered SVG. Writes docs/images/metro_map.svg (default
theme) and docs/images/metro_map_light.png (light theme).

Needs nf-metro (pip install nf-metro).
"""

import re
import subprocess
import sys
import tempfile
from itertools import pairwise
from pathlib import Path

from nf_metro.render.raster import svg_to_png

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "metro_map.mmd"
SVG_OUT = ROOT / "docs" / "images" / "metro_map.svg"
PNG_OUT = ROOT / "docs" / "images" / "metro_map_light.png"

BLOCKS = [
    {
        "title": "Assembly QC",
        "fill": "#f2c230",
        "opacity": 0.2,
        "ink": "#b07d00",
        "stations": ["quast", "mash", "gambitcore", "mlst", "mapping", "coverage", "qc_summary", "qc_out"],
    },
    {
        "title": "Typing",
        "fill": "#2db572",
        "opacity": 0.16,
        "ink": "#1f8a56",
        "stations": ["chewbbaca", "distances", "distances_tsv", "report", "report_out"],
    },
]
PAD_X = 22
PAD_Y = 12
TITLE_SIZE = 14
TITLE_GAP = 6
GAP = 6
TITLE_ROOM = 70


def attrs(tag):
    return dict(re.findall(r'([\w:-]+)="([^"]*)"', tag))


def station_boxes(svg):
    boxes = {}

    def grow(sid, x0, y0, x1, y1):
        b = boxes.get(sid)
        boxes[sid] = (x0, y0, x1, y1) if b is None else (min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1))

    for tag in re.findall(r"<(?:rect|circle|path|use|g)\b[^>]*data-station-id=\"[^\"]+\"[^>]*>", svg):
        a = attrs(tag)
        sid = a["data-station-id"]
        if "width" in a and "x" in a:
            x, y, w, h = (float(a[k]) for k in ("x", "y", "width", "height"))
            grow(sid, x, y, x + w, y + h)
        elif "cx" in a:
            cx, cy, r = float(a["cx"]), float(a["cy"]), float(a.get("r", 5))
            grow(sid, cx - r, cy - r, cx + r, cy + r)
    for tag, text in re.findall(r"(<text\b[^>]*nf-metro-station-label[^>]*>)(.*?)</text>", svg, re.DOTALL):
        a = attrs(tag)
        sid = a.get("data-station-id")
        if not sid:
            continue
        label = re.sub(r"<[^>]+>", "\n", text)
        lines = [line for line in (part.strip() for part in label.split("\n")) if line]
        size = float(a.get("font-size", 13))
        width = max((len(line) for line in lines), default=0) * size * 0.58
        height = size * 1.25 * max(len(lines), 1)
        x, y = float(a["x"]), float(a["y"])
        anchor = a.get("text-anchor", "start")
        x0 = x - width / 2 if anchor == "middle" else (x - width if anchor == "end" else x)
        y0 = y if a.get("dominant-baseline") == "hanging" else y - size
        grow(sid, x0, y0, x0 + width, y0 + height)
    for tag in re.findall(r"<(?:image|g|use)\b[^>]*data-file-id=\"[^\"]+\"[^>]*>", svg):
        a = attrs(tag)
        if "x" in a and "width" in a:
            x, y, w, h = (float(a[k]) for k in ("x", "y", "width", "height"))
            grow(a["data-file-id"], x, y, x + w, y + h)
    return boxes


def shade(svg):
    boxes = station_boxes(svg)
    rects = []
    for block in BLOCKS:
        found = [boxes[s] for s in block["stations"] if s in boxes]
        missing = [s for s in block["stations"] if s not in boxes]
        if missing:
            sys.exit(f"stations not found in the rendered map: {', '.join(missing)}")
        x0 = min(b[0] for b in found) - PAD_X
        y0 = min(b[1] for b in found) - PAD_Y - TITLE_SIZE - TITLE_GAP
        x1 = max(b[2] for b in found) + PAD_X
        y1 = max(b[3] for b in found) + PAD_Y
        rects.append([x0, y0, x1, y1])
    for upper, lower in pairwise(rects):
        if upper[3] > lower[1] - GAP:
            middle = (upper[3] + lower[1]) / 2
            upper[3], lower[1] = middle - GAP / 2, middle + GAP / 2
    shapes = []
    for block, (x0, y0, x1, y1) in zip(BLOCKS, rects):
        shapes.append(
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" rx="12" ry="12" '
            f'fill="{block["fill"]}" fill-opacity="{block["opacity"]}" stroke="{block["fill"]}" '
            f'stroke-opacity="0.45" stroke-width="1" class="sinklink-block" />'
            f'<text x="{x0 + 12:.1f}" y="{y0 + 8 + TITLE_SIZE:.1f}" font-size="{TITLE_SIZE}" font-weight="bold" '
            f"font-family=\"Inter, 'Helvetica Neue', Helvetica, Arial, sans-serif\" fill=\"{block['ink']}\" "
            f'class="sinklink-block-title">{block["title"]}</text>'
        )
    background = re.search(r"<rect\b[^>]*nf-metro-bg[^>]*/>", svg)
    if not background:
        sys.exit("no background rectangle in the rendered map")
    return svg[: background.end()] + "".join(shapes) + svg[background.end():]


def crop_top(svg):
    """Move the title down to just above the map and drop the empty band above it."""
    boxes = station_boxes(svg)
    top = min(b[1] for b in boxes.values())
    title_tag = re.search(r"<text\b[^>]*nf-metro-title[^>]*>", svg)
    root = re.search(r"<svg\b[^>]*>", svg)
    if not title_tag or not root:
        sys.exit("no title or svg element in the rendered map")
    title_y = float(attrs(title_tag.group(0))["y"])
    shift = top - TITLE_ROOM - title_y
    if shift <= 0:
        return svg
    moved = re.sub(r'\by="[^"]*"', f'y="{title_y + shift:.1f}"', title_tag.group(0), count=1)
    svg = svg[: title_tag.start()] + moved + svg[title_tag.end():]
    root = re.search(r"<svg\b[^>]*>", svg)
    tag = root.group(0)
    a = attrs(tag)
    width, height = float(a["width"]), float(a["height"])
    vb = [float(v) for v in a.get("viewBox", f"0 0 {width} {height}").split()]
    new_tag = re.sub(r'\bheight="[^"]*"', f'height="{height - shift:.1f}"', tag, count=1)
    new_tag = re.sub(r'\bviewBox="[^"]*"', f'viewBox="{vb[0]} {vb[1] + shift:.1f} {vb[2]} {vb[3] - shift:.1f}"', new_tag, count=1)
    return svg.replace(tag, new_tag, 1)


def render(extra=()):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "map.svg"
        subprocess.run(["nf-metro", "render", str(SOURCE), "-o", str(out), *extra], check=True)
        return out.read_text()


def main():
    SVG_OUT.write_text(crop_top(shade(render())))
    raster = render(["--mode", "light", "--no-chrome-css", "--embed-font"])
    PNG_OUT.write_bytes(svg_to_png(crop_top(shade(raster))))
    print(f"Written {SVG_OUT.relative_to(ROOT)} and {PNG_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

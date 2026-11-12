#!/usr/bin/env python3
"""Transmission report and publication figures from the sinklink distance tables.

Reads pairwise_distances.tsv, group_summary.tsv and allele_qc.tsv
(check_distances.py), qc_summary.tsv (summarise_qc.py), the study metadata,
assets/schemas.tsv and assets/qc_thresholds.tsv. Writes
transmission_report.html, table1.tsv and figures/ with every figure as PDF,
SVG and PNG. Run it on a finished results folder to restyle the figures
without rerunning the pipeline.
"""

import argparse
import csv
import html
import io
import logging
import math
import re
from datetime import date, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, MaxNLocator, NullLocator

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

ORANGE = "#eb6834"
BLUE = "#2a78d6"
GREY = "#898781"
AQUA = "#1baf7a"
VIOLET = "#6250d6"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#ffffff"

VERDICTS = {
    "within_threshold": ("Within threshold", ORANGE, True),
    "borderline": ("Borderline", BLUE, True),
    "above_threshold": ("Above threshold", GREY, False),
}
PAIR_KINDS = {
    "environment-patient": ("Environment–patient", "D"),
    "environment-environment": ("Environment–environment", "s"),
    "patient-patient": ("Patient–patient", "o"),
}
KINDS = {
    "environment": ("Environment", AQUA, "s"),
    "patient": ("Patient", VIOLET, "o"),
}
QC_STATUS = {
    "pass": ("Pass", "#0ca30c", "#ffffff"),
    "warn": ("Warn", "#fab219", "#0b0b0b"),
    "fail": ("Fail", "#d03b3b", "#ffffff"),
    "": ("Not checked", GREY, "#ffffff"),
}
ROMAN_WORDS = {"species", "complex", "group"}
DISTANCE_TICKS = [0, 5, 10, 15, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
MM = 1 / 25.4


def read_tsv(path):
    if not path or not Path(path).is_file() or Path(path).stat().st_size == 0:
        return []
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_metadata(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return {row["sample"]: row for row in csv.DictReader(handle)}


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_date(value):
    try:
        return datetime.fromisoformat((value or "").strip())
    except ValueError:
        return None


def natural_key(text):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def species_label(organism):
    """Mathtext with the Latin words in italics and 'species complex' upright."""
    out, run = [], []
    for word in organism.split():
        if word.lower() in ROMAN_WORDS:
            if run:
                out.append(r"$\it{" + r"\ ".join(run) + "}$")
                run = []
            out.append(word)
        else:
            run.append(word)
    if run:
        out.append(r"$\it{" + r"\ ".join(run) + "}$")
    return " ".join(out)


def species_html(organism):
    words = []
    for word in organism.split():
        escaped = html.escape(word)
        words.append(escaped if word.lower() in ROMAN_WORDS else f"<i>{escaped}</i>")
    return " ".join(words).replace("</i> <i>", " ")


def style(font_size):
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": font_size,
        "axes.titlesize": font_size,
        "axes.labelsize": font_size,
        "xtick.labelsize": font_size - 1,
        "ytick.labelsize": font_size - 1,
        "legend.fontsize": font_size - 1,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK2,
        "axes.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlecolor": INK,
        "xtick.color": AXIS,
        "ytick.color": AXIS,
        "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "legend.frameon": False,
        "figure.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "mathtext.fontset": "custom",
        "mathtext.rm": "sans",
        "mathtext.it": "sans:italic",
        "mathtext.bf": "sans:bold",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


class Figures:
    """Saves figures, and gives every point tagged with tip() a hover label in the SVG."""

    def __init__(self, outdir, formats, dpi):
        self.dir = Path(outdir) / "figures"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.formats = formats
        self.dpi = dpi
        self.tips = {}
        self.count = 0

    def tip(self, artist, lines):
        self.count += 1
        gid = f"tip-{self.count}"
        artist.set_gid(gid)
        self.tips[gid] = "\n".join(line for line in lines if line)

    def save(self, fig, name):
        buffer = io.StringIO()
        fig.savefig(buffer, format="svg", bbox_inches="tight")
        svg = add_tips(buffer.getvalue(), self.tips)
        self.tips = {}
        for fmt in self.formats:
            path = self.dir / f"{name}.{fmt}"
            if fmt == "svg":
                path.write_text(svg, encoding="utf-8")
            else:
                fig.savefig(path, dpi=self.dpi, bbox_inches="tight")
        plt.close(fig)
        return inline_svg(svg, name)


def add_tips(svg, tips):
    def label(match):
        text = tips.get(match.group(1))
        if text is None:
            return match.group(0)
        return f'<g id="{match.group(1)}" class="pt"{match.group(2)}><title>{html.escape(text)}</title>'
    return re.sub(r'<g id="(tip-\d+)"([^>]*)>', label, svg)


def inline_svg(svg, name):
    """The SVG ready to place in the HTML: no XML prolog, ids unique to this figure and a scalable size."""
    svg = svg[svg.index("<svg"):]
    svg = re.sub(r"<style[^>]*>.*?</style>", "", svg, flags=re.S)
    svg = re.sub(r'(<svg[^>]*?)\s(?:width|height)="[^"]*"', r"\1", svg, count=1)
    svg = re.sub(r'(<svg[^>]*?)\s(?:width|height)="[^"]*"', r"\1", svg, count=1)
    ids = set(re.findall(r'\bid="([^"]+)"', svg))
    prefix = re.sub(r"[^\w-]", "_", name)
    return re.sub(r'(\bid="|url\(#|href="#)([^")]+)',
                  lambda m: f"{m.group(1)}{prefix}-{m.group(2)}" if m.group(2) in ids else m.group(0), svg)


def pair_tip(pair):
    days = to_int(pair.get("days_apart"))
    types = " – ".join(t for t in (pair.get("type_a", ""), pair.get("type_b", "")) if t)
    return [
        f"{pair['sample_a']} – {pair['sample_b']} ({pair['transmission']})",
        f"{plural(pair['diffs'], 'allele difference')}, {VERDICTS[pair['verdict']][0].lower()}",
        f"{plural(pair['snps'], 'SNP')}" if pair.get("snps") is not None else "",
        f"{plural(days, 'day')} apart" if days is not None else "",
        types,
    ]


def isolate_tip(sid, sample):
    patient = sample.get("studypatientnumber", "").strip()
    sampled = parse_date(sample.get("date"))
    return [
        f"{sid} ({sample.get('transmission', '')})" if sample.get("transmission") else sid,
        " · ".join(x for x in (sample.get("sample_type", "").strip(), f"patient {patient}" if patient else "") if x),
        f"sampled {sampled.date().isoformat()}" if sampled else "",
    ]


def sample_kind(sample, environment_types):
    return "environment" if sample.get("sample_type", "").strip().lower() in environment_types else "patient"


def pair_kind(pair, environment_types):
    kinds = sorted(
        "environment" if pair[f"type_{side}"].strip().lower() in environment_types else "patient"
        for side in ("a", "b")
    )
    return "-".join(kinds) if kinds != ["environment", "patient"] else "environment-patient"


def distance_axis(ax, axis, values, thresholds):
    top = max(values + thresholds + [1])
    set_scale = ax.set_xscale if axis == "x" else ax.set_yscale
    set_lim = ax.set_xlim if axis == "x" else ax.set_ylim
    target = ax.xaxis if axis == "x" else ax.yaxis
    if top <= 30:
        set_lim(-0.8, top * 1.15 + 1)
        target.set_major_locator(MaxNLocator(nbins=6, integer=True))
        return
    set_scale("symlog", linthresh=20, linscale=1.2)
    ticks = [t for t in DISTANCE_TICKS if t <= top * 1.05] or [0]
    target.set_major_locator(FixedLocator(ticks))
    target.set_minor_locator(NullLocator())
    target.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    set_lim(-0.8, top * 1.4)


def verdict_marker(ax, x, y, verdict, kind, size=34, zorder=3):
    _, colour, filled = VERDICTS[verdict]
    marker = PAIR_KINDS[kind][1]
    return ax.scatter(
        x, y, s=size, marker=marker, zorder=zorder,
        facecolors=colour if filled else SURFACE,
        edgecolors=SURFACE if filled else colour,
        linewidths=0.6 if filled else 1.1,
    )


def top_legend(fig, handles):
    fig.subplots_adjust(top=1 - 0.24 / fig.get_figheight())
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=len(handles),
               handletextpad=0.4, columnspacing=1.2, handlelength=1.4)


def verdict_handles(verdicts):
    handles = []
    for verdict, (label, colour, filled) in VERDICTS.items():
        if verdict in verdicts:
            handles.append(Patch(facecolor=colour if filled else SURFACE, edgecolor=colour,
                                 linewidth=1.1, label=label))
    return handles


def verdict_legend(fig, verdicts, kinds):
    handles = verdict_handles(verdicts)
    for kind, (label, marker) in PAIR_KINDS.items():
        if kind in kinds:
            handles.append(Line2D([], [], linestyle="none", marker=marker, markersize=5,
                                  markerfacecolor=INK2, markeredgecolor=INK2, label=label))
    top_legend(fig, handles)


def threshold_marks(ax, axis, info, span=None):
    threshold, borderline = info["threshold"], info["borderline"]
    line = ax.axvline if axis == "x" else ax.axhline
    band = ax.axvspan if axis == "x" else ax.axhspan
    kwargs = {} if span is None else ({"ymin": span[0], "ymax": span[1]} if axis == "x"
                                      else {"xmin": span[0], "xmax": span[1]})
    if borderline:
        band(threshold, borderline, color=BLUE, alpha=0.10, linewidth=0, zorder=1, **kwargs)
    line(threshold, color=INK2, linewidth=0.8, linestyle=(0, (3, 2)), zorder=2, **kwargs)


def display_position(value):
    return value / 20 if value <= 20 else 1 + 1.2 * math.log10(value / 20)


def spread(values, step=0.2, limit=0.38, tolerance=0.06):
    """Vertical offsets that pull apart points sitting at almost the same place on the axis."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    clusters, current = [], []
    for i in order:
        if current and display_position(values[i]) - display_position(values[current[-1]]) > tolerance:
            clusters.append(current)
            current = []
        current.append(i)
    if current:
        clusters.append(current)
    offsets = [0.0] * len(values)
    for cluster in clusters:
        n = len(cluster)
        for rank, i in enumerate(cluster):
            offsets[i] = max(-limit, min(limit, (rank - (n - 1) / 2) * step))
    return offsets


def overview_figure(figs, rows_by_schema, schemas, width_mm, environment_types):
    order = sorted(rows_by_schema, key=lambda s: schemas[s]["organism"])
    heights = [len({p["transmission"] for p in rows_by_schema[s]}) for s in order]
    fig_height = sum(0.24 * h + 0.32 for h in heights) + 0.25
    fig, axes = plt.subplots(len(order), 1, figsize=(width_mm * MM, fig_height), sharex=True,
                             gridspec_kw={"height_ratios": [h + 0.6 for h in heights], "hspace": 0.55},
                             squeeze=False)
    all_values = [p["diffs"] for s in order for p in rows_by_schema[s]]
    all_thresholds = [schemas[s]["borderline"] or schemas[s]["threshold"] for s in order]
    verdicts, kinds = set(), set()
    for ax, schema in zip(axes[:, 0], order):
        info = schemas[schema]
        groups = sorted({p["transmission"] for p in rows_by_schema[schema]}, key=natural_key, reverse=True)
        y_of = {g: i for i, g in enumerate(groups)}
        threshold_marks(ax, "x", info)
        for group in groups:
            pairs = sorted((p for p in rows_by_schema[schema] if p["transmission"] == group), key=lambda p: p["diffs"])
            for pair, offset in zip(pairs, spread([p["diffs"] for p in pairs])):
                kind = pair_kind(pair, environment_types)
                verdicts.add(pair["verdict"])
                kinds.add(kind)
                figs.tip(verdict_marker(ax, pair["diffs"], y_of[group] + offset, pair["verdict"], kind),
                         pair_tip(pair))
        ax.set_yticks(range(len(groups)), groups)
        ax.set_ylim(-0.6, len(groups) - 0.4)
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        ax.grid(axis="x", zorder=0)
        ax.set_axisbelow(True)
        ax.set_title(species_label(info["organism"]), loc="left", pad=3)
        ax.set_title(threshold_text(info), loc="right", pad=3, color=INK2)
        distance_axis(ax, "x", all_values, all_thresholds)
    axes[-1, 0].set_xlabel("Allele differences")
    verdict_legend(fig, verdicts, kinds)
    return figs.save(fig, "distance_overview")


def threshold_text(info):
    if info["borderline"]:
        return f"threshold ≤{info['threshold']} (borderline ≤{info['borderline']})"
    return f"threshold ≤{info['threshold']}"


def small_multiples(n, width_mm, panel_height, ncols_max=3):
    ncols = min(ncols_max, n)
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(width_mm * MM, panel_height * nrows + 0.3),
                             squeeze=False, gridspec_kw={"hspace": 0.6, "wspace": 0.35})
    for ax in axes.flat[n:]:
        ax.set_visible(False)
    return fig, axes.flat[:n]


def time_figure(figs, rows_by_schema, schemas, width_mm, environment_types):
    order = [s for s in sorted(rows_by_schema, key=lambda s: schemas[s]["organism"])
             if any(p["days"] is not None for p in rows_by_schema[s])]
    if not order:
        return None
    fig, axes = small_multiples(len(order), width_mm, 1.55)
    verdicts, kinds = set(), set()
    for ax, schema in zip(axes, order):
        info = schemas[schema]
        pairs = [p for p in rows_by_schema[schema] if p["days"] is not None]
        threshold_marks(ax, "y", info)
        for pair in pairs:
            kind = pair_kind(pair, environment_types)
            verdicts.add(pair["verdict"])
            kinds.add(kind)
            figs.tip(verdict_marker(ax, pair["days"], pair["diffs"], pair["verdict"], kind, size=26), pair_tip(pair))
        distance_axis(ax, "y", [p["diffs"] for p in pairs], [info["borderline"] or info["threshold"]])
        days_axis(ax, max(p["days"] for p in pairs))
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.set_title(species_label(info["organism"]), loc="left", pad=3)
        ax.set_xlabel("Days between samples")
        ax.set_ylabel("Allele differences")
    verdict_legend(fig, verdicts, kinds)
    return figs.save(fig, "distance_vs_time")


def days_axis(ax, longest):
    top = max(longest, 10)
    ticks = [t for t in MaxNLocator(nbins=5, integer=True).tick_values(0, top) if 0 <= t <= top * 1.08]
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.set_xlim(-0.04 * top, top * 1.08)


def snp_figure(figs, rows_by_schema, schemas, width_mm, environment_types):
    order = [s for s in sorted(rows_by_schema, key=lambda s: schemas[s]["organism"])
             if any(p["snps"] is not None for p in rows_by_schema[s])]
    if not order:
        return None
    fig, axes = small_multiples(len(order), width_mm, 1.6)
    verdicts, kinds = set(), set()
    for ax, schema in zip(axes, order):
        info = schemas[schema]
        pairs = [p for p in rows_by_schema[schema] if p["snps"] is not None]
        threshold_marks(ax, "x", info)
        for pair in pairs:
            kind = pair_kind(pair, environment_types)
            verdicts.add(pair["verdict"])
            kinds.add(kind)
            figs.tip(verdict_marker(ax, pair["diffs"], pair["snps"], pair["verdict"], kind, size=26), pair_tip(pair))
        distance_axis(ax, "x", [p["diffs"] for p in pairs], [info["borderline"] or info["threshold"]])
        distance_axis(ax, "y", [p["snps"] for p in pairs], [])
        ax.grid(True)
        ax.set_axisbelow(True)
        filtered = {p["filtered"] for p in pairs}
        note = " (Gubbins)" if filtered == {"yes"} else ""
        ax.set_title(species_label(info["organism"]), loc="left", pad=3)
        ax.set_xlabel("Allele differences")
        ax.set_ylabel(f"SNP differences{note}")
    verdict_legend(fig, verdicts, kinds)
    return figs.save(fig, "allele_vs_snp")


def isolate_rows(isolates, environment_types):
    keys = {}
    for sample in isolates:
        kind = sample_kind(sample, environment_types)
        patient = sample.get("studypatientnumber", "").strip()
        sample_type = sample.get("sample_type", "").strip() or kind
        key = (0 if kind == "environment" else 1, tuple(natural_key(patient)), sample_type)
        keys[sample["sample"]] = (key, f"{patient} · {sample_type}" if patient else sample_type)
    order = sorted({v for v in keys.values()}, key=lambda kv: kv[0], reverse=True)
    y_of = {label: i for i, (_, label) in enumerate(order)}
    return {sid: y_of[label] for sid, (_, label) in keys.items()}, [label for _, label in order]


def draw_timeline(figs, ax, group, isolates, links, environment_types, show_xlabel=True):
    dated = [s for s in isolates if parse_date(s.get("date"))]
    row_of, labels = isolate_rows(dated, environment_types)
    x_of = {s["sample"]: mdates.date2num(parse_date(s["date"])) for s in dated}
    for pair in links:
        a, b = pair["sample_a"], pair["sample_b"]
        if a not in x_of or b not in x_of:
            continue
        _, colour, _ = VERDICTS[pair["verdict"]]
        style_ = "-" if pair["verdict"] == "within_threshold" else (0, (3, 2))
        xa, ya, xb, yb = x_of[a], row_of[a], x_of[b], row_of[b]
        if ya == yb:
            ax.annotate("", xy=(xb, yb), xytext=(xa, ya), zorder=2,
                        arrowprops={"arrowstyle": "-", "color": colour, "linewidth": 1.2,
                                    "linestyle": style_, "connectionstyle": "arc3,rad=-0.35",
                                    "shrinkA": 4, "shrinkB": 4})
            mx, my = (xa + xb) / 2, ya + 0.32
        else:
            ax.plot([xa, xb], [ya, yb], color=colour, linewidth=1.2, linestyle=style_, zorder=2)
            mx, my = (xa + xb) / 2, (ya + yb) / 2
        ax.text(mx, my, str(pair["diffs"]), ha="center", va="center", fontsize=plt.rcParams["font.size"] - 1.5,
                color=INK, zorder=4, bbox={"boxstyle": "round,pad=0.15", "facecolor": SURFACE,
                                           "edgecolor": colour, "linewidth": 0.6})
    span = (max(x_of.values()) - min(x_of.values())) if x_of else 0
    last = {}
    for sample in sorted(dated, key=lambda s: x_of[s["sample"]]):
        sid = sample["sample"]
        kind = sample_kind(sample, environment_types)
        _, colour, marker = KINDS[kind]
        x, y = x_of[sid], row_of[sid]
        figs.tip(ax.scatter(x, y, s=34, marker=marker, facecolors=colour, edgecolors=SURFACE, linewidths=0.6,
                            zorder=3), isolate_tip(sid, sample))
        close = y in last and span and (x - last[y][0]) < 0.08 * span
        below = close and not last[y][1]
        last[y] = (x, below)
        ax.annotate(sid, (x, y), xytext=(0, -8 if below else 6), textcoords="offset points",
                    ha="center", va="top" if below else "bottom", color=INK2,
                    fontsize=plt.rcParams["font.size"] - 1.5, zorder=5)
    ax.set_yticks(range(len(labels)), labels)
    ax.set_ylim(-0.7, len(labels) - 0.2)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    pad = max(span * 0.06, 3)
    if x_of:
        ax.set_xlim(min(x_of.values()) - pad, max(x_of.values()) + pad)
    locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.set_title(group, loc="left", pad=3)
    if show_xlabel:
        ax.set_xlabel("Sampling date")


def kind_handles():
    return [Line2D([], [], linestyle="none", marker=marker, markersize=5, markerfacecolor=colour,
                   markeredgecolor=colour, label=label) for label, colour, marker in KINDS.values()]


def timeline_legend(fig, links):
    handles = kind_handles()
    verdicts = {p["verdict"] for p in links}
    if "within_threshold" in verdicts:
        handles.append(Line2D([], [], color=ORANGE, linewidth=1.2, label="Within threshold"))
    if "borderline" in verdicts:
        handles.append(Line2D([], [], color=BLUE, linewidth=1.2, linestyle=(0, (3, 2)), label="Borderline"))
    top_legend(fig, handles)


def closest_earlier(isolates, pairs):
    """Join each isolate to the earlier isolate it is closest to, when the pair is within the threshold."""
    when = {s["sample"]: parse_date(s.get("date")) for s in isolates}
    order = sorted((s for s in when if when[s]), key=lambda s: (when[s], natural_key(s)))
    rank = {s: i for i, s in enumerate(order)}
    links = []
    for sample in order[1:]:
        candidates = []
        for p in pairs:
            if p["verdict"] not in ("within_threshold", "borderline") or sample not in (p["sample_a"], p["sample_b"]):
                continue
            other = p["sample_b"] if p["sample_a"] == sample else p["sample_a"]
            if other in rank and rank[other] < rank[sample]:
                candidates.append((p["diffs"], (when[sample] - when[other]).days, p))
        if candidates:
            links.append(min(candidates, key=lambda c: (c[0], c[1]))[2])
    return links


def timeline_figures(figs, groups, metadata, pairs_by_group, width_mm, environment_types):
    images, panels = {}, []
    for group in groups:
        isolates = [metadata[s] for s in groups[group] if s in metadata]
        if sum(1 for s in isolates if parse_date(s.get("date"))) < 2:
            continue
        links = closest_earlier(isolates, pairs_by_group.get(group, []))
        n_rows = len(isolate_rows([s for s in isolates if parse_date(s.get("date"))], environment_types)[1])
        height = 0.34 * n_rows + 0.85
        fig, ax = plt.subplots(figsize=(width_mm * MM, height))
        draw_timeline(figs, ax, group, isolates, links, environment_types)
        timeline_legend(fig, links)
        images[group] = figs.save(fig, f"timeline_{safe_name(group)}")
        panels.append((group, isolates, links, n_rows))
    if len(panels) > 1:
        heights = [0.34 * n + 0.6 for *_, n in panels]
        fig, axes = plt.subplots(len(panels), 1, figsize=(width_mm * MM, sum(heights) + 0.3), squeeze=False,
                                 gridspec_kw={"height_ratios": heights, "hspace": 0.9})
        for ax, (group, isolates, links, _) in zip(axes[:, 0], panels):
            draw_timeline(figs, ax, group, isolates, links, environment_types, show_xlabel=False)
        axes[-1, 0].set_xlabel("Sampling date")
        timeline_legend(fig, [link for p in panels for link in p[2]])
        images["_all"] = figs.save(fig, "timelines")
    return images


def minimum_spanning_tree(nodes, distance):
    tree, edges = {nodes[0]}, []
    while len(tree) < len(nodes):
        best = min(((distance[(a, b)], a, b) for a in tree for b in nodes if b not in tree and (a, b) in distance),
                   default=None)
        if best is None:
            break
        d, a, b = best
        tree.add(b)
        edges.append((a, b, d))
    return edges


def radial_layout(root, edges):
    children, weight = {}, {}
    for a, b, d in edges:
        children.setdefault(a, []).append(b)
        children.setdefault(b, []).append(a)
        weight[(a, b)] = weight[(b, a)] = d
    tree, seen, stack = {}, {root}, [root]
    while stack:
        node = stack.pop()
        tree[node] = sorted((c for c in children.get(node, []) if c not in seen), key=natural_key)
        seen.update(tree[node])
        stack.extend(tree[node])

    def leaves(node):
        return 1 if not tree[node] else sum(leaves(c) for c in tree[node])

    pos = {root: (0.0, 0.0)}

    def place(node, start, span):
        total = sum(leaves(c) for c in tree[node]) or 1
        angle = start
        for child in tree[node]:
            part = span * leaves(child) / total
            theta = angle + part / 2
            length = 1 + 1.2 * math.log10(1 + weight[(node, child)])
            x, y = pos[node]
            pos[child] = (x + length * math.cos(theta), y + length * math.sin(theta))
            place(child, angle, part)
            angle += part

    place(root, math.pi / 2, 2 * math.pi)
    parent = {c: n for n, cs in tree.items() for c in cs}
    return pos, parent


def draw_tree(figs, ax, group, isolates, pairs, environment_types):
    nodes = sorted({p[s] for p in pairs for s in ("sample_a", "sample_b")}, key=natural_key)
    distance, verdict_of = {}, {}
    for p in pairs:
        distance[(p["sample_a"], p["sample_b"])] = distance[(p["sample_b"], p["sample_a"])] = p["diffs"]
        verdict_of[frozenset((p["sample_a"], p["sample_b"]))] = p["verdict"]
    edges = minimum_spanning_tree(nodes, distance)
    degree = {}
    for a, b, _ in edges:
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    by_id = {s["sample"]: s for s in isolates}
    first = {n: parse_date(by_id.get(n, {}).get("date")) or datetime.max for n in nodes}
    root = min(nodes, key=lambda n: (-degree.get(n, 0), first[n], natural_key(n)))
    pos, parent = radial_layout(root, edges)
    small = plt.rcParams["font.size"] - 1.5
    for a, b, d in edges:
        _, colour, _ = VERDICTS[verdict_of[frozenset((a, b))]]
        (xa, ya), (xb, yb) = pos[a], pos[b]
        ax.plot([xa, xb], [ya, yb], color=colour, linewidth=1.4, zorder=1, solid_capstyle="round")
        ax.text((xa + xb) / 2, (ya + yb) / 2, str(d), ha="center", va="center", fontsize=small, color=INK,
                zorder=4, bbox={"boxstyle": "round,pad=0.15", "facecolor": SURFACE, "edgecolor": "none"})
    for node in nodes:
        if node not in pos:
            continue
        kind = sample_kind(by_id.get(node, {}), environment_types)
        _, colour, marker = KINDS[kind]
        x, y = pos[node]
        figs.tip(ax.scatter(x, y, s=70, marker=marker, facecolors=colour, edgecolors=SURFACE, linewidths=0.8,
                            zorder=3), isolate_tip(node, by_id.get(node, {})))
        if node in parent:
            px, py = pos[parent[node]]
            angle = math.atan2(y - py, x - px) + math.pi / 2
            if math.sin(angle) < 0:
                angle += math.pi
        else:
            angle = math.pi / 2
        ax.annotate(node, (x, y), xytext=(10 * math.cos(angle), 10 * math.sin(angle)), textcoords="offset points",
                    ha="center", va="center", fontsize=small, color=INK2, zorder=5)
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    margin = 0.9
    ax.set_xlim(min(xs) - margin, max(xs) + margin)
    ax.set_ylim(min(ys) - margin, max(ys) + margin)
    ax.set_aspect("equal", adjustable="datalim")
    ax.axis("off")
    ax.set_title(group, loc="left", pad=3)
    return edges


def tree_legend(fig, verdicts):
    handles = kind_handles()
    for verdict, (label, colour, _) in VERDICTS.items():
        if verdict in verdicts:
            handles.append(Line2D([], [], color=colour, linewidth=1.4, label=label))
    top_legend(fig, handles)


def tree_figures(figs, groups, metadata, pairs_by_group, width_mm, environment_types):
    images, panels = {}, []
    for group in groups:
        pairs = pairs_by_group.get(group, [])
        nodes = {p[s] for p in pairs for s in ("sample_a", "sample_b")}
        if len(nodes) < 3:
            continue
        isolates = [metadata[s] for s in groups[group] if s in metadata]
        size = width_mm * MM / 2
        fig, ax = plt.subplots(figsize=(size, size))
        draw_tree(figs, ax, group, isolates, pairs, environment_types)
        tree_legend(fig, {p["verdict"] for p in pairs})
        images[group] = figs.save(fig, f"tree_{safe_name(group)}")
        panels.append((group, isolates, pairs))
    if len(panels) > 1:
        fig, axes = small_multiples(len(panels), width_mm, width_mm * MM / 4)
        for ax, (group, isolates, pairs) in zip(axes, panels):
            draw_tree(figs, ax, group, isolates, pairs, environment_types)
        tree_legend(fig, {p["verdict"] for _, _, ps in panels for p in ps})
        images["_all"] = figs.save(fig, "trees")
    return images


def status_bars(ax, rows, counts, labels):
    y_of = {row: i for i, row in enumerate(reversed(rows))}
    totals = {row: sum(counts[row].values()) for row in rows}
    longest = max(totals.values()) or 1
    small = plt.rcParams["font.size"] - 1
    for row in rows:
        left = 0
        for status, (_, colour, ink) in QC_STATUS.items():
            n = counts[row].get(status, 0)
            if not n:
                continue
            ax.barh(y_of[row], n, left=left, height=0.62, color=colour, edgecolor=SURFACE, linewidth=1.2, zorder=3)
            if n / longest > 0.04:
                ax.text(left + n / 2, y_of[row], str(n), ha="center", va="center", color=ink, fontsize=small, zorder=4)
            left += n
        ax.text(left + longest * 0.015, y_of[row], f"{totals[row]}", ha="left", va="center", color=INK2,
                fontsize=small)
    ax.set_yticks(range(len(rows)), [labels[r] for r in reversed(rows)])
    ax.set_xlim(0, longest * 1.1)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x")
    ax.set_axisbelow(True)


def sample_qc_figure(figs, metadata, qc_rows, schemas, width_mm, environment_types):
    """Isolates by read and assembly QC status, per species and per kind of sample."""
    if not metadata:
        return None, {}
    qc = {r["sample"]: r for r in qc_rows}
    by_species, by_kind, overall = {}, {}, {}
    for sid, sample in metadata.items():
        row = qc.get(sid, {})
        status = row.get("qc_status", "") if row.get("qc_status", "") in QC_STATUS else ""
        schema = row.get("schema", "") if row.get("schema", "") in schemas else ""
        kind = sample_kind(sample, environment_types)
        for table, key in ((by_species, schema), (by_kind, kind)):
            table.setdefault(key, {}).setdefault(status, 0)
            table[key][status] += 1
        overall[status] = overall.get(status, 0) + 1
    species_rows = sorted((s for s in by_species if s), key=lambda s: schemas[s]["organism"])
    if "" in by_species:
        species_rows.append("")
    species_labels = {s: species_label(schemas[s]["organism"]) if s else "No schema" for s in species_rows}
    kind_rows = [k for k in KINDS if k in by_kind]
    kind_labels = {k: KINDS[k][0] for k in kind_rows}
    height = 0.24 * len(species_rows) + 0.75
    fig, axes = plt.subplots(1, 2, figsize=(width_mm * MM, height), squeeze=False,
                             gridspec_kw={"width_ratios": [3, 2], "wspace": 0.5})
    status_bars(axes[0, 0], species_rows, by_species, species_labels)
    status_bars(axes[0, 1], kind_rows, by_kind, kind_labels)
    axes[0, 1].set_ylim(-0.6 - (len(species_rows) - len(kind_rows)) / 2, len(kind_rows) - 0.4
                        + (len(species_rows) - len(kind_rows)) / 2)
    axes[0, 0].set_title("By species", loc="left", pad=3)
    axes[0, 1].set_title("By sample type", loc="left", pad=3)
    for ax in axes[0]:
        ax.set_xlabel("Isolates")
    present = [s for s in QC_STATUS if overall.get(s)]
    top_legend(fig, [Patch(facecolor=QC_STATUS[s][1], edgecolor=QC_STATUS[s][1], label=QC_STATUS[s][0])
                     for s in present])
    return figs.save(fig, "sample_qc"), overall


PLATFORMS = {"illumina": ("Illumina", "o", (0, (3, 2))), "nanopore": ("Nanopore", "^", (0, (1, 1.5)))}


def swarm(values, span, step=0.13, limit=0.4, tolerance=0.035):
    """Vertical offsets that keep points at nearly the same value from covering each other."""
    slots = [0.0] + [sign * k * step for k in range(1, int(limit / step) + 1) for sign in (1, -1)]
    offsets, placed = [0.0] * len(values), []
    for i in sorted(range(len(values)), key=lambda i: values[i]):
        near = [offsets[j] for j in placed if abs(values[j] - values[i]) <= tolerance * span]
        free = [o for o in slots if all(abs(o - n) > step / 2 for n in near)]
        offsets[i] = free[0] if free else slots[len(near) % len(slots)]
        placed.append(i)
    return offsets


def qc_value_text(field, value):
    return f"{value:.0f}×" if field == "mean_depth" else f"{value * 100:.1f}%"


def qc_figure(figs, qc_rows, allele_qc, schemas, cutoffs, width_mm):
    metrics = [
        ("mean_depth", "Depth (own assembly)", cutoffs.get("min_depth", {})),
        ("expected_species_fraction", "Expected species",
         {"": cutoffs.get("min_expected_species_fraction", {}).get("illumina")}),
        ("other_genus_fraction", "Other genus",
         {"": cutoffs.get("max_other_genus_fraction", {}).get("illumina")}),
        ("fraction_called", "Loci called", {}),
    ]
    called = {r["sample"]: r for r in allele_qc}
    rows = []
    for r in qc_rows:
        schema = r.get("schema", "")
        if schema not in schemas:
            continue
        rows.append({**r, "fraction_called": called.get(r["sample"], {}).get("fraction_called", "")})
    if not rows:
        return None
    order = sorted({r["schema"] for r in rows}, key=lambda s: schemas[s]["organism"], reverse=True)
    y_of = {s: i for i, s in enumerate(order)}
    present = [m for m in metrics if any(to_float(r.get(m[0])) is not None for r in rows)]
    if not present:
        return None
    platforms = sorted({r.get("platform", "") for r in rows} & set(PLATFORMS))
    mixed = len(platforms) > 1
    height = 0.3 * len(order) + 0.9
    fig, axes = plt.subplots(1, len(present), figsize=(width_mm * MM, height), sharey=True, squeeze=False,
                             gridspec_kw={"wspace": 0.18})
    for ax, (field, label, lines) in zip(axes[0], present):
        values = [to_float(r.get(field)) for r in rows]
        lines = {k: float(v) for k, v in lines.items() if v not in (None, "") and (not k or k in platforms)}
        limits = [v for v in values if v is not None] + list(lines.values())
        if field == "fraction_called":
            limits += [to_float(schemas[s].get("min_called_fraction")) or 1 for s in order]
        if field == "mean_depth":
            low, high = 0, max(limits) * 1.05
        elif field == "other_genus_fraction":
            low, high = 0, max(limits + [0.05]) * 1.6
        else:
            low = max(0.0, math.floor((min(limits) - 0.02) * 20) / 20)
            high = 1.0
        for schema in order:
            members = [(r, v) for r, v in zip(rows, values) if r["schema"] == schema and v is not None]
            offsets = swarm([v for _, v in members], high - low)
            for (r, value), offset in zip(members, offsets):
                status = r.get("qc_status", "") if r.get("qc_status", "") in QC_STATUS else ""
                platform = r.get("platform", "")
                marker = PLATFORMS[platform][1] if mixed and platform in PLATFORMS else "o"
                point = ax.scatter(value, y_of[schema] + offset, s=14, marker=marker, facecolors=QC_STATUS[status][1],
                                   edgecolors=SURFACE, linewidths=0.4, zorder=3)
                flags = r.get("qc_flags", "")
                figs.tip(point, [
                    f"{r['sample']} ({PLATFORMS.get(platform, (platform,))[0]})" if platform else r["sample"],
                    f"{label}: {qc_value_text(field, value)}",
                    f"QC {QC_STATUS[status][0].lower()}" + (f": {flags}" if flags else ""),
                ])
        if field == "fraction_called":
            for schema in order:
                cutoff = to_float(schemas[schema].get("min_called_fraction"))
                if cutoff is not None:
                    ax.plot([cutoff, cutoff], [y_of[schema] - 0.42, y_of[schema] + 0.42], color=INK2,
                            linewidth=0.8, linestyle=(0, (3, 2)), zorder=2)
        for platform, value in lines.items():
            style_ = PLATFORMS[platform][2] if mixed and platform else (0, (3, 2))
            ax.axvline(value, color=INK2, linewidth=0.8, linestyle=style_, zorder=2)
        ax.set_title(label, loc="left", pad=3)
        ax.grid(axis="x")
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        pad = (high - low) * 0.04
        ax.set_xlim(low - pad, high + pad)
        if field == "mean_depth":
            ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
            ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}×"))
        else:
            ax.xaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 2.5, 5, 10]))
            ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    axes[0, 0].set_yticks(range(len(order)), [species_label(schemas[s]["organism"]) for s in order])
    axes[0, 0].set_ylim(-0.6, len(order) - 0.4)
    statuses = [s for s in QC_STATUS if any((r.get("qc_status", "") if r.get("qc_status", "") in QC_STATUS else "")
                                            == s for r in rows)]
    handles = [Patch(facecolor=QC_STATUS[s][1], edgecolor=QC_STATUS[s][1], label=QC_STATUS[s][0]) for s in statuses]
    if mixed:
        for platform in platforms:
            name, marker, style_ = PLATFORMS[platform]
            handles.append(Line2D([], [], linestyle="none", marker=marker, markersize=4, markerfacecolor=INK2,
                                  markeredgecolor=INK2, label=name))
        for platform in platforms:
            name, _, style_ = PLATFORMS[platform]
            handles.append(Line2D([], [], color=INK2, linewidth=0.8, linestyle=style_, label=f"{name} cut-off"))
    else:
        handles.append(Line2D([], [], color=INK2, linewidth=0.8, linestyle=(0, (3, 2)), label="QC cut-off"))
    top_legend(fig, handles)
    return figs.save(fig, "isolate_qc")


ISOLATE_FIELDS = ["sample", "transmission", "schema", "platform", "reads", "mapped", "mean_depth", "breadth",
                  "contigs", "n50", "reference_ani", "st", "loci_missing", "novel_alleles", "qc_status", "qc_flags"]
ISOLATE_HEADERS = ["Sample", "Group", "Schema", "Platform", "Reads", "Mapped", "Depth", "Breadth", "Contigs", "N50",
                   "ANI to ref. (aligned)", "ST", "Missing loci", "Novel alleles", "QC", "Flags"]


def isolate_qc_rows(qc_rows, allele_qc):
    def percent(value, digits=1):
        number = to_float(value)
        return "" if number is None else f"{number * 100:.{digits}f}%"

    def count(value):
        number = to_float(value)
        return "" if number is None else f"{number:,.0f}"

    alleles = {r["sample"]: r for r in allele_qc}
    rows = []
    for r in qc_rows:
        a = alleles.get(r["sample"], {})
        ani = to_float(r.get("reference_ani"))
        aligned = to_float(r.get("reference_aligned_fraction"))
        rows.append({
            **r,
            "transmission": r.get("transmission") or a.get("transmission", ""),
            "reads": count(r.get("reads")),
            "mapped": percent(r.get("mapped_fraction")),
            "mean_depth": f"{to_float(r['mean_depth']):.0f}x" if to_float(r.get("mean_depth")) is not None else "",
            "breadth": percent(r.get("breadth")),
            "contigs": count(r.get("contigs")),
            "n50": count(r.get("n50")),
            "reference_ani": "" if ani is None else f"{ani:.2f}%" + ("" if aligned is None else f" ({aligned:.0f}%)"),
            "loci_missing": a.get("loci_missing", ""),
            "novel_alleles": a.get("novel_alleles", ""),
        })
    return rows


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text)


def load_schemas(path):
    schemas = {}
    for row in read_tsv(path):
        schemas[row["schema"]] = {
            **row,
            "threshold": to_int(row.get("threshold")),
            "borderline": to_int(row.get("borderline")),
        }
    return schemas


def load_cutoffs(path):
    return {row["metric"]: {"illumina": row.get("illumina"), "nanopore": row.get("nanopore")}
            for row in read_tsv(path)}


def prepare_pairs(rows):
    pairs = []
    for row in rows:
        diffs = to_int(row.get("allele_diffs"))
        if diffs is None or row.get("verdict") not in VERDICTS:
            continue
        pairs.append({
            **row,
            "diffs": diffs,
            "days": to_int(row.get("days_apart")),
            "snps": to_int(row.get("snp_distance")),
            "filtered": row.get("snp_recombination_filtered", ""),
        })
    return pairs


def span_text(values):
    values = [v for v in values if v is not None]
    if not values:
        return ""
    lo, hi = min(values), max(values)
    return str(lo) if lo == hi else f"{lo}–{hi}"


def table1(groups, summary, metadata, pairs_by_group, schemas, environment_types):
    rows = []
    for group in sorted(groups, key=natural_key):
        isolates = [metadata[s] for s in groups[group] if s in metadata]
        kinds = [sample_kind(s, environment_types) for s in isolates]
        dates = sorted(d for d in (parse_date(s.get("date")) for s in isolates) if d)
        info = summary.get(group, {})
        schema_names = [s for s in info.get("schema", "").split(",") if s]
        organism = "; ".join(schemas[s]["organism"] for s in schema_names if s in schemas)
        pairs = pairs_by_group.get(group, [])
        rows.append({
            "transmission": group,
            "species": organism,
            "isolates": len(isolates),
            "environment": kinds.count("environment"),
            "patient": kinds.count("patient"),
            "patients": len({s.get("studypatientnumber", "") for s in isolates} - {""}),
            "first_sample": dates[0].date().isoformat() if dates else "",
            "last_sample": dates[-1].date().isoformat() if dates else "",
            "span_days": (dates[-1] - dates[0]).days if len(dates) > 1 else "",
            "allele_diffs": span_text([p["diffs"] for p in pairs]),
            "snp_distance": span_text([p["snps"] for p in pairs]),
            "pairs": info.get("pairs", ""),
            "pairs_within": info.get("pairs_within", ""),
            "pairs_borderline": info.get("pairs_borderline", ""),
            "overall": info.get("overall", ""),
            "qc": info.get("qc", ""),
        })
    return rows


def write_tsv(path, rows, fields):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


OVERALL = {
    "all_pairs_within": "All pairs within threshold",
    "some_pairs_within": "Some pairs within threshold",
    "no_pairs_within": "No pairs within threshold",
    "incomplete": "Incomplete",
    "single_isolate": "Single isolate",
}
VERDICT_TEXT = {**{k: v[0] for k, v in VERDICTS.items()},
                "missing_profile": "Missing profile", "different_schema": "Different schema"}


def html_table(rows, fields, headers=None, classes=""):
    if not rows:
        return "<p class='empty'>None.</p>"
    headers = headers or fields
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = []
    for row in rows:
        cells = []
        for field in fields:
            value = row.get(field, "")
            text = value if isinstance(value, str) and value.startswith("<") else html.escape(str(value))
            numeric = " class='num'" if re.fullmatch(r"[\d.,–-]+[%x]?", str(value) or "?") else ""
            cells.append(f"<td{numeric}>{text}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (f"<div class='table-wrap'><table class='sortable {classes}'><thead><tr>{head}</tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table></div>")


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def nowrap(text):
    return f"<span class='nowrap'>{html.escape(text)}</span>"


def figure_html(svg, caption, alt, cls=""):
    if not svg:
        return ""
    return (f"<figure class='{cls}'><div class='plot' role='img' aria-label='{html.escape(alt)}'>{svg}</div>"
            f"<figcaption>{caption}</figcaption></figure>")


def badge(verdict):
    cls = {"within_threshold": "within", "borderline": "borderline", "above_threshold": "above",
           "all_pairs_within": "within", "some_pairs_within": "within", "no_pairs_within": "above"}.get(verdict, "other")
    text = VERDICT_TEXT.get(verdict) or OVERALL.get(verdict) or verdict
    return f"<span class='badge {cls}'>{html.escape(text)}</span>"


CSS = """
:root { color-scheme: light; --page: #f9f9f7; --surface: #ffffff; --ink: #0b0b0b; --ink2: #52514e;
  --muted: #898781; --line: #e1e0d9; --within: #eb6834; --borderline: #2a78d6; --above: #898781; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme: dark; --page: #0d0d0d;
  --surface: #1a1a19; --ink: #f0efec; --ink2: #c3c2b7; --line: #2c2c2a; --within: #d95926;
  --borderline: #3987e5; } }
:root[data-theme="dark"] { color-scheme: dark; --page: #0d0d0d; --surface: #1a1a19; --ink: #f0efec;
  --ink2: #c3c2b7; --line: #2c2c2a; --within: #d95926; --borderline: #3987e5; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink); font: 14px/1.5 system-ui, -apple-system,
  "Segoe UI", sans-serif; }
main { max-width: 1200px; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-size: 24px; margin: 0 0 4px; } h2 { font-size: 18px; margin: 40px 0 12px; }
h3 { font-size: 15px; margin: 28px 0 8px; }
.sub { color: var(--ink2); margin: 0 0 24px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.tile { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; }
.tile .value { font-size: 24px; font-weight: 600; } .tile .label { color: var(--ink2); font-size: 13px; }
figure { margin: 16px 0; background: #ffffff; border: 1px solid var(--line); border-radius: 8px; padding: 12px; }
figure .plot svg { display: block; width: 100%; height: auto; margin: 0 auto; }
figure .plot svg * { stroke-linejoin: round; stroke-linecap: butt; }
.pt { cursor: default; }
.pt:hover use, .pt:hover path { stroke: #0b0b0b !important; stroke-width: 1.4px !important; }
.tip { position: fixed; z-index: 10; pointer-events: none; max-width: 320px; padding: 6px 9px; border-radius: 6px;
  background: var(--ink); color: var(--page); font-size: 12px; line-height: 1.4; white-space: pre-line;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2); }
figcaption { color: #52514e; font-size: 13px; margin-top: 8px; }
.table-wrap { overflow-x: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { padding: 6px 10px; text-align: left; border-bottom: 1px solid var(--line); vertical-align: top; }
th { position: sticky; top: 0; background: var(--surface); color: var(--ink2); font-weight: 600; cursor: pointer;
  white-space: nowrap; user-select: none; }
th[aria-sort="ascending"]::after { content: " ▲"; } th[aria-sort="descending"]::after { content: " ▼"; }
td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
tbody tr:last-child td { border-bottom: none; }
.badge { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 12px; white-space: nowrap;
  border: 1px solid currentColor; }
.badge.within { color: var(--within); } .badge.borderline { color: var(--borderline); }
.badge.above, .badge.other { color: var(--ink2); }
.group { border-top: 1px solid var(--line); margin-top: 32px; }
.group-head { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: baseline; }
.empty, .note { color: var(--ink2); }
.nowrap { white-space: nowrap; }
figure.narrow { max-width: 560px; }
nav { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 8px 0 0; font-size: 13px; }
a { color: var(--borderline); }
"""

JS = """
const tip = document.createElement('div');
tip.className = 'tip';
tip.hidden = true;
document.body.appendChild(tip);
const place = event => {
  const x = Math.min(event.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
  const y = event.clientY + 14 + tip.offsetHeight > window.innerHeight
    ? event.clientY - tip.offsetHeight - 10 : event.clientY + 14;
  tip.style.left = `${Math.max(8, x)}px`;
  tip.style.top = `${Math.max(8, y)}px`;
};
document.querySelectorAll('.plot .pt').forEach(point => {
  const title = point.querySelector('title');
  if (!title) return;
  const text = title.textContent;
  title.remove();
  point.addEventListener('pointerenter', event => { tip.textContent = text; tip.hidden = false; place(event); });
  point.addEventListener('pointermove', place);
  point.addEventListener('pointerleave', () => { tip.hidden = true; });
});
document.querySelectorAll('table.sortable').forEach(table => {
  table.querySelectorAll('th').forEach((th, index) => {
    th.addEventListener('click', () => {
      const dir = th.getAttribute('aria-sort') === 'ascending' ? 'descending' : 'ascending';
      table.querySelectorAll('th').forEach(h => h.removeAttribute('aria-sort'));
      th.setAttribute('aria-sort', dir);
      const rows = Array.from(table.tBodies[0].rows);
      const key = row => {
        const text = row.cells[index].textContent.trim();
        const num = parseFloat(text.replace(/,/g, ''));
        return isNaN(num) || !/^[\\d.,–-]+$/.test(text) ? text.toLowerCase() : num;
      };
      rows.sort((a, b) => {
        const x = key(a), y = key(b);
        const cmp = typeof x === typeof y ? (x < y ? -1 : x > y ? 1 : 0) : (typeof x === 'number' ? -1 : 1);
        return dir === 'ascending' ? cmp : -cmp;
      });
      rows.forEach(row => table.tBodies[0].appendChild(row));
    });
  });
});
"""


def build_html(context):
    c = context
    parts = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<title>Transmission report</title><style>{CSS}</style></head><body><main>",
        "<h1>Transmission report</h1>",
        f"<p class='sub'>sinklink {html.escape(c['version'])} · generated {c['generated']}</p>",
        "<div class='tiles'>",
    ]
    for value, label in c["tiles"]:
        parts.append(f"<div class='tile'><div class='value'>{value}</div><div class='label'>{label}</div></div>")
    parts.append("</div>")
    parts.append("<nav>" + "".join(f"<a href='#{a}'>{t}</a>" for a, t in c["nav"]) + "</nav>")

    parts.append("<h2 id='summary'>Transmission groups</h2>")
    parts.append(html_table(c["table1_html"], c["table1_fields"], c["table1_headers"]))
    parts.append("<p class='note'>Allele differences are counted over the loci called in both isolates of a pair. "
                 "A pair at or below its species threshold is the same strain; the dates and patient history decide "
                 "whether a transmission is plausible. SNP distances are for information only.</p>")

    parts.append("<h2 id='overview'>Distances</h2>")
    parts.append(figure_html(c["fig_overview"], "Allele differences for every pair of isolates in each transmission "
                             "group. Dashed lines mark the species threshold; the shaded band is the borderline range. "
                             "Shape shows which kinds of sample the pair joins. Hover over a point to see the pair.",
                             "Allele differences per group"))
    parts.append(figure_html(c["fig_time"], "Allele differences against the days between the two samples of each "
                             "pair, per species.", "Allele differences against time"))
    parts.append(figure_html(c["fig_snp"], "Allele differences against SNP differences from the masked "
                             "pseudogenomes, per species.", "Allele against SNP differences"))
    if c["fig_timelines"]:
        parts.append(figure_html(c["fig_timelines"], "Sampling timeline of every group. Each isolate is joined to "
                                 "the earlier isolate it is closest to, when that pair is at or below the threshold; "
                                 "lines are labelled with the allele differences.", "Timelines"))
    if c["fig_trees"]:
        parts.append(figure_html(c["fig_trees"], "Minimum spanning trees of every group with three or more "
                                 "isolates, from the pairwise allele differences.", "Minimum spanning trees"))

    parts.append("<h2 id='groups'>Groups</h2>")
    for g in c["groups"]:
        parts.append(f"<section class='group' id='g-{html.escape(safe_name(g['name']))}'>")
        parts.append(f"<div class='group-head'><h3>{html.escape(g['name'])}</h3>{g['species']}{badge(g['overall'])}</div>")
        parts.append(f"<p class='note'>{g['line']}</p>")
        parts.append(figure_html(g["timeline"], "Each isolate is joined to the earlier isolate it is closest to, "
                                 "when within the threshold.", f"{g['name']} timeline"))
        parts.append(figure_html(g["tree"], "Minimum spanning tree from the pairwise allele differences.",
                                 f"{g['name']} tree", "narrow"))
        parts.append(html_table(g["pairs"], c["pair_fields"], c["pair_headers"]))
        parts.append("</section>")

    if c["fig_qc"] or c["fig_sample_qc"] or c["isolates"]:
        parts.append("<h2 id='qc'>Isolate QC</h2>")
        parts.append(figure_html(c["fig_sample_qc"], "Isolates by read and assembly QC status (qc_summary.tsv), per "
                                 "species and per kind of sample; the number after each bar is the total.",
                                 "Isolates by QC status"))
    if c["fig_qc"]:
        parts.append(figure_html(c["fig_qc"], "Mean read depth over the isolate's own assembly, the share of reads "
                                 "from the species the schema covers, the largest share from another genus, and the "
                                 "share of schema loci called, per isolate, coloured by QC status. Dashed lines are the "
                                 "QC cut-offs. Hover over a point to see the isolate.", "Isolate QC"))
    if c["isolates"]:
        parts.append("<h3>Every isolate</h3>")
        parts.append("<p class='note'>Reads, mapped reads, depth and breadth come from mapping each isolate's reads "
                     "back to its own assembly. ANI is skani's, from the assembly to the schema's reference genome, "
                     "with the share of the assembly aligned. Missing loci are schema loci without a valid call; "
                     "novel alleles are calls not yet in the schema, and many of them in one isolate often point "
                     "to sequencing or assembly errors rather than real differences.</p>")
        parts.append(html_table(c["isolates"], ISOLATE_FIELDS, ISOLATE_HEADERS))
    if c["failed"]:
        parts.append("<h3>Isolates that failed QC or have no allele profile</h3>")
        parts.append(html_table(c["failed"], ["sample", "transmission", "schema", "qc", "assembly_qc", "assembly_flags"],
                                ["Sample", "Group", "Schema", "Allele QC", "Assembly QC", "Assembly flags"]))

    parts.append("<h2 id='methods'>Thresholds</h2>")
    parts.append(html_table(c["thresholds"], ["species", "scheme", "threshold", "source"],
                            ["Species", "Scheme", "Threshold (alleles)", "Source"]))
    parts.append(f"<p class='note'>Figures are in <code>figures/</code> as {html.escape(c['formats'])}. "
                 "The minimum spanning trees use the pairwise distances over loci shared by each pair; where several "
                 "trees are equally short, one is shown.</p>")
    parts.append(f"<script>{JS}</script></main></body></html>")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", required=True, help="pairwise_distances.tsv")
    parser.add_argument("--groups", required=True, help="group_summary.tsv")
    parser.add_argument("--allele-qc", help="allele_qc.tsv")
    parser.add_argument("--qc-summary", help="qc_summary.tsv")
    parser.add_argument("--metadata", required=True, help="study metadata CSV")
    parser.add_argument("--schemas", required=True, help="assets/schemas.tsv")
    parser.add_argument("--qc-thresholds", help="assets/qc_thresholds.tsv")
    parser.add_argument("--outdir", default=".")
    parser.add_argument("--formats", default="pdf,svg,png", help="comma-separated: pdf, svg, png")
    parser.add_argument("--dpi", type=int, default=300, help="resolution of the PNG figures")
    parser.add_argument("--width-mm", type=float, default=180, help="width of full-width figures")
    parser.add_argument("--font-size", type=float, default=7)
    parser.add_argument("--environment-types", default="environment",
                        help="comma-separated sample_type values that are environmental samples")
    parser.add_argument("--pipeline-version", default="")
    args = parser.parse_args()

    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    environment_types = {t.strip().lower() for t in args.environment_types.split(",") if t.strip()}
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    style(args.font_size)
    figs = Figures(outdir, formats, args.dpi)

    metadata = read_metadata(args.metadata)
    schemas = load_schemas(args.schemas)
    cutoffs = load_cutoffs(args.qc_thresholds)
    raw_pairs = read_tsv(args.pairs)
    pairs = prepare_pairs(raw_pairs)
    summary = {r["transmission"]: r for r in read_tsv(args.groups)}
    allele_qc = read_tsv(args.allele_qc)
    qc_rows = read_tsv(args.qc_summary)

    groups = {}
    for sid, sample in metadata.items():
        groups.setdefault(sample["transmission"], []).append(sid)
    pairs_by_group, rows_by_schema = {}, {}
    for pair in pairs:
        pairs_by_group.setdefault(pair["transmission"], []).append(pair)
        if pair["schema"] in schemas:
            rows_by_schema.setdefault(pair["schema"], []).append(pair)

    fig_overview = overview_figure(figs, rows_by_schema, schemas, args.width_mm, environment_types) if rows_by_schema else None
    fig_time = time_figure(figs, rows_by_schema, schemas, args.width_mm, environment_types) if rows_by_schema else None
    fig_snp = snp_figure(figs, rows_by_schema, schemas, args.width_mm, environment_types) if rows_by_schema else None
    timelines = timeline_figures(figs, groups, metadata, pairs_by_group, args.width_mm, environment_types)
    trees = tree_figures(figs, groups, metadata, pairs_by_group, args.width_mm, environment_types)
    fig_sample_qc, qc_counts = sample_qc_figure(figs, metadata, qc_rows, schemas, args.width_mm, environment_types)
    fig_qc = qc_figure(figs, qc_rows, allele_qc, schemas, cutoffs, args.width_mm)

    table_rows = table1(groups, summary, metadata, pairs_by_group, schemas, environment_types)
    table_fields = list(table_rows[0]) if table_rows else ["transmission"]
    write_tsv(outdir / "table1.tsv", table_rows, table_fields)

    all_pairs_by_group = {}
    for row in raw_pairs:
        all_pairs_by_group.setdefault(row["transmission"], []).append(row)
    group_contexts = []
    for row in table_rows:
        name = row["transmission"]
        pair_rows = [{**p, "verdict_html": badge(p["verdict"]) if p.get("verdict") else ""}
                     for p in all_pairs_by_group.get(name, [])]
        dates = f"{row['first_sample']} to {row['last_sample']}" if row["first_sample"] else "no dates"
        line = (f"{plural(row['isolates'], 'isolate')} ({row['environment']} environment, {row['patient']} patient) "
                f"from {plural(row['patients'], 'patient')}, {dates}. Allele differences {row['allele_diffs'] or 'not available'}"
                + (f", SNPs {row['snp_distance']}" if row["snp_distance"] else "") + ".")
        group_contexts.append({
            "name": name,
            "species": species_html(row["species"]) if row["species"] else "",
            "overall": row["overall"],
            "line": html.escape(line),
            "timeline": timelines.get(name),
            "tree": trees.get(name),
            "pairs": pair_rows,
        })

    used = {p["schema"] for p in pairs} | {s for r in summary.values() for s in r.get("schema", "").split(",") if s}
    threshold_rows = [{"species": species_html(schemas[s]["organism"]), "scheme": schemas[s].get("scheme", ""),
                       "threshold": threshold_text(schemas[s]).replace("threshold ", ""), "source": schemas[s].get("source", "")}
                      for s in sorted(used & set(schemas), key=lambda s: schemas[s]["organism"])]
    failed = [{**r, "transmission": r.get("transmission", "")} for r in allele_qc if r.get("qc") and r["qc"] != "pass"]
    isolates = isolate_qc_rows(qc_rows, allele_qc)
    n_within = sum(1 for p in pairs if p["verdict"] == "within_threshold")
    n_env_patient_within = sum(1 for p in pairs if p["verdict"] == "within_threshold"
                               and pair_kind(p, environment_types) == "environment-patient")
    table_html = [{**r, "species": species_html(r["species"]) if r["species"] else "",
                   "isolates_text": nowrap(f"{r['isolates']} ({r['environment']} env / {r['patient']} patient)"),
                   "dates": nowrap(f"{r['first_sample']} to {r['last_sample']}") if r["first_sample"] else "",
                   "overall": badge(r["overall"]) if r["overall"] else ""} for r in table_rows]
    nav = [("summary", "Groups table"), ("overview", "Figures"), ("groups", "Each group")]
    if fig_qc or (fig_sample_qc and qc_rows) or isolates:
        nav.append(("qc", "Isolate QC"))
    nav.append(("methods", "Thresholds"))

    context = {
        "version": args.pipeline_version or "",
        "generated": date.today().isoformat(),
        "tiles": [
            (len(groups), "transmission groups"),
            (len(metadata), "isolates"),
            (qc_counts.get("pass", 0) if qc_rows else "–", "isolates passing QC"),
            (len(pairs), "pairs with a distance"),
            (n_within, "pairs within threshold"),
            (n_env_patient_within, "environment–patient pairs within threshold"),
        ],
        "nav": nav,
        "table1_html": table_html,
        "table1_fields": ["transmission", "species", "isolates_text", "patients", "dates", "span_days",
                          "allele_diffs", "snp_distance", "overall", "qc"],
        "table1_headers": ["Group", "Species", "Isolates", "Patients", "Sampled", "Days", "Allele diffs", "SNPs",
                           "Verdict", "QC"],
        "fig_overview": fig_overview,
        "fig_time": fig_time,
        "fig_snp": fig_snp,
        "fig_timelines": timelines.get("_all"),
        "fig_trees": trees.get("_all"),
        "fig_qc": fig_qc,
        "fig_sample_qc": fig_sample_qc if qc_rows else None,
        "groups": group_contexts,
        "pair_fields": ["sample_a", "sample_b", "type_a", "type_b", "days_apart", "shared_loci", "allele_diffs",
                        "threshold", "verdict_html", "snp_distance", "qc", "notes"],
        "pair_headers": ["Sample A", "Sample B", "Type A", "Type B", "Days", "Shared loci", "Allele diffs",
                         "Threshold", "Verdict", "SNPs", "QC", "Notes"],
        "failed": failed,
        "isolates": isolates,
        "thresholds": threshold_rows,
        "formats": ", ".join(f.upper() for f in formats),
    }
    (outdir / "transmission_report.html").write_text(build_html(context), encoding="utf-8")
    print(f"Written to {outdir}: transmission_report.html, table1.tsv and {len(list(figs.dir.iterdir()))} figure files")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Summarise read and assembly QC for one isolate and check it against thresholds.

Reads QUAST, samtools coverage and flagstat, gambitcore, Kraken2/Bracken, mlst,
Mash and skani output for one isolate, checks them against assets/qc_thresholds.tsv and the species,
genome size and reference genome expectations for its schema in
assets/schemas.tsv, and writes a one-row TSV. Rows from all isolates are concatenated into qc_summary.tsv.
"""

import argparse
import csv
import re
import sys


FIELDS = [
    "sample", "transmission", "growth", "schema", "platform",
    "assembly_length", "contigs", "n50", "gc",
    "reads", "mapped_fraction", "mean_depth", "breadth",
    "reference", "reference_ani", "reference_aligned_fraction", "reference_distance", "genome_fraction",
    "gambit_species", "completeness", "gambit_qc",
    "species_source", "top_species", "top_species_fraction",
    "expected_species_fraction", "other_genus_fraction",
    "mlst_scheme", "st", "qc_status", "qc_flags",
]


def read_tsv(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def to_float(value):
    try:
        return float(str(value).strip().rstrip("%"))
    except (TypeError, ValueError):
        return None


def quast_metrics(path):
    """Parse QUAST report.tsv (one metric per row) or transposed_report.tsv."""
    if not path:
        return {}
    with open(path, newline="") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    if not rows:
        return {}
    if rows[0] and rows[0][0] == "Assembly" and len(rows[0]) > 2 and len(rows) == 2:
        metrics = dict(zip(rows[0], rows[1]))
    else:
        metrics = {row[0]: row[1] for row in rows if len(row) >= 2}
    return {
        "assembly_length": to_float(metrics.get("Total length")),
        "contigs": to_float(metrics.get("# contigs")),
        "n50": to_float(metrics.get("N50")),
        "gc": to_float(metrics.get("GC (%)")),
        "genome_fraction": to_float(metrics.get("Genome fraction (%)")),
    }


def coverage_metrics(path):
    """Length-weighted mean depth and the share of assembly bases covered, from samtools coverage."""
    if not path:
        return None, None
    total_length = weighted = covered = 0.0
    for row in read_tsv(path):
        length = to_float(row.get("endpos"))
        depth = to_float(row.get("meandepth"))
        bases = to_float(row.get("covbases"))
        if length and depth is not None:
            total_length += length
            weighted += length * depth
            covered += bases or 0.0
    if not total_length:
        return None, None
    return weighted / total_length, covered / total_length


def flagstat_metrics(path):
    """Primary reads and the share of them mapped, from samtools flagstat."""
    if not path:
        return None, None
    counts = {}
    with open(path) as handle:
        for line in handle:
            match = re.match(r"(\d+) \+ (\d+) (.+?)(?: \(|$)", line.strip())
            if match:
                counts[match.group(3).strip()] = int(match.group(1)) + int(match.group(2))
    if "primary" in counts:
        reads, mapped = counts["primary"], counts.get("primary mapped")
    elif "in total (QC-passed reads + QC-failed reads)" in counts:
        extra = counts.get("secondary", 0) + counts.get("supplementary", 0)
        reads = counts["in total (QC-passed reads + QC-failed reads)"] - extra
        mapped = counts["mapped"] - extra if "mapped" in counts else None
    else:
        return None, None
    return reads, (mapped / reads if reads and mapped is not None else None)


def skani_ani(path):
    """(ANI %, aligned fraction of the assembly %) from skani dist, or (None, None) when skani
    reports no hit, which it does below about 80% ANI."""
    if not path:
        return None, None
    rows = read_tsv(path)
    if not rows:
        return None, None
    return to_float(rows[0].get("ANI")), to_float(rows[0].get("Align_fraction_query"))


def gambitcore_metrics(path):
    if not path:
        return {}
    rows = read_tsv(path)
    if not rows:
        return {}
    row = {k.strip(): v for k, v in rows[0].items() if k}
    return {
        "gambit_species": row.get("Species", ""),
        "completeness": to_float(row.get("Completeness (%)")),
        "gambit_qc": row.get("Assembly QC", ""),
    }


def species_fractions(bracken, kraken_report):
    """Return (source, [(species, fraction)]) from Bracken, else the Kraken2 report."""
    if bracken:
        return "bracken", [
            (row["name"].strip(), to_float(row["fraction_total_reads"]) or 0.0)
            for row in read_tsv(bracken)
        ]
    if kraken_report:
        species = []
        with open(kraken_report) as handle:
            for line in handle:
                fields = line.rstrip("\n").split("\t")
                if len(fields) >= 6 and fields[3] == "S":
                    species.append((fields[5].strip(), (to_float(fields[0]) or 0.0) / 100))
        return "kraken2", species
    return "", []


def mash_distance(path):
    """Distance from `mash dist reference query` output (reference, query, distance, ...)."""
    if not path:
        return None
    with open(path) as handle:
        fields = handle.readline().rstrip("\n").split("\t")
    return to_float(fields[2]) if len(fields) >= 3 else None


def mlst_result(path):
    if not path:
        return "", ""
    with open(path) as handle:
        fields = handle.readline().rstrip("\n").split("\t")
    if len(fields) < 3:
        return "", ""
    return fields[1], fields[2]


def fmt(value, digits=0):
    return "" if value is None else f"{value:.{digits}f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--platform", required=True, choices=["illumina", "nanopore"])
    parser.add_argument("--schema", default="")
    parser.add_argument("--growth", default="")
    parser.add_argument("--transmission", default="")
    parser.add_argument("--reference", default="", help="reference genome accession")
    parser.add_argument("--schemas", required=True, help="assets/schemas.tsv")
    parser.add_argument("--thresholds", required=True, help="assets/qc_thresholds.tsv")
    parser.add_argument("--assembly")
    parser.add_argument("--quast", help="QUAST report.tsv")
    parser.add_argument("--coverage", help="samtools coverage output")
    parser.add_argument("--flagstat", help="samtools flagstat output")
    parser.add_argument("--gambitcore")
    parser.add_argument("--bracken", help="Bracken species-level output")
    parser.add_argument("--kraken-report")
    parser.add_argument("--mlst", help="mlst TSV output")
    parser.add_argument("--mash", help="mash dist output, reference against assembly")
    parser.add_argument("--ani", help="skani dist output, assembly against reference")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    schema_info = {r["schema"]: r for r in read_tsv(args.schemas)}.get(args.schema, {})
    thresholds = {r["metric"]: r for r in read_tsv(args.thresholds)}
    platform = args.platform
    flags = []

    def limit(metric):
        row = thresholds.get(metric)
        return (to_float(row.get(platform)), row["severity"]) if row else (None, "warn")

    def check(severity, name, failed):
        if failed:
            flags.append((severity, name))

    quast = quast_metrics(args.quast)
    depth, breadth = coverage_metrics(args.coverage)
    reads, mapped_fraction = flagstat_metrics(args.flagstat)
    ani, ani_aligned = skani_ani(args.ani)
    gambit = gambitcore_metrics(args.gambitcore)
    source, fractions = species_fractions(args.bracken, args.kraken_report)
    mlst_scheme, st = mlst_result(args.mlst)
    ref_distance = mash_distance(args.mash)

    has_assembly = bool(args.assembly)
    check("fail", "no_assembly", not has_assembly)
    check("warn", "no_schema", not args.schema)

    value, severity = limit("min_depth")
    if depth is None:
        check("warn", "depth_not_measured", has_assembly)
    elif value is not None:
        check(severity, f"low_depth({depth:.0f}x<{value:g}x)", depth < value)

    value, severity = limit("min_mapped_fraction")
    if mapped_fraction is not None and value is not None:
        check(severity, f"low_mapped_reads({mapped_fraction:.2f}<{value:g})", mapped_fraction < value)

    value, severity = limit("max_contigs")
    contigs = quast.get("contigs")
    if contigs is not None and value is not None:
        check(severity, f"many_contigs({contigs:.0f}>{value:g})", contigs > value)

    value, severity = limit("min_n50")
    n50 = quast.get("n50")
    if n50 is not None and value is not None:
        check(severity, f"low_n50({n50:.0f}<{value:g})", n50 < value)

    length = quast.get("assembly_length")
    size_min = to_float(schema_info.get("genome_size_min_mb"))
    size_max = to_float(schema_info.get("genome_size_max_mb"))
    if length is not None and size_min is not None and size_max is not None:
        mb = length / 1e6
        _, severity = limit("genome_size")
        check(severity, f"genome_size({mb:.2f}Mb not {size_min:g}-{size_max:g})",
              not size_min <= mb <= size_max)

    value, severity = limit("min_completeness")
    completeness = gambit.get("completeness")
    if completeness is not None and value is not None:
        check(severity, f"low_completeness({completeness:.1f}%<{value:g}%)", completeness < value)

    value, severity = limit("min_reference_ani")
    if args.ani and value is not None:
        if ani is None:
            check(severity, "distant_reference(ANI<80%)", True)
        else:
            check(severity, f"distant_reference(ANI {ani:.2f}%<{value:g}%)", ani < value)
    else:
        value, severity = limit("max_reference_distance")
        if ref_distance is not None and value is not None:
            check(severity, f"distant_reference({ref_distance:.3f}>{value:g})", ref_distance > value)

    top_species = top_fraction = expected_fraction = other_genus = None
    if fractions:
        top_species, top_fraction = max(fractions, key=lambda item: item[1])
        pattern = schema_info.get("species_pattern")
        genera = {g.strip() for g in schema_info.get("genera", "").split(",") if g.strip()}
        if pattern:
            regex = re.compile(pattern)
            expected_fraction = sum(f for name, f in fractions if regex.search(name))
            value, severity = limit("min_expected_species_fraction")
            if value is not None:
                check(severity, f"species_mismatch(top {top_species} {top_fraction:.2f})",
                      expected_fraction < value)
        if genera:
            by_genus = {}
            for name, fraction in fractions:
                genus = name.split()[0] if name else ""
                if genus not in genera:
                    by_genus[genus] = by_genus.get(genus, 0.0) + fraction
            other_genus = 0.0
            if by_genus:
                genus, other_genus = max(by_genus.items(), key=lambda item: item[1])
                value, severity = limit("max_other_genus_fraction")
                if value is not None:
                    check(severity, f"contamination({genus} {other_genus:.2f})", other_genus > value)
    elif has_assembly:
        check("warn", "species_not_checked", True)

    severities = {severity for severity, _ in flags}
    status = "fail" if "fail" in severities else "warn" if "warn" in severities else "pass"

    row = {
        "sample": args.id,
        "transmission": args.transmission,
        "growth": args.growth,
        "schema": args.schema,
        "platform": platform,
        "assembly_length": fmt(length),
        "contigs": fmt(contigs),
        "n50": fmt(n50),
        "gc": fmt(quast.get("gc"), 2),
        "reads": fmt(reads),
        "mapped_fraction": fmt(mapped_fraction, 3),
        "mean_depth": fmt(depth, 1),
        "breadth": fmt(breadth, 3),
        "reference": args.reference,
        "reference_ani": fmt(ani, 2),
        "reference_aligned_fraction": fmt(ani_aligned, 1),
        "reference_distance": fmt(ref_distance, 4),
        "genome_fraction": fmt(quast.get("genome_fraction"), 2),
        "gambit_species": gambit.get("gambit_species", ""),
        "completeness": fmt(completeness, 2),
        "gambit_qc": gambit.get("gambit_qc", ""),
        "species_source": source,
        "top_species": top_species or "",
        "top_species_fraction": fmt(top_fraction, 3),
        "expected_species_fraction": fmt(expected_fraction, 3),
        "other_genus_fraction": fmt(other_genus, 3),
        "mlst_scheme": mlst_scheme,
        "st": st,
        "qc_status": status,
        "qc_flags": "; ".join(f"{severity}:{name}" for severity, name in flags),
    }
    with open(args.output, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)
    if row["qc_flags"]:
        print(f"{args.id}: {row['qc_flags']}", file=sys.stderr)


if __name__ == "__main__":
    main()

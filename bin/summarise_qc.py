#!/usr/bin/env python3
"""Summarise read and assembly QC per isolate and check it against thresholds.

Collects QUAST, read depth (samtools coverage), gambitcore, Kraken2/Bracken and
MLST results from the sinklink output folder, checks them against
assets/qc_thresholds.tsv and the species/genome size expectations in
assets/schemas.tsv, and writes qc_summary.tsv.
"""

import argparse
import csv
import re
import sys
from pathlib import Path


def read_tsv(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(value):
    try:
        return float(str(value).strip().rstrip("%"))
    except (TypeError, ValueError):
        return None


def quast_metrics(sample_dir):
    path = sample_dir / "quast" / "transposed_report.tsv"
    if not path.is_file():
        return {}
    rows = read_tsv(path)
    if not rows:
        return {}
    row = rows[0]
    return {
        "assembly_length": to_float(row.get("Total length")),
        "contigs": to_float(row.get("# contigs")),
        "n50": to_float(row.get("N50")),
        "gc": to_float(row.get("GC (%)")),
    }


def mean_depth(sample_dir, sample_id):
    path = sample_dir / "mapping" / f"{sample_id}.coverage.tsv"
    if not path.is_file():
        return None
    total_length = weighted = 0.0
    with open(path, newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            length = to_float(row.get("endpos"))
            depth = to_float(row.get("meandepth"))
            if length and depth is not None:
                total_length += length
                weighted += length * depth
    return weighted / total_length if total_length else None


def gambitcore_metrics(sample_dir, sample_id):
    path = sample_dir / "gambitcore" / f"{sample_id}.tsv"
    if not path.is_file():
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


def species_fractions(sample_dir, sample_id):
    """Return [(species, fraction)] from Bracken, or from the Kraken2 report."""
    bracken = sample_dir / "kraken" / f"{sample_id}.bracken.tsv"
    if bracken.is_file():
        return "bracken", [
            (row["name"].strip(), to_float(row["fraction_total_reads"]) or 0.0)
            for row in read_tsv(bracken)
        ]
    report = sample_dir / "kraken" / f"{sample_id}.kraken.report"
    if report.is_file():
        species = []
        with open(report) as handle:
            for line in handle:
                fields = line.rstrip("\n").split("\t")
                if len(fields) >= 6 and fields[3] == "S":
                    species.append((fields[5].strip(), (to_float(fields[0]) or 0.0) / 100))
        return "kraken2", species
    return "", []


def mlst_result(sample_dir, sample_id):
    path = sample_dir / "mlst" / f"{sample_id}.tsv"
    if not path.is_file():
        return "", ""
    with open(path) as handle:
        fields = handle.readline().rstrip("\n").split("\t")
    if len(fields) < 3:
        return "", ""
    return fields[1], fields[2]


def check(flags, severity, name, failed):
    if failed:
        flags.append((severity, name))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reads", required=True, help="reads sheet (id,platform,read1,read2)")
    parser.add_argument("--samplesheet", required=True)
    parser.add_argument("--results", required=True, help="output folder of sinklink.sh")
    parser.add_argument("--species-map", required=True)
    parser.add_argument("--schemas", required=True)
    parser.add_argument("--thresholds", required=True)
    args = parser.parse_args()

    results = Path(args.results)
    species_map = {r["growth"]: r["schema"] for r in read_tsv(args.species_map)}
    schemas = {r["schema"]: r for r in read_tsv(args.schemas)}
    study = {r["translation_id"]: r for r in read_csv(args.samplesheet)}
    thresholds = {r["metric"]: r for r in read_tsv(args.thresholds)}

    def limit(metric, platform):
        row = thresholds.get(metric)
        return (to_float(row.get(platform)), row["severity"]) if row else (None, "warn")

    rows = []
    for sample in read_csv(args.reads):
        sid = sample["id"].strip()
        platform = sample["platform"].strip()
        info = study.get(sid, {})
        schema = species_map.get(info.get("growth", ""), "")
        schema_info = schemas.get(schema, {})
        sample_dir = results / "samples" / sid
        flags = []

        quast = quast_metrics(sample_dir)
        depth = mean_depth(sample_dir, sid)
        gambit = gambitcore_metrics(sample_dir, sid)
        source, fractions = species_fractions(sample_dir, sid)
        mlst_scheme, st = mlst_result(sample_dir, sid)

        has_assembly = (sample_dir / "assembly" / f"{sid}.fasta").is_file()
        check(flags, "fail", "no_assembly", not has_assembly)
        check(flags, "warn", "no_schema", not schema)

        value, severity = limit("min_depth", platform)
        if depth is None:
            check(flags, "warn", "depth_not_measured", has_assembly)
        elif value is not None:
            check(flags, severity, f"low_depth({depth:.0f}x<{value:g}x)", depth < value)

        value, severity = limit("max_contigs", platform)
        contigs = quast.get("contigs")
        if contigs is not None and value is not None:
            check(flags, severity, f"many_contigs({contigs:.0f}>{value:g})", contigs > value)

        value, severity = limit("min_n50", platform)
        n50 = quast.get("n50")
        if n50 is not None and value is not None:
            check(flags, severity, f"low_n50({n50:.0f}<{value:g})", n50 < value)

        length = quast.get("assembly_length")
        size_min = to_float(schema_info.get("genome_size_min_mb"))
        size_max = to_float(schema_info.get("genome_size_max_mb"))
        if length is not None and size_min is not None and size_max is not None:
            mb = length / 1e6
            _, severity = limit("genome_size", platform)
            check(flags, severity, f"genome_size({mb:.2f}Mb not {size_min:g}-{size_max:g})",
                  not size_min <= mb <= size_max)

        value, severity = limit("min_completeness", platform)
        completeness = gambit.get("completeness")
        if completeness is not None and value is not None:
            check(flags, severity, f"low_completeness({completeness:.1f}%<{value:g}%)",
                  completeness < value)

        top_species = top_fraction = expected_fraction = other_genus = None
        if fractions:
            top_species, top_fraction = max(fractions, key=lambda item: item[1])
            pattern = schema_info.get("species_pattern")
            genera = {g.strip() for g in schema_info.get("genera", "").split(",") if g.strip()}
            if pattern:
                regex = re.compile(pattern)
                expected_fraction = sum(f for name, f in fractions if regex.search(name))
                value, severity = limit("min_expected_species_fraction", platform)
                if value is not None:
                    check(flags, severity,
                          f"species_mismatch(top {top_species} {top_fraction:.2f})",
                          expected_fraction < value)
            if genera:
                by_genus = {}
                for name, fraction in fractions:
                    genus = name.split()[0] if name else ""
                    if genus not in genera:
                        by_genus[genus] = by_genus.get(genus, 0.0) + fraction
                if by_genus:
                    genus, other_genus = max(by_genus.items(), key=lambda item: item[1])
                    value, severity = limit("max_other_genus_fraction", platform)
                    if value is not None:
                        check(flags, severity, f"contamination({genus} {other_genus:.2f})",
                              other_genus > value)
                else:
                    other_genus = 0.0
        elif has_assembly:
            check(flags, "warn", "species_not_checked", True)

        severities = {severity for severity, _ in flags}
        status = "fail" if "fail" in severities else "warn" if "warn" in severities else "pass"

        def fmt(value, digits=0):
            return "" if value is None else f"{value:.{digits}f}"

        rows.append({
            "translation_id": sid,
            "transmission": info.get("transmission", ""),
            "growth": info.get("growth", ""),
            "schema": schema,
            "platform": platform,
            "assembly_length": fmt(length),
            "contigs": fmt(contigs),
            "n50": fmt(n50),
            "gc": fmt(quast.get("gc"), 2),
            "mean_depth": fmt(depth, 1),
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
        })

    if not rows:
        sys.exit("no isolates in the reads sheet")
    out = results / "qc_summary.tsv"
    with open(out, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    fields = ["translation_id", "platform", "schema", "contigs", "n50", "mean_depth",
              "top_species", "st", "qc_status"]
    widths = {f: max(len(f), *(len(r[f]) for r in rows)) for f in fields}
    print("  ".join(f.ljust(widths[f]) for f in fields))
    for row in rows:
        print("  ".join(row[f].ljust(widths[f]) for f in fields))
    for row in rows:
        if row["qc_flags"]:
            print(f"{row['translation_id']}: {row['qc_flags']}", file=sys.stderr)
    print(f"\nWritten to {out}")


if __name__ == "__main__":
    main()

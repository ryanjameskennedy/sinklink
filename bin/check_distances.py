#!/usr/bin/env python3
"""Compare chewBBACA allele profiles within each transmission group.

For every pair of isolates in a group, counts allele differences over the loci
called in both isolates and compares the count with the species threshold in
assets/schemas.tsv. Read and assembly QC from qc_summary.tsv (summarise_qc.py)
is carried into each pair. Writes allele_qc.tsv, pairwise_distances.tsv and
group_summary.tsv.
"""

import argparse
import csv
import sys
from datetime import datetime
from itertools import combinations
from pathlib import Path


def read_tsv(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def parse_date(value):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            pass
    return None


def normalise_call(value):
    """Return the allele ID for a valid call, or None for missing/ambiguous calls.

    Novel alleles keep their '*' so they never match a schema allele with the
    same number.
    """
    value = value.strip()
    if value.startswith("INF-"):
        value = value[4:]
    return value if value.lstrip("*").isdigit() else None


def schema_of_alleles(path):
    name = Path(path).name
    suffix = "_results_alleles.tsv"
    return name[: -len(suffix)] if name.endswith(suffix) else None


def load_profiles(path):
    if not path:
        return None, {}
    with open(path, newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader)
        loci = header[1:]
        profiles = {}
        for row in reader:
            sample = row[0]
            for ext in (".fasta", ".fna", ".fa"):
                if sample.endswith(ext):
                    sample = sample[: -len(ext)]
            profiles[sample] = {
                locus: allele
                for locus, allele in zip(loci, (normalise_call(v) for v in row[1:]))
                if allele is not None
            }
    return len(loci), profiles


def compare(a, b):
    shared = a.keys() & b.keys()
    return len(shared), sum(1 for locus in shared if a[locus] != b[locus])


def verdict(diffs, threshold, borderline):
    if diffs <= threshold:
        return "within_threshold"
    if borderline is not None and diffs <= borderline:
        return "borderline"
    return "above_threshold"


def write_tsv(path, rows, fields):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def print_table(rows, fields):
    widths = {f: max(len(f), *(len(str(r[f])) for r in rows)) for f in fields}
    print("  ".join(f.ljust(widths[f]) for f in fields))
    for row in rows:
        print("  ".join(str(row[f]).ljust(widths[f]) for f in fields))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samplesheet", required=True)
    parser.add_argument("--alleles", nargs="*", default=[],
                        help="chewBBACA allele tables named <schema>_results_alleles.tsv")
    parser.add_argument("--outdir", default=".", help="where to write the tables")
    parser.add_argument("--qc-summary", help="qc_summary.tsv from summarise_qc.py")
    parser.add_argument("--species-map", required=True)
    parser.add_argument("--schemas", required=True)
    args = parser.parse_args()

    out_dir = Path(args.outdir)
    allele_files = {}
    for path in args.alleles:
        schema = schema_of_alleles(path)
        if schema is None:
            sys.exit(f"cannot tell the schema from {path}; expected <schema>_results_alleles.tsv")
        allele_files[schema] = path
    assembly_qc = {}
    if args.qc_summary and Path(args.qc_summary).is_file():
        assembly_qc = {r["translation_id"]: r for r in read_tsv(args.qc_summary)}
    species_map = {r["growth"]: r for r in read_tsv(args.species_map)}
    schemas = {r["schema"]: r for r in read_tsv(args.schemas)}
    with open(args.samplesheet, newline="", encoding="utf-8-sig") as handle:
        samples = list(csv.DictReader(handle))

    profiles, n_loci = {}, {}
    for schema in schemas:
        n_loci[schema], profiles[schema] = load_profiles(allele_files.get(schema))

    qc_rows, sample_info = [], {}
    for sample in samples:
        sid = sample["translation_id"]
        mapping = species_map.get(sample["growth"])
        schema = mapping["schema"] if mapping else ""
        profile = profiles.get(schema, {}).get(sid)
        min_called = schemas[schema]["min_called_fraction"] if schema else ""
        called = len(profile) if profile is not None else 0
        fraction = called / n_loci[schema] if profile is not None and n_loci[schema] else 0
        if not schema:
            qc = "no_schema"
        elif profile is None:
            qc = "no_profile"
        elif min_called and fraction < float(min_called):
            qc = "low_calls"
        else:
            qc = "pass"
        aqc = assembly_qc.get(sid, {})
        sample_info[sid] = {
            **sample,
            "schema": schema,
            "profile": profile,
            "qc": qc,
            "assembly_qc": aqc.get("qc_status", ""),
            "assembly_flags": aqc.get("qc_flags", ""),
            "platform": aqc.get("platform", ""),
            "st": aqc.get("st", ""),
        }
        qc_rows.append({
            "translation_id": sid,
            "transmission": sample["transmission"],
            "growth": sample["growth"],
            "schema": schema,
            "loci_called": called,
            "loci_in_schema": n_loci.get(schema) or "",
            "fraction_called": f"{fraction:.3f}",
            "qc": qc,
            "assembly_qc": sample_info[sid]["assembly_qc"],
            "assembly_flags": sample_info[sid]["assembly_flags"],
        })

    groups = {}
    for sample in samples:
        groups.setdefault(sample["transmission"], []).append(sample["translation_id"])

    pair_rows = []
    for group, ids in groups.items():
        for id_a, id_b in combinations(ids, 2):
            a, b = sample_info[id_a], sample_info[id_b]
            row = {
                "transmission": group,
                "sample_a": id_a,
                "sample_b": id_b,
                "type_a": a.get("sample", ""),
                "type_b": b.get("sample", ""),
                "patient_a": a.get("studypatientnumber", ""),
                "patient_b": b.get("studypatientnumber", ""),
                "days_apart": "",
                "schema": a["schema"] if a["schema"] == b["schema"] else f"{a['schema']}/{b['schema']}",
                "shared_loci": "",
                "allele_diffs": "",
                "threshold": "",
                "verdict": "",
                "qc": "",
                "notes": "",
            }
            date_a, date_b = parse_date(a.get("date", "")), parse_date(b.get("date", ""))
            if date_a and date_b:
                row["days_apart"] = abs((date_b - date_a).days)

            notes = {species_map[s["growth"]]["note"] for s in (a, b)
                     if s["growth"] in species_map and species_map[s["growth"]]["note"]}
            if a["schema"] == "smaltophilia":
                notes.add("wgMLST distance over loci shared by both; Groschel used 1275 core loci")
            failed = [f"{s['translation_id']}:{s['qc']}" for s in (a, b) if s["qc"] != "pass"]
            failed += [f"{s['translation_id']}:assembly {s['assembly_qc']} ({s['assembly_flags']})"
                       for s in (a, b) if s["assembly_qc"] in ("fail", "warn")]
            if a["platform"] and b["platform"] and a["platform"] != b["platform"]:
                notes.add(f"mixed platforms ({a['platform']}/{b['platform']}); "
                          "sequencing errors can add allele differences")
            if a["st"] not in ("", "-") and b["st"] not in ("", "-") and a["st"] != b["st"]:
                notes.add(f"different MLST ST ({a['st']} vs {b['st']})")
            statuses = {s["assembly_qc"] for s in (a, b)}
            if any(s["qc"] != "pass" for s in (a, b)) or "fail" in statuses:
                row["qc"] = "fail"
            elif "warn" in statuses:
                row["qc"] = "warn"
            elif statuses == {"pass"}:
                row["qc"] = "pass"
            else:
                row["qc"] = "not_checked"

            if a["schema"] != b["schema"]:
                row["verdict"] = "different_schema"
            elif a["profile"] is None or b["profile"] is None:
                row["verdict"] = "missing_profile"
            else:
                info = schemas[a["schema"]]
                threshold = int(info["threshold"])
                borderline = int(info["borderline"]) if info["borderline"] else None
                shared, diffs = compare(a["profile"], b["profile"])
                row["shared_loci"] = shared
                row["allele_diffs"] = diffs
                row["threshold"] = threshold if borderline is None else f"{threshold}-{borderline}"
                row["verdict"] = verdict(diffs, threshold, borderline)
            if failed:
                notes.add("QC: " + ", ".join(failed))
            row["notes"] = "; ".join(sorted(notes))
            pair_rows.append(row)

    summary_rows = []
    for group, ids in groups.items():
        rows = [r for r in pair_rows if r["transmission"] == group]
        verdicts = [r["verdict"] for r in rows]
        diffs = [r["allele_diffs"] for r in rows if r["allele_diffs"] != ""]
        if not rows:
            overall = "single_isolate"
        elif any(v in ("missing_profile", "different_schema") for v in verdicts):
            overall = "incomplete"
        elif all(v == "within_threshold" for v in verdicts):
            overall = "all_pairs_within"
        elif any(v in ("within_threshold", "borderline") for v in verdicts):
            overall = "some_pairs_within"
        else:
            overall = "no_pairs_within"
        summary_rows.append({
            "transmission": group,
            "schema": ",".join(sorted({sample_info[i]["schema"] for i in ids})),
            "isolates": len(ids),
            "pairs": len(rows),
            "min_diffs": min(diffs) if diffs else "",
            "max_diffs": max(diffs) if diffs else "",
            "pairs_within": verdicts.count("within_threshold"),
            "pairs_borderline": verdicts.count("borderline"),
            "overall": overall,
            "qc": next((q for q in ("fail", "warn", "not_checked", "pass")
                        if q in {r["qc"] for r in rows}), ""),
        })

    qc_fields = list(qc_rows[0])
    pair_fields = list(pair_rows[0]) if pair_rows else []
    summary_fields = list(summary_rows[0])
    out_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(out_dir / "allele_qc.tsv", qc_rows, qc_fields)
    write_tsv(out_dir / "pairwise_distances.tsv", pair_rows, pair_fields)
    write_tsv(out_dir / "group_summary.tsv", summary_rows, summary_fields)

    if pair_rows:
        print_table(pair_rows, ["transmission", "sample_a", "sample_b", "days_apart", "schema",
                                "shared_loci", "allele_diffs", "threshold", "verdict", "qc"])
        print()
    print_table(summary_rows, summary_fields)
    print(f"\nWritten to {out_dir}: allele_qc.tsv, pairwise_distances.tsv, group_summary.tsv")

    low = [r["translation_id"] for r in qc_rows if r["qc"] != "pass"]
    if low:
        print(f"Isolates failing QC or missing profiles: {', '.join(low)}", file=sys.stderr)


if __name__ == "__main__":
    main()

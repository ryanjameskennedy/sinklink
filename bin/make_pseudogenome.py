#!/usr/bin/env python3
"""Build a masked pseudogenome for one isolate from its reference-based variant calls.

Applies the PASS substitutions (SNPs and same-length MNPs) of a haploid VCF from
Snippy or Clair3 to the reference genome, then masks positions with read depth
below --min-depth as N and positions without reads as -. Every isolate mapped to
the same reference gets a sequence of the same length, so pairwise SNP distances
can be counted position by position. Writes <prefix>.pseudogenome.fa and a
one-row <prefix>.pseudogenome.tsv.
"""

import argparse
import csv
import gzip
import re

CALLED_GENOTYPES = {"1", "1/1", "1|1"}
BASES = re.compile(r"^[ACGT]+$")


def open_text(path):
    with open(path, "rb") as handle:
        gzipped = handle.read(2) == b"\x1f\x8b"
    return gzip.open(path, "rt") if gzipped else open(path)


def read_fasta(path):
    contigs, name, chunks = [], None, []
    with open_text(path) as handle:
        for line in handle:
            line = line.strip()
            if line.startswith(">"):
                if name is not None:
                    contigs.append((name, "".join(chunks).upper()))
                name, chunks = line[1:].split()[0], []
            elif line:
                chunks.append(line)
    if name is not None:
        contigs.append((name, "".join(chunks).upper()))
    return contigs


def read_depth(path, contig_lengths):
    depth = {name: bytearray(length) for name, length in contig_lengths.items()}
    with open_text(path) as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 3 or fields[0] not in depth:
                continue
            position = int(fields[1]) - 1
            if 0 <= position < len(depth[fields[0]]):
                depth[fields[0]][position] = min(int(fields[2]), 255)
    return depth


def read_substitutions(path):
    substitutions = []
    with open_text(path) as handle:
        for line in handle:
            if line.startswith("#") or not line.strip():
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 10:
                continue
            chrom, pos, _id, ref, alt, _qual, filt, _info, fmt, sample = fields[:10]
            if filt not in ("PASS", "."):
                continue
            if "," in alt or len(ref) != len(alt) or not BASES.match(alt.upper()):
                continue
            keys = fmt.split(":")
            values = sample.split(":")
            genotype = values[keys.index("GT")] if "GT" in keys and keys.index("GT") < len(values) else ""
            if genotype not in CALLED_GENOTYPES:
                continue
            substitutions.append((chrom, int(pos) - 1, ref.upper(), alt.upper()))
    return substitutions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", required=True)
    parser.add_argument("--reference", required=True, help="reference genome FASTA")
    parser.add_argument("--vcf", required=True, help="haploid VCF, plain or gzipped")
    parser.add_argument("--depth", required=True, help="samtools depth output for the same BAM")
    parser.add_argument("--min-depth", type=int, default=10)
    parser.add_argument("--prefix", required=True)
    args = parser.parse_args()

    contigs = read_fasta(args.reference)
    lengths = {name: len(seq) for name, seq in contigs}
    sequences = {name: bytearray(seq, "ascii") for name, seq in contigs}
    depth = read_depth(args.depth, lengths)

    applied = 0
    for chrom, start, ref, alt in read_substitutions(args.vcf):
        if chrom not in sequences or start + len(ref) > lengths[chrom]:
            continue
        sequences[chrom][start:start + len(alt)] = alt.encode("ascii")
        applied += sum(1 for r, a in zip(ref, alt) if r != a)

    masked = 0
    for name, seq in sequences.items():
        contig_depth = depth[name]
        for i, value in enumerate(contig_depth):
            if value == 0:
                seq[i] = ord("-")
                masked += 1
            elif value < args.min_depth:
                seq[i] = ord("N")
                masked += 1

    genome = b"".join(sequences[name] for name, _seq in contigs).decode("ascii")
    with open(f"{args.prefix}.pseudogenome.fa", "w") as handle:
        handle.write(f">{args.sample}\n")
        for i in range(0, len(genome), 60):
            handle.write(genome[i:i + 60] + "\n")

    total = len(genome)
    with open(f"{args.prefix}.pseudogenome.tsv", "w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["sample", "reference_length", "snps", "masked_positions", "fraction_called"])
        writer.writerow([args.sample, total, applied, masked,
                         f"{(total - masked) / total:.4f}" if total else ""])


if __name__ == "__main__":
    main()

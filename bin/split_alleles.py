#!/usr/bin/env python3
"""Split a single multi-locus allele FASTA into one FASTA per locus.

chewBBACA PrepExternalSchema expects a folder with one FASTA file per locus,
while some schemes (e.g. the Groschel et al. 2020 S. maltophilia wgMLST) are
published as one file holding every allele of every locus.
"""

import argparse
import gzip
import re
import sys
from collections import OrderedDict
from pathlib import Path


def open_text(path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path)


def read_fasta(path):
    header, seq = None, []
    with open_text(path) as handle:
        for line in handle:
            line = line.rstrip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    yield header, "".join(seq)
                header, seq = line[1:].split()[0], []
            else:
                seq.append(line)
    if header is not None:
        yield header, "".join(seq)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fasta", help="multi-locus allele FASTA (optionally gzipped)")
    parser.add_argument("outdir", help="folder to write <locus>.fasta files into")
    parser.add_argument(
        "--pattern",
        default=r"^(?P<locus>.+)[_:|](?P<allele>\d+)$",
        help="regex with named groups 'locus' and 'allele', matched against the header ID",
    )
    parser.add_argument(
        "--expect-loci",
        type=int,
        help="fail if the number of loci found differs from this by more than 5%%",
    )
    args = parser.parse_args()

    pattern = re.compile(args.pattern)
    loci = OrderedDict()
    for header, seq in read_fasta(args.fasta):
        match = pattern.match(header)
        if not match:
            sys.exit(f"Header '{header}' does not match --pattern '{args.pattern}'")
        loci.setdefault(match.group("locus"), []).append((match.group("allele"), seq))

    n_alleles = sum(len(v) for v in loci.values())
    example = next(iter(loci), None)
    print(f"Found {len(loci)} loci and {n_alleles} alleles (e.g. locus '{example}')")

    if args.expect_loci and abs(len(loci) - args.expect_loci) > 0.05 * args.expect_loci:
        sys.exit(
            f"Expected about {args.expect_loci} loci but found {len(loci)}. "
            "The header format probably differs; set --pattern to match it."
        )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for locus, alleles in loci.items():
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", locus)
        with open(outdir / f"{safe}.fasta", "w") as out:
            for allele, seq in alleles:
                out.write(f">{safe}_{allele}\n{seq}\n")


if __name__ == "__main__":
    main()
